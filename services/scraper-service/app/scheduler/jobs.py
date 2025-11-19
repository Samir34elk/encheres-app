"""
Scheduler for automated scraping jobs.
REPLACES: GitHub Actions workflows (.github/workflows/scheduled-jobs.yml)

This internal scheduler runs the same jobs that were previously executed by GitHub Actions:
1. Scrape sales every 15 minutes (replaces prepare-sales + scrape-sales jobs)
2. Discover sales daily at 3am (replaces discover-sales job)
3. Update favorite prices every minute (replaces update-favorite-prices job)
"""

import logging
import sys
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Add scripts directory (legacy GitHub Actions) to sys.path
SCRIPTS_PATH = os.getenv("SCRIPTS_PATH", "/app/scripts")
if os.path.isdir(SCRIPTS_PATH):
    sys.path.insert(0, SCRIPTS_PATH)

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.batch_scraper import BatchAuctionScraper
from app.services.sale_discovery import SaleDiscoveryService

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Internal scheduler service that replaces GitHub Actions.

    GitHub Actions workflows replaced:
    - scheduled-jobs.yml::prepare-sales (every 15 min)
    - scheduled-jobs.yml::scrape-sales (every 15 min)
    - scheduled-jobs.yml::discover-sales (daily at 3am)
    - scheduled-jobs.yml::update-favorite-prices (every minute)
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def scrape_sales_job(self):
        """
        Scraping périodique des ventes nécessitant une mise à jour.

        REPLACES: GitHub Actions jobs 'prepare-sales' + 'scrape-sales'
        - Was: Python script triggered by GitHub Actions cron
        - Now: Internal APScheduler job
        """
        logger.info("[SCRAPER] Exécution du job : scraping des ventes sélectionnées")
        logger.info("[SCRAPER] (Replaces: GitHub Actions prepare-sales + scrape-sales)")

        async with AsyncSessionLocal() as db:
            try:
                batch = BatchAuctionScraper(db)
                summary = await batch.run()
                logger.info(f"[SCRAPER] Scraping batch terminé : {summary}")
            except Exception as exc:
                logger.exception(f"[SCRAPER] Erreur pendant le scraping automatique : {exc}")

    async def discover_sales_job(self):
        """
        Découverte quotidienne des ventes disponibles.

        REPLACES: GitHub Actions job 'discover-sales'
        - Was: Triggered by GitHub Actions cron (0 3 * * *)
        - Now: Internal APScheduler job (daily at 3am)
        """
        logger.info("[DISCOVERY] Exécution du job : découverte des ventes")
        logger.info("[DISCOVERY] (Replaces: GitHub Actions discover-sales)")

        async with AsyncSessionLocal() as db:
            try:
                service = SaleDiscoveryService()
                sales = await service.fetch_sales()
                created, updated = await service.sync_with_database(db, sales)
                logger.info(
                    f"[DISCOVERY] Découverte des ventes terminée : {len(sales)} ventes, "
                    f"{created} créées, {updated} mises à jour"
                )
            except Exception as exc:
                logger.exception(f"[DISCOVERY] Erreur pendant la découverte automatique des ventes : {exc}")

    async def update_favorite_prices_job(self):
        """
        Mise à jour des prix des lots favoris.

        REPLACES: GitHub Actions job 'update-favorite-prices'
        - Was: Python script update_favorite_prices.py triggered every minute
        - Now: Internal APScheduler job (every minute)
        """
        logger.info("[PRICES] Exécution du job : mise à jour des prix favoris")
        logger.info("[PRICES] (Replaces: GitHub Actions update-favorite-prices)")

        try:
            # Import the script logic
            from update_favorite_prices import main as update_prices_main
            await update_prices_main()
        except Exception as exc:
            logger.exception(f"[PRICES] Erreur pendant la mise à jour des prix : {exc}")

    def start(self):
        """Démarre le scheduler et enregistre les tâches."""
        if not settings.ENABLE_SCHEDULER:
            logger.info("⚠️ Internal scheduler disabled via configuration.")
            return

        logger.info("="*60)
        logger.info("🚀 Starting Internal Scheduler")
        logger.info("   REPLACES: GitHub Actions (.github/workflows/scheduled-jobs.yml)")
        logger.info("="*60)

        # Job 1: Scrape sales every 15 minutes
        # REPLACES: GitHub Actions cron '*/15 * * * *' (prepare-sales + scrape-sales)
        self.scheduler.add_job(
            self.scrape_sales_job,
            trigger=IntervalTrigger(minutes=settings.SCRAPER_INTERVAL_MINUTES),
            id="scrape_sales",
            name="[SCRAPER] Scrape sales (Replaces GHA prepare-sales + scrape-sales)",
            replace_existing=True,
        )
        logger.info(f"✓ Job 1: Scrape sales every {settings.SCRAPER_INTERVAL_MINUTES} minutes")
        logger.info(f"         (Replaces: GitHub Actions cron '*/15 * * * *')")

        # Job 2: Discover sales daily at 3am
        # REPLACES: GitHub Actions cron '0 3 * * *' (discover-sales)
        self.scheduler.add_job(
            self.discover_sales_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="discover_sales",
            name="[DISCOVERY] Discover sales daily (Replaces GHA discover-sales)",
            replace_existing=True,
        )
        logger.info(f"✓ Job 2: Discover sales daily at 3:00 AM")
        logger.info(f"         (Replaces: GitHub Actions cron '0 3 * * *')")

        # Job 3: Update favorite prices every minute
        # REPLACES: GitHub Actions cron '* * * * *' (update-favorite-prices)
        if settings.ENABLE_PRICE_UPDATES:
            self.scheduler.add_job(
                self.update_favorite_prices_job,
                trigger=IntervalTrigger(minutes=1),
                id="update_favorite_prices",
                name="[PRICES] Update favorite prices (Replaces GHA update-favorite-prices)",
                replace_existing=True,
            )
            logger.info(f"✓ Job 3: Update favorite prices every minute")
            logger.info(f"         (Replaces: GitHub Actions cron '* * * * *')")
        else:
            logger.info(f"⊘ Job 3: Update favorite prices DISABLED")

        self.scheduler.start()
        logger.info("="*60)
        logger.info("✅ Scheduler started successfully!")
        logger.info("   GitHub Actions workflows are now REPLACED by internal scheduler")
        logger.info("="*60)

    def shutdown(self):
        """Arrête proprement le scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler arrêté")

    def get_jobs(self):
        """Get all scheduled jobs"""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str):
        """Pause a specific job"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.pause()
            logger.info(f"Job {job_id} paused")

    def resume_job(self, job_id: str):
        """Resume a paused job"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.resume()
            logger.info(f"Job {job_id} resumed")

    def trigger_job(self, job_id: str):
        """Manually trigger a job"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=None)
            logger.info(f"Job {job_id} triggered manually")
