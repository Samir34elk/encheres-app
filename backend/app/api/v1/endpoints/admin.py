from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.lot import Lot
from app.models.favorite import Favorite
from app.models.sale import Sale
from app.models.alert import Alert
from app.services.scraper import AuctionScraper
from app.services.sale_discovery import SaleDiscoveryService
from app.services.batch_scraper import BatchAuctionScraper

router = APIRouter()


class ScrapeRequest(BaseModel):
    sale_number: Optional[int] = None


class ScrapeMultipleRequest(BaseModel):
    sale_numbers: List[int]


@router.get("/stats", response_model=Dict[str, Any])
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get global statistics for admin dashboard"""
    # Total users
    users_result = await db.execute(select(func.count()).select_from(User))
    total_users = users_result.scalar()

    # Active users (logged in last 30 days)
    # For simplicity, just count all active users
    active_users_result = await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)
    )
    active_users = active_users_result.scalar()

    # Total lots
    lots_result = await db.execute(select(func.count()).select_from(Lot))
    total_lots = lots_result.scalar()

    # Active lots
    active_lots_result = await db.execute(
        select(func.count()).select_from(Lot).where(Lot.is_active == 1)
    )
    active_lots = active_lots_result.scalar()

    # Total favorites
    favorites_result = await db.execute(select(func.count()).select_from(Favorite))
    total_favorites = favorites_result.scalar()

    # Other aggregates
    sales_result = await db.execute(select(func.count()).select_from(Sale))
    total_sales = sales_result.scalar()

    alerts_result = await db.execute(select(func.count()).select_from(Alert))
    total_alerts = alerts_result.scalar()

    last_scrape_result = await db.execute(
        select(func.max(Sale.last_scraped_at))
    )
    last_scrape = last_scrape_result.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_lots": total_lots,
        "active_lots": active_lots,
        "total_favorites": total_favorites,
        "total_sales": total_sales,
        "total_alerts": total_alerts,
        "last_scrape": last_scrape.isoformat() if last_scrape else None,
        "scraper_status": "idle"
    }


@router.post("/scrape")
async def trigger_scrape(
    payload: ScrapeRequest = ScrapeRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Manually trigger auction scraping for a specific sale or default sale"""
    scraper = AuctionScraper(db, sale_number=payload.sale_number)
    stats = await scraper.run()

    return {
        "message": f"Scraping completed for sale #{scraper.sale_number}",
        "sale_number": scraper.sale_number,
        "stats": stats
    }


@router.post("/scrape-multiple")
async def trigger_multiple_scrapes(
    payload: ScrapeMultipleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Trigger scraping for multiple sales"""
    results = []

    for sale_number in payload.sale_numbers:
        try:
            scraper = AuctionScraper(db, sale_number=sale_number)
            stats = await scraper.run()
            results.append({
                "sale_number": sale_number,
                "success": True,
                "stats": stats
            })
        except Exception as e:
            results.append({
                "sale_number": sale_number,
                "success": False,
                "error": str(e)
            })

    return {
        "message": f"Scraping completed for {len(payload.sale_numbers)} sales",
        "results": results
    }


@router.get("/scraper-logs")
async def get_scraper_logs(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Return basic scraper logs derived from sale metadata"""
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")

    total_result = await db.execute(select(func.count()).select_from(Sale))
    total = total_result.scalar()

    query = (
        select(Sale)
        .order_by(desc(Sale.last_scraped_at), desc(Sale.created_at))
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    sales = result.scalars().all()

    items = []
    for sale in sales:
        items.append({
            "id": sale.id,
            "sale_number": sale.sale_number,
            "lots_scraped": sale.total_lots,
            "status": "completed" if sale.is_scraped else "pending",
            "error": None,
            "started_at": sale.last_scraped_at,
            "completed_at": sale.last_scraped_at,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/discover-sales")
async def discover_sales(
    max_pages: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Récupère les ventes disponibles et les synchronise avec la base."""
    service = SaleDiscoveryService()
    sales = await service.fetch_sales(max_pages=max_pages)
    created, updated = await service.sync_with_database(db, sales)

    return {
        "items": [sale.to_dict() for sale in sales],
        "created": created,
        "updated": updated,
        "total": len(sales),
    }


@router.post("/scrape-all")
async def scrape_all_sales(
    limit: Optional[int] = None,
    staleness_hours: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Scrape toutes les ventes qui nécessitent une mise à jour."""
    batch = BatchAuctionScraper(
        db,
        staleness_hours=staleness_hours or settings.SALE_REFRESH_HOURS,
        limit=limit,
    )
    summary = await batch.run()
    return summary
