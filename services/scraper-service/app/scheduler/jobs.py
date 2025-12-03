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
from app.services.graphql_scraper import GraphQLAuctionScraper
from app.services.graphql_lot_scraper import GraphQLLotScraper
from sqlalchemy import select

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
        Scraping périodique des ventes et lots via GraphQL.

        REPLACES: GitHub Actions jobs 'prepare-sales' + 'scrape-sales'
        - Was: Playwright HTML scraping (slow, fragile)
        - Now: GraphQL API scraping (30x faster, stable)
        """
        logger.info("[SCRAPER] Exécution du job : scraping GraphQL des ventes et lots")
        logger.info("[SCRAPER] (Replaces: GitHub Actions prepare-sales + scrape-sales)")

        async with AsyncSessionLocal() as db:
            try:
                # Étape 1: Scraper toutes les ventes actives
                auction_scraper = GraphQLAuctionScraper(db)
                stats_ventes = await auction_scraper.sync_auctions(
                    filter_status="incoming",  # Ventes à venir
                    max_pages=None  # Toutes les pages
                )
                logger.info(f"[SCRAPER] Ventes synchronisées : {stats_ventes}")

                # Étape 2: Scraper les lots pour les ventes actives
                lot_scraper = GraphQLLotScraper(db)

                # Récupérer les ventes actives depuis la BDD
                from shared.models.sale import Sale
                result = await db.execute(
                    select(Sale)
                    .where(Sale.status == "active")
                    .order_by(Sale.start_date.desc())
                    .limit(50)  # Limiter aux 50 ventes les plus récentes
                )
                sales = result.scalars().all()

                total_lots = 0
                for sale in sales:
                    try:
                        stats_lots = await lot_scraper.sync_auction_lots(
                            auction_id=str(sale.sale_number),
                            sale_id=sale.id,
                            fetch_full_details=False  # Rapide: juste les infos de base
                        )
                        total_lots += stats_lots.get('total_processed', 0)
                        logger.info(f"[SCRAPER] Vente #{sale.sale_number}: {stats_lots}")
                    except Exception as e:
                        logger.error(f"[SCRAPER] Erreur vente #{sale.sale_number}: {e}")

                # Fermer les sessions aiohttp
                await auction_scraper.close()
                await lot_scraper.close()

                logger.info(
                    f"[SCRAPER] Scraping terminé : {len(sales)} ventes, "
                    f"{total_lots} lots synchronisés"
                )

            except Exception as exc:
                logger.exception(f"[SCRAPER] Erreur pendant le scraping automatique : {exc}")

    async def discover_sales_job(self):
        """
        Découverte quotidienne des ventes disponibles via GraphQL.

        REPLACES: GitHub Actions job 'discover-sales'
        - Was: HTML scraping for sale discovery
        - Now: GraphQL API (all statuses: incoming, ongoing, closed)
        """
        logger.info("[DISCOVERY] Exécution du job : découverte GraphQL des ventes")
        logger.info("[DISCOVERY] (Replaces: GitHub Actions discover-sales)")

        async with AsyncSessionLocal() as db:
            try:
                scraper = GraphQLAuctionScraper(db)

                # Synchroniser TOUTES les ventes (incoming, ongoing, closed)
                stats = await scraper.sync_auctions(
                    filter_status=None,  # Toutes les ventes
                    max_pages=None  # Toutes les pages
                )

                await scraper.close()

                logger.info(
                    f"[DISCOVERY] Découverte terminée : {stats}"
                )
            except Exception as exc:
                logger.exception(f"[DISCOVERY] Erreur pendant la découverte automatique des ventes : {exc}")

    async def update_favorite_prices_job(self):
        """
        Mise à jour des prix des lots favoris.

        REPLACES: GitHub Actions job 'update-favorite-prices'
        - Was: Python script update_favorite_prices.py triggered every minute
        - Now: Internal APScheduler job (every minute)

        NOTE: Legacy script not implemented yet. This job is disabled until
        the favorite prices update logic is migrated to GraphQL.
        """
        logger.info("[PRICES] Exécution du job : mise à jour des prix favoris")
        logger.info("[PRICES] (Replaces: GitHub Actions update-favorite-prices)")

        try:
            # Try to import the legacy script if it exists
            try:
                from update_favorite_prices import main as update_prices_main
                await update_prices_main()
            except ModuleNotFoundError:
                logger.warning(
                    "[PRICES] Module 'update_favorite_prices' not found. "
                    "This legacy feature needs to be migrated to GraphQL. "
                    "Set ENABLE_PRICE_UPDATES=False to disable this job."
                )
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
