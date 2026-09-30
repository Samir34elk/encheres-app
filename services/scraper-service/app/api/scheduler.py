"""
Endpoints de pilotage du scraper (déclenchement manuel, état, diagnostic).
Tout passe par le client HTTP throttlé : aucun endpoint ne contourne la protection anti-blocage.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.services.graphql_lot_scraper import GraphQLLotScraper
from app.scheduler.jobs import SchedulerService
from app.services.polite_client import ScraperPausedError, polite_client

router = APIRouter()
logger = logging.getLogger(__name__)

SCRAPER_DISABLED_MESSAGE = "Internal scraping is disabled. Use the ingestion workflow instead."


def get_scheduler() -> SchedulerService:
    """Expose the running scheduler instance (configured in app.main)."""
    try:
        from app.main import scheduler
        return scheduler
    except Exception as exc:  # pragma: no cover
        logger.error("Scheduler not available: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scheduler not available"
        )


def _ensure_enabled():
    if not settings.ENABLE_INTERNAL_SCRAPER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SCRAPER_DISABLED_MESSAGE,
        )


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
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """
    Déclenche un passage de scraping (même logique que le job planifié :
    seules les ventes à rafraîchir sont scrapées, requêtes throttlées).
    """
    _ensure_enabled()
    return await scheduler.scrape_sales_job()


@router.post("/trigger-discovery")
async def trigger_discovery(
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Déclenche la découverte complète de la liste des ventes."""
    _ensure_enabled()
    return await scheduler.discover_sales_job()


@router.post("/force-scrape-sale/{sale_number}")
async def force_scrape_sale(
    sale_number: int,
    full_details: bool = False,
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """
    Force le scraping des lots d'une vente.

    full_details=true récupère aussi les caractéristiques de CHAQUE lot
    (1 requête par lot) : à réserver aux petites ventes.
    """
    _ensure_enabled()
    if scheduler.is_running:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un scraping est déjà en cours")

    from datetime import datetime
    from app.models.sale import Sale

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Sale).where(Sale.sale_number == sale_number))
        sale = result.scalar_one_or_none()
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sale {sale_number} not found in database"
            )

        try:
            stats = await GraphQLLotScraper(db).sync_auction_lots(
                auction_id=str(sale_number),
                sale_id=sale.id,
                fetch_full_details=full_details
            )
        except ScraperPausedError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

        sale.is_scraped = True
        sale.last_scraped_at = datetime.utcnow()
        await db.commit()

    return {"status": "success", "sale_number": sale_number, "stats": stats}


@router.post("/force-scrape-all")
async def force_scrape_all(
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """
    Force le scraping de toutes les ventes non finalisées (en cours, à venir,
    clôturées dont le prix final n'a pas encore été capturé), sans attendre leur
    intervalle. Les ventes clôturées déjà finalisées ne sont jamais re-scrapées.
    Toujours throttlé : peut prendre du temps.
    """
    _ensure_enabled()
    return await scheduler.scrape_sales_job(force_all_open=True)


@router.post("/resume")
async def resume_after_block(_: None = Depends(verify_cron_secret)):
    """Lève manuellement la pause du disjoncteur (à utiliser avec prudence)."""
    polite_client.blocked_until = None
    return {"status": "resumed", "client": polite_client.status()}


@router.get("/jobs-status")
async def get_jobs_status(
    _: None = Depends(verify_cron_secret),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """État du scheduler, du client HTTP (pause, budget) et des derniers passages."""
    jobs = [{
        "id": job.id,
        "name": job.name,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "trigger": str(job.trigger)
    } for job in scheduler.get_jobs()]

    return {
        "scheduler": "internal",
        "running": scheduler.is_running,
        "jobs": jobs,
        "client": polite_client.status(),
        "last_run": scheduler.last_run,
    }


@router.get("/diagnostic")
async def diagnostic(
    db: AsyncSession = Depends(get_db)
):
    """Diagnostic : configuration anti-blocage, état du client et de la BDD."""
    from sqlalchemy import func
    from app.models.sale import Sale

    info = {
        "configuration": {
            "scraper_interval_minutes": settings.SCRAPER_INTERVAL_MINUTES,
            "sales_list_refresh_minutes": settings.SALES_LIST_REFRESH_MINUTES,
            "max_sales_per_run": settings.MAX_SALES_PER_RUN,
            "request_min_delay_seconds": settings.REQUEST_MIN_DELAY_SECONDS,
            "max_requests_per_day": settings.MAX_REQUESTS_PER_DAY,
        },
        "client": polite_client.status(),
        "database": {},
    }
    try:
        result = await db.execute(select(Sale.status, func.count(Sale.id)).group_by(Sale.status))
        info["database"]["sales_by_status"] = {status_: count for status_, count in result.all()}
        info["database"]["status"] = "connected"
    except Exception as e:
        info["database"]["status"] = "error"
        info["database"]["error"] = str(e)
    return info
