from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc, asc
from typing import Optional, List, Annotated
from pydantic import Field
import math

from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.lot import Lot
from app.models.favorite import Favorite
from app.models.price_history import PriceHistory
from app.schemas.lot import LotResponse, LotListResponse, LotWithFavorite, PriceHistoryResponse

router = APIRouter()


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
    query = select(Lot)

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

    # Transform SQLAlchemy objects to Pydantic
    items = [LotResponse.model_validate(lot) for lot in lots]

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
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Increment view count
    lot.view_count += 1
    await db.commit()

    lot_data = LotWithFavorite.model_validate(lot)
    lot_data.is_favorited = False
    lot_data.user_tags = None
    lot_data.user_notes = None

    if current_user:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.lot_id == lot.id
            )
        )
        favorite = fav_result.scalar_one_or_none()
        if favorite:
            lot_data.is_favorited = True
            lot_data.user_tags = favorite.tags
            lot_data.user_notes = favorite.notes

    return lot_data


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
