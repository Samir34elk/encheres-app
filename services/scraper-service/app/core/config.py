"""Scraper Service configuration"""
import sys
import os
from typing import List

# Add shared library to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../shared"))

from shared.config import BaseServiceConfig
from pydantic import Field


class ScraperServiceConfig(BaseServiceConfig):
    """Configuration for Scraper Service - Replaces GitHub Actions"""

    SERVICE_NAME: str = Field(default="scraper-service")
    PORT: int = Field(default=8003)

    # Scheduler settings (replaces GitHub Actions cron)
    ENABLE_SCHEDULER: bool = Field(default=True)
    SCRAPER_INTERVAL_MINUTES: int = Field(default=15)
    ENABLE_PRICE_UPDATES: bool = Field(default=True)

    # Scraper settings
    AUCTION_BASE_URL: str = Field(default="https://encheres-domaine.gouv.fr")
    MAX_PAGES: int = Field(default=5)
    MAX_SALES: int = Field(default=20)
    MAX_SALES_FULL_DISCOVERY: int = Field(default=50)
    MAX_PAGES_FULL_DISCOVERY: int = Field(default=10)

    # Playwright settings
    HEADLESS_BROWSER: bool = Field(default=True)
    BROWSER_TIMEOUT: int = Field(default=30000)

    # Celery settings (for async workers)
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/1")


settings = ScraperServiceConfig()
