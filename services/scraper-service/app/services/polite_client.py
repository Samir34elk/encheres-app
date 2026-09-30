"""
Client HTTP "poli" partagé pour toutes les requêtes vers encheres-domaine.gouv.fr.

Objectif : ne plus se faire bloquer l'IP. Toutes les requêtes du scraper passent
par ce client unique qui garantit :

- une seule requête à la fois (sérialisation globale) ;
- un délai minimum + un jitter aléatoire entre deux requêtes ;
- des retries avec backoff exponentiel sur 429 / 5xx / timeouts (respecte Retry-After) ;
- un disjoncteur : dès qu'un 403/429 persiste, TOUT le scraping est mis en pause
  pendant un cooldown (qui double à chaque blocage successif) ;
- un budget quotidien de requêtes.
"""

import asyncio
import logging
import random
import time
from datetime import date
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperPausedError(Exception):
    """Levée quand le scraping est en pause (blocage détecté ou budget épuisé)."""


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://encheres-domaine.gouv.fr/",
    "Store": "default",
}

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class PoliteClient:
    def __init__(
        self,
        min_delay: float,
        jitter: float,
        max_retries: int,
        backoff_base: float,
        cooldown_seconds: float,
        max_cooldown_seconds: float,
        daily_budget: int,
        verify_ssl: bool = True,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        sleep=asyncio.sleep,
        clock=time.monotonic,
    ):
        self.min_delay = min_delay
        self.jitter = jitter
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.cooldown_seconds = cooldown_seconds
        self.max_cooldown_seconds = max_cooldown_seconds
        self.daily_budget = daily_budget
        self._verify_ssl = verify_ssl
        self._transport = transport
        self._sleep = sleep
        self._clock = clock

        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._last_request_at: Optional[float] = None

        self.blocked_until: Optional[float] = None
        self.consecutive_blocks = 0
        self.last_error: Optional[str] = None
        self._budget_day = date.today()
        self.requests_today = 0

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=BROWSER_HEADERS,
                verify=self._verify_ssl,
                transport=self._transport,
            )
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # --- État -------------------------------------------------------------

    def pause_remaining_seconds(self) -> float:
        if self.blocked_until is None:
            return 0.0
        return max(0.0, self.blocked_until - self._clock())

    def is_paused(self) -> bool:
        return self.pause_remaining_seconds() > 0 or self._budget_exhausted()

    def _budget_exhausted(self) -> bool:
        self._roll_budget_day()
        return self.requests_today >= self.daily_budget

    def _roll_budget_day(self):
        today = date.today()
        if today != self._budget_day:
            self._budget_day = today
            self.requests_today = 0

    def _trip_breaker(self, reason: str):
        self.consecutive_blocks += 1
        cooldown = min(
            self.cooldown_seconds * (2 ** (self.consecutive_blocks - 1)),
            self.max_cooldown_seconds,
        )
        self.blocked_until = self._clock() + cooldown
        self.last_error = reason
        logger.error(
            "[POLITE] Blocage détecté (%s). Scraping en pause pendant %d min.",
            reason, cooldown // 60,
        )

    def status(self) -> Dict[str, Any]:
        self._roll_budget_day()
        return {
            "paused": self.is_paused(),
            "pause_remaining_seconds": int(self.pause_remaining_seconds()),
            "consecutive_blocks": self.consecutive_blocks,
            "requests_today": self.requests_today,
            "daily_budget": self.daily_budget,
            "last_error": self.last_error,
            "min_delay_seconds": self.min_delay,
        }

    # --- Requêtes ---------------------------------------------------------

    async def _wait_turn(self):
        delay = self.min_delay + random.uniform(0, self.jitter)
        if self._last_request_at is not None:
            elapsed = self._clock() - self._last_request_at
            if elapsed < delay:
                await self._sleep(delay - elapsed)

    async def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET JSON en respectant throttling, retries et disjoncteur."""
        async with self._lock:
            for attempt in range(self.max_retries + 1):
                if self.pause_remaining_seconds() > 0:
                    raise ScraperPausedError(
                        f"Scraping en pause encore {int(self.pause_remaining_seconds())}s "
                        f"(dernière erreur : {self.last_error})"
                    )
                if self._budget_exhausted():
                    raise ScraperPausedError(
                        f"Budget quotidien atteint ({self.daily_budget} requêtes)"
                    )

                await self._wait_turn()
                self._last_request_at = self._clock()
                self.requests_today += 1

                retry_after: Optional[float] = None
                try:
                    response = await self._get_client().get(url, params=params)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    self.last_error = f"{type(exc).__name__}: {exc}"
                    logger.warning("[POLITE] Erreur réseau (tentative %d) : %s", attempt + 1, exc)
                else:
                    if response.status_code < 400:
                        try:
                            data = response.json()
                        except ValueError:
                            # Page HTML (ex. "This website requires JS enabled and cookies") :
                            # le site filtre les clients automatisés. On s'arrête, on ne
                            # tente pas de contourner la protection.
                            self._trip_breaker("protection anti-robot (réponse HTML au lieu de JSON)")
                            raise ScraperPausedError(
                                "Le site renvoie une page anti-robot au lieu des données"
                            )
                        self.consecutive_blocks = 0
                        self.last_error = None
                        return data

                    self.last_error = f"HTTP {response.status_code}"
                    if response.status_code == 403:
                        # 403 = blocage WAF/IP : insister ne fait qu'aggraver la situation.
                        self._trip_breaker("HTTP 403")
                        raise ScraperPausedError("HTTP 403 : IP probablement bloquée")
                    if response.status_code not in RETRYABLE_STATUS:
                        response.raise_for_status()
                    retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                    logger.warning(
                        "[POLITE] HTTP %d (tentative %d/%d)",
                        response.status_code, attempt + 1, self.max_retries + 1,
                    )

                if attempt < self.max_retries:
                    backoff = retry_after or self.backoff_base * (2 ** attempt)
                    await self._sleep(backoff + random.uniform(0, self.jitter))

            if self.last_error == "HTTP 429":
                self._trip_breaker("HTTP 429 persistant")
                raise ScraperPausedError("HTTP 429 persistant : trop de requêtes")
            raise httpx.HTTPError(f"Échec après {self.max_retries + 1} tentatives : {self.last_error}")


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


polite_client = PoliteClient(
    min_delay=settings.REQUEST_MIN_DELAY_SECONDS,
    jitter=settings.REQUEST_JITTER_SECONDS,
    max_retries=settings.REQUEST_MAX_RETRIES,
    backoff_base=settings.REQUEST_BACKOFF_SECONDS,
    cooldown_seconds=settings.BLOCK_COOLDOWN_MINUTES * 60,
    max_cooldown_seconds=settings.BLOCK_MAX_COOLDOWN_HOURS * 3600,
    daily_budget=settings.MAX_REQUESTS_PER_DAY,
    verify_ssl=settings.HTTP_VERIFY_SSL,
)
