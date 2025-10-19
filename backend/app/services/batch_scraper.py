import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, asc, nullsfirst

from app.core.config import settings
from app.models.sale import Sale
from app.services.scraper import AuctionScraper

logger = logging.getLogger(__name__)


class BatchAuctionScraper:
    """Service orchestrant le scraping de plusieurs ventes."""

    def __init__(
        self,
        db: AsyncSession,
        staleness_hours: int = settings.SALE_REFRESH_HOURS,
        limit: Optional[int] = None,
    ):
        self.db = db
        self.staleness_hours = staleness_hours
        self.limit = limit

    async def _get_sales_to_scrape(self) -> List[Sale]:
        """Sélectionne les ventes à traiter en fonction de leur fraicheur."""
        threshold = datetime.utcnow() - timedelta(hours=self.staleness_hours)

        query = (
            select(Sale)
            .where(
                or_(
                    Sale.is_scraped.is_(False),
                    Sale.last_scraped_at.is_(None),
                    Sale.last_scraped_at <= threshold,
                )
            )
            .order_by(
                nullsfirst(asc(Sale.last_scraped_at)),
                asc(Sale.sale_number),
            )
        )

        if self.limit:
            query = query.limit(self.limit)

        result = await self.db.execute(query)
        sales = result.scalars().all()
        logger.info("Sélection de %s vente(s) à scraper", len(sales))
        return sales

    async def run(self) -> Dict[str, Any]:
        """Exécute le scraping pour toutes les ventes sélectionnées."""
        sales = await self._get_sales_to_scrape()
        summary: Dict[str, Any] = {
            "total_sales": len(sales),
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for sale in sales:
            summary["processed"] += 1
            logger.info("Scraping de la vente #%s", sale.sale_number)
            try:
                scraper = AuctionScraper(self.db, sale_number=sale.sale_number)
                stats = await scraper.run()
                summary["success"] += 1
                summary.setdefault("details", []).append(
                    {
                        "sale_number": sale.sale_number,
                        "stats": stats,
                    }
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Erreur lors du scraping de la vente #%s: %s", sale.sale_number, exc)
                summary["failed"] += 1
                summary["errors"].append(
                    {
                        "sale_number": sale.sale_number,
                        "error": str(exc),
                    }
                )

        return summary
