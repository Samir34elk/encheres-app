"""Scraper Service configuration"""
import sys
import os
from typing import List

# Add shared library to path
# In Docker: /app/shared, in local dev: ../../../shared
shared_path = "/app/shared" if os.path.exists("/app/shared") else os.path.join(os.path.dirname(__file__), "../../../shared")
sys.path.insert(0, shared_path)

from shared.config import BaseServiceConfig
from pydantic import Field


class ScraperServiceConfig(BaseServiceConfig):
    """Configuration for Scraper Service - Replaces GitHub Actions"""

    SERVICE_NAME: str = Field(default="scraper-service")
    PORT: int = Field(default=8003)

    # Scheduler settings (replaces GitHub Actions cron)
    ENABLE_SCHEDULER: bool = Field(default=True)
    SCRAPER_INTERVAL_MINUTES: int = Field(default=15)
    ENABLE_INTERNAL_SCRAPER: bool = Field(default=True)

    # Anti-blocage : throttling des requêtes vers encheres-domaine.gouv.fr
    REQUEST_MIN_DELAY_SECONDS: float = Field(default=4.0)
    REQUEST_JITTER_SECONDS: float = Field(default=3.0)
    REQUEST_MAX_RETRIES: int = Field(default=3)
    REQUEST_BACKOFF_SECONDS: float = Field(default=30.0)
    BLOCK_COOLDOWN_MINUTES: int = Field(default=120)
    BLOCK_MAX_COOLDOWN_HOURS: int = Field(default=24)
    MAX_REQUESTS_PER_DAY: int = Field(default=1500)
    HTTP_VERIFY_SSL: bool = Field(default=True)

    # Anti-blocage : fréquence de rafraîchissement
    SALES_LIST_REFRESH_MINUTES: int = Field(default=60)
    MAX_SALES_PER_RUN: int = Field(default=15)
    LOTS_REFRESH_ENDING_SOON_MINUTES: int = Field(default=15)   # vente finit dans < 3h
    LOTS_REFRESH_ENDING_TODAY_MINUTES: int = Field(default=60)  # vente finit dans < 24h
    LOTS_REFRESH_ACTIVE_MINUTES: int = Field(default=360)       # vente en cours
    LOTS_REFRESH_UPCOMING_MINUTES: int = Field(default=720)     # vente à venir

    # Scraper settings
    AUCTION_BASE_URL: str = Field(default="https://encheres-domaine.gouv.fr")
    AUCTION_GRAPHQL_URL: str = Field(default="https://encheres-domaine.gouv.fr/gateway/magento/graphql/")
    MAX_PAGES: int = Field(default=5)
    MAX_SALES: int = Field(default=20)
    MAX_SALES_FULL_DISCOVERY: int = Field(default=50)
    MAX_PAGES_FULL_DISCOVERY: int = Field(default=10)
    SALE_REFRESH_HOURS: int = Field(default=24)
    CRON_SECRET: str = Field(default="dev-cron-secret")

    # Playwright settings
    HEADLESS_BROWSER: bool = Field(default=True)
    BROWSER_TIMEOUT: int = Field(default=30000)

    # Celery settings (for async workers)
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/1")


settings = ScraperServiceConfig()
