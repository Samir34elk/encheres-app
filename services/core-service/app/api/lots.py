from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Annotated
from pydantic import Field, BaseModel
from datetime import datetime
import math

from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.lot import Lot
from app.models.sale import Sale
from app.models.favorite import Favorite
from app.models.price_history import PriceHistory
from app.schemas.lot import LotResponse, LotListResponse, LotWithFavorite, PriceHistoryResponse

router = APIRouter()


class PriceUpdate(BaseModel):
    """Schema for price update from GitHub Actions"""
    price: int
    status: Optional[str] = None


async def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify the cron secret header for GitHub Actions"""
    cron_secret = getattr(settings, 'CRON_SECRET', None)
    if not cron_secret:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")
    if not x_cron_secret or x_cron_secret != cron_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing cron secret")


@router.get("", response_model=LotListResponse)
async def get_lots(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
    sale_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query(default="price"),
    order: str = Query(default="desc"),
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of auction lots with filters"""
    # Eager load sale relationship to get end_date
    query = select(Lot).options(selectinload(Lot.sale))

    # Filters
    if sale_id:
        query = query.where(Lot.sale_id == sale_id)

    if active_only:
        query = query.where(Lot.is_active == 1)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Lot.title.ilike(search_term),
                Lot.description.ilike(search_term)
            )
        )

    if min_price is not None:
        query = query.where(Lot.price >= min_price)

    if max_price is not None:
        query = query.where(Lot.price <= max_price)

    if location:
        query = query.where(Lot.depot_location.ilike(f"%{location}%"))

    if status:
        query = query.where(Lot.status.ilike(f"%{status}%"))

    # Sorting
    if sort_by == "end_date":
        # For sorting by end_date, we need to join Sale table
        query = query.join(Sale, Lot.sale_id == Sale.id, isouter=True)
        sort_column = Sale.end_date
    else:
        sort_column = {
            "price": Lot.price,
            "date": Lot.last_updated,
            "lot_number": Lot.lot_number,
            "popularity": Lot.favorite_count
        }[sort_by]

    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Total count
    count_query = select(func.count()).select_from(Lot)
    if active_only:
        count_query = count_query.where(Lot.is_active == 1)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # Execute query
    result = await db.execute(query)
    lots = result.scalars().all()

    # Transform SQLAlchemy objects to Pydantic with sale_end_date
    items = []
    for lot in lots:
        lot_dict = {
            "id": lot.id,
            "lot_number": lot.lot_number,
            "title": lot.title,
            "description": lot.description,
            "price": lot.price,
            "status": lot.status,
            "depot_location": lot.depot_location,
            "url": lot.url,
            "image_url": lot.image_url,
            "sale_id": lot.sale_id,
            "sale_end_date": lot.sale.end_date if lot.sale else None,
            "first_seen": lot.first_seen,
            "last_updated": lot.last_updated,
            "is_active": lot.is_active,
            "view_count": lot.view_count,
            "favorite_count": lot.favorite_count
        }
        items.append(LotResponse(**lot_dict))

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/{lot_id}", response_model=LotWithFavorite)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """Get a specific lot by ID"""
    result = await db.execute(
        select(Lot).options(selectinload(Lot.sale)).where(Lot.id == lot_id)
    )
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Increment view count
    lot.view_count += 1
    await db.commit()

    # Build lot data dict with sale_end_date
    lot_dict = {
        "id": lot.id,
        "lot_number": lot.lot_number,
        "title": lot.title,
        "description": lot.description,
        "price": lot.price,
        "status": lot.status,
        "depot_location": lot.depot_location,
        "url": lot.url,
        "image_url": lot.image_url,
        "sale_id": lot.sale_id,
        "sale_end_date": lot.sale.end_date if lot.sale else None,
        "first_seen": lot.first_seen,
        "last_updated": lot.last_updated,
        "is_active": lot.is_active,
        "view_count": lot.view_count,
        "favorite_count": lot.favorite_count,
        "is_favorited": False,
        "user_tags": None,
        "user_notes": None
    }

    if current_user:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.lot_id == lot.id
            )
        )
        favorite = fav_result.scalar_one_or_none()
        if favorite:
            lot_dict["is_favorited"] = True
            lot_dict["user_tags"] = favorite.tags
            lot_dict["user_notes"] = favorite.notes

    return LotWithFavorite(**lot_dict)


@router.get("/{lot_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_lot_price_history(
    lot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get price history for a lot"""
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    history_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.lot_id == lot_id)
        .order_by(desc(PriceHistory.recorded_at))
    )
    history = history_result.scalars().all()

    return [PriceHistoryResponse.model_validate(h) for h in history]


@router.patch("/{lot_id}/price")
async def update_lot_price(
    lot_id: int,
    price_update: PriceUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """
    Update a lot's price from GitHub Actions scraping.
    Records price history if changed.
    Requires CRON_SECRET header.
    """
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    old_price = lot.price
    new_price = price_update.price

    # Update price
    lot.price = new_price
    lot.last_updated = datetime.utcnow()

    # Update status if provided
    if price_update.status:
        lot.status = price_update.status

    # Record price history if price changed
    if old_price != new_price:
        price_history = PriceHistory(
            lot_id=lot_id,
            price=new_price,
            status=price_update.status or lot.status,
            recorded_at=datetime.utcnow()
        )
        db.add(price_history)

    await db.commit()

    return {
        "success": True,
        "lot_id": lot_id,
        "old_price": old_price,
        "new_price": new_price,
        "price_changed": old_price != new_price
    }
