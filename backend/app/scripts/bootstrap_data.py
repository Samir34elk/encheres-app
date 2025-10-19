import argparse
import asyncio
import json
import logging
from typing import Optional

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.sale_discovery import SaleDiscoveryService
from app.services.batch_scraper import BatchAuctionScraper


logger = logging.getLogger(__name__)


async def bootstrap(
    max_pages: Optional[int],
    limit: Optional[int],
    staleness_hours: Optional[int],
) -> dict:
    """Découvre les ventes et lance le scraping batch."""
    async with AsyncSessionLocal() as db:
        discovery = SaleDiscoveryService()
        sales = await discovery.fetch_sales(max_pages=max_pages)
        created, updated = await discovery.sync_with_database(db, sales)
        logger.info(
            "Découverte terminée : %s ventes (créées=%s, mises à jour=%s)",
            len(sales),
            created,
            updated,
        )

        batch = BatchAuctionScraper(
            db,
            staleness_hours=staleness_hours or settings.SALE_REFRESH_HOURS,
            limit=limit,
        )
        summary = await batch.run()

    return {
        "discovered": len(sales),
        "created": created,
        "updated": updated,
        "batch": summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Découvre les ventes et scrape les lots"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Nombre maximum de pages à explorer pour la liste des ventes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximum de ventes à scraper lors du batch",
    )
    parser.add_argument(
        "--staleness-hours",
        type=int,
        default=None,
        help="Âge maximal des ventes avant re-scraping (heures)",
    )
    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    args = parse_args()
    result = asyncio.run(
        bootstrap(
            max_pages=args.max_pages,
            limit=args.limit,
            staleness_hours=args.staleness_hours,
        )
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
