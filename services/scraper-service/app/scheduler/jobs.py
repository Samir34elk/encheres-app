"""
Scheduler des jobs de scraping.

Stratégie anti-blocage (voir aussi app/services/polite_client.py) :
1. Liste des ventes : rafraîchie au plus toutes les SALES_LIST_REFRESH_MINUTES,
   en mode incrémental (on s'arrête dès qu'on retombe sur des ventes clôturées connues).
2. Lots : seules les ventes qui en ont besoin sont re-scrapées (voir refresh_policy.py),
   les plus urgentes d'abord, au plus MAX_SALES_PER_RUN par passage.
3. Découverte complète (tout l'historique) : une fois par jour, la nuit.
4. Toutes les requêtes passent par un client unique, throttlé, avec disjoncteur.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.sale import Sale
from app.scheduler.refresh_policy import decide_lots_refresh
from app.services.graphql_scraper import GraphQLAuctionScraper
from app.services.graphql_lot_scraper import GraphQLLotScraper
from app.services.polite_client import ScraperPausedError, polite_client

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        # Un seul job de scraping à la fois (planifié ou déclenché via l'API).
        self._run_lock = asyncio.Lock()
        self._last_sales_list_refresh: Optional[datetime] = None
        self.last_run: Dict[str, Any] = {}

    @property
    def is_running(self) -> bool:
        return self._run_lock.locked()

    async def scrape_sales_job(self, force_all_open: bool = False) -> Dict[str, Any]:
        """
        Scraping périodique : rafraîchit la liste des ventes si nécessaire,
        puis les lots des ventes qui en ont besoin.

        force_all_open: ignore les intervalles et scrape toutes les ventes non finalisées
        (toujours sans re-scraper les ventes clôturées déjà finalisées).
        """
        if self._run_lock.locked():
            logger.info("[SCRAPER] Un scraping est déjà en cours, passage ignoré")
            return {"status": "skipped", "reason": "already_running"}

        async with self._run_lock:
            if polite_client.is_paused():
                logger.warning("[SCRAPER] Scraping en pause : %s", polite_client.status())
                return {"status": "paused", "client": polite_client.status()}

            summary: Dict[str, Any] = {
                "status": "success",
                "started_at": datetime.utcnow().isoformat(),
                "sales_list": None,
                "sales_scraped": [],
                "lots_total": 0,
            }
            try:
                async with AsyncSessionLocal() as db:
                    now = datetime.utcnow()
                    if force_all_open or self._sales_list_is_stale(now):
                        summary["sales_list"] = await GraphQLAuctionScraper(db).sync_auctions(
                            incremental=True
                        )
                        self._last_sales_list_refresh = now

                    for sale, reason in await self._select_due_sales(db, force_all_open):
                        stats = await GraphQLLotScraper(db).sync_auction_lots(
                            auction_id=str(sale.sale_number),
                            sale_id=sale.id,
                            fetch_full_details=False,
                        )
                        sale.is_scraped = True
                        sale.last_scraped_at = datetime.utcnow()
                        await db.commit()
                        summary["lots_total"] += stats.get("total", 0)
                        summary["sales_scraped"].append(
                            {"sale_number": sale.sale_number, "reason": reason, "lots": stats.get("total", 0)}
                        )
            except ScraperPausedError as exc:
                logger.error("[SCRAPER] Arrêt du passage : %s", exc)
                summary["status"] = "paused"
                summary["error"] = str(exc)
            except Exception as exc:
                logger.exception("[SCRAPER] Erreur pendant le scraping : %s", exc)
                summary["status"] = "error"
                summary["error"] = str(exc)

            summary["client"] = polite_client.status()
            self.last_run["scrape_sales"] = summary
            logger.info(
                "[SCRAPER] Terminé (%s) : %d ventes, %d lots, %d requêtes aujourd'hui",
                summary["status"], len(summary["sales_scraped"]), summary["lots_total"],
                polite_client.requests_today,
            )
            return summary

    def _sales_list_is_stale(self, now: datetime) -> bool:
        return self._last_sales_list_refresh is None or (
            now - self._last_sales_list_refresh
            >= timedelta(minutes=settings.SALES_LIST_REFRESH_MINUTES)
        )

    async def _select_due_sales(self, db, force_all_open: bool):
        now = datetime.utcnow()
        # Les ventes clôturées finalisées sont écartées par la politique ;
        # on ne charge que les colonnes utiles au tri.
        result = await db.execute(select(Sale))
        candidates = []
        for sale in result.scalars().all():
            decision = decide_lots_refresh(sale.status, sale.end_date, sale.last_scraped_at, now)
            if decision.due or (force_all_open and decision.priority < 99):
                candidates.append((decision.priority, sale.end_date or datetime.max, sale, decision.reason))

        candidates.sort(key=lambda c: (c[0], c[1]))
        limit = None if force_all_open else settings.MAX_SALES_PER_RUN
        selected = candidates[:limit]
        if len(candidates) > len(selected):
            logger.info(
                "[SCRAPER] %d ventes à rafraîchir, %d traitées ce passage (MAX_SALES_PER_RUN)",
                len(candidates), len(selected),
            )
        return [(sale, reason) for _, _, sale, reason in selected]

    async def discover_sales_job(self) -> Dict[str, Any]:
        """Découverte complète de la liste des ventes (tout l'historique), une fois par jour."""
        if self._run_lock.locked():
            return {"status": "skipped", "reason": "already_running"}

        async with self._run_lock:
            if polite_client.is_paused():
                return {"status": "paused", "client": polite_client.status()}
            try:
                async with AsyncSessionLocal() as db:
                    stats = await GraphQLAuctionScraper(db).sync_auctions()
                self._last_sales_list_refresh = datetime.utcnow()
                summary = {"status": "success", "stats": stats}
            except ScraperPausedError as exc:
                summary = {"status": "paused", "error": str(exc)}
            except Exception as exc:
                logger.exception("[DISCOVERY] Erreur : %s", exc)
                summary = {"status": "error", "error": str(exc)}

            summary["client"] = polite_client.status()
            self.last_run["discover_sales"] = summary
            logger.info("[DISCOVERY] %s", summary)
            return summary

    def start(self):
        if not settings.ENABLE_SCHEDULER:
            logger.info("Internal scheduler disabled via configuration.")
            return

        self.scheduler.add_job(
            self.scrape_sales_job,
            trigger=IntervalTrigger(minutes=settings.SCRAPER_INTERVAL_MINUTES, jitter=120),
            id="scrape_sales",
            name="Scraping des ventes/lots à rafraîchir",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self.scheduler.add_job(
            self.discover_sales_job,
            trigger=CronTrigger(hour=3, minute=17, jitter=900),
            id="discover_sales",
            name="Découverte complète des ventes (quotidienne)",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info(
            "Scheduler démarré : scraping toutes les %d min, découverte quotidienne à 3h",
            settings.SCRAPER_INTERVAL_MINUTES,
        )

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler arrêté")

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            job.pause()

    def resume_job(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            job.resume()
