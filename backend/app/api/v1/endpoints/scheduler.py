"""
Scheduler endpoints for triggering background jobs externally.
Used by GitHub Actions or external cron services.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.services.batch_scraper import BatchAuctionScraper
from app.services.sale_discovery import SaleDiscoveryService

router = APIRouter()
logger = logging.getLogger(__name__)


async def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify the cron secret header for security"""
    # Get the secret from settings (should be set via environment variable)
    cron_secret = getattr(settings, 'CRON_SECRET', None)

    if not cron_secret:
        logger.error("CRON_SECRET not configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scheduler not properly configured"
        )

    if not x_cron_secret or x_cron_secret != cron_secret:
        logger.warning(f"Invalid cron secret attempt: {x_cron_secret}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret"
        )


@router.post("/trigger-scraping")
async def trigger_scraping(
    _: None = Depends(verify_cron_secret)
):
    """
    Trigger the sales scraping job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the scraping job
    """
    logger.info("Scraping job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            batch = BatchAuctionScraper(db)
            summary = await batch.run()
            logger.info(f"Scraping completed successfully: {summary}")

            return {
                "status": "success",
                "job": "scraping",
                "summary": summary,
                "message": "Sales scraping completed successfully"
            }
        except Exception as e:
            logger.exception(f"Error during scraping job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping job failed: {str(e)}"
            )


@router.post("/trigger-discovery")
async def trigger_discovery(
    _: None = Depends(verify_cron_secret)
):
    """
    Trigger the sales discovery job manually.
    This endpoint is called by GitHub Actions or external cron services.

    Headers:
        X-Cron-Secret: The secret key to authenticate the request

    Returns:
        Status and summary of the discovery job
    """
    logger.info("Discovery job triggered via API endpoint")

    async with AsyncSessionLocal() as db:
        try:
            service = SaleDiscoveryService()
            sales = await service.fetch_sales()
            created, updated = await service.sync_with_database(db, sales)

            result = {
                "status": "success",
                "job": "discovery",
                "total_sales": len(sales),
                "created": created,
                "updated": updated,
                "message": f"Discovery completed: {created} new, {updated} updated"
            }

            logger.info(f"Discovery completed successfully: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error during discovery job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Discovery job failed: {str(e)}"
            )


@router.get("/jobs-status")
async def get_jobs_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of scheduled jobs.
    Returns information about last execution times.

    Note: This is a basic implementation. For production, consider storing
    job execution history in the database.
    """
    # TODO: Implement job execution history tracking in database
    # For now, return basic info

    return {
        "scheduler": "external (GitHub Actions)",
        "jobs": [
            {
                "name": "scrape_sales",
                "schedule": f"Every {settings.SCRAPER_INTERVAL_MINUTES} minutes",
                "endpoint": "/api/v1/scheduler/trigger-scraping"
            },
            {
                "name": "discover_sales",
                "schedule": "Daily at 03:00 UTC",
                "endpoint": "/api/v1/scheduler/trigger-discovery"
            }
        ],
        "note": "Job history tracking not yet implemented"
    }
