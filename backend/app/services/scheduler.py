import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.batch_scraper import BatchAuctionScraper
from app.services.sale_discovery import SaleDiscoveryService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service de planification des tâches asynchrones."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def scrape_sales_job(self):
        """Scraping périodique des ventes nécessitant une mise à jour."""
        logger.info("Exécution du job planifié : scraping des ventes sélectionnées")
        async with AsyncSessionLocal() as db:
            try:
                batch = BatchAuctionScraper(db)
                summary = await batch.run()
                logger.info("Scraping batch terminé : %s", summary)
            except Exception as exc:
                logger.exception("Erreur pendant le scraping automatique : %s", exc)

    async def discover_sales_job(self):
        """Découverte quotidienne des ventes disponibles."""
        logger.info("Exécution du job planifié : découverte des ventes")
        async with AsyncSessionLocal() as db:
            try:
                service = SaleDiscoveryService()
                sales = await service.fetch_sales()
                created, updated = await service.sync_with_database(db, sales)
                logger.info(
                    "Découverte des ventes terminée : %s ventes, %s créées, %s mises à jour",
                    len(sales),
                    created,
                    updated,
                )
            except Exception as exc:
                logger.exception("Erreur pendant la découverte automatique des ventes : %s", exc)

    def start(self):
        """Démarre le scheduler et enregistre les tâches."""
        # Scraping récurrent des ventes
        self.scheduler.add_job(
            self.scrape_sales_job,
            trigger=IntervalTrigger(minutes=settings.SCRAPER_INTERVAL_MINUTES),
            id="scrape_sales",
            name="Scraper les ventes nécessitant une mise à jour",
            replace_existing=True,
        )

        # Découverte quotidienne des ventes (tous les jours à 03h00)
        self.scheduler.add_job(
            self.discover_sales_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="discover_sales",
            name="Découvrir les ventes disponibles",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler démarré avec %s minute(s) d'intervalle pour le scraping", settings.SCRAPER_INTERVAL_MINUTES)

    def shutdown(self):
        """Arrête proprement le scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler arrêté")
