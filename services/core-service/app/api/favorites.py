from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.favorite import Favorite
from app.models.lot import Lot
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteUpdate,
    FavoriteResponse,
    FavoriteListResponse,
    FavoriteListItem,
)
from app.schemas.lot import LotResponse

router = APIRouter()


async def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify the cron secret header for GitHub Actions"""
    cron_secret = getattr(settings, 'CRON_SECRET', None)
    if not cron_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRON_SECRET not configured"
        )
    if not x_cron_secret or x_cron_secret != cron_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret"
        )


def _serialize_tags(raw_tags: str | None) -> List[str] | None:
    if not raw_tags:
        return None
    tags = [tag.strip() for tag in raw_tags.split(",")]
    return [tag for tag in tags if tag]


def _deserialize_tags(tags: List[str] | None) -> str | None:
    if not tags:
        return None
    cleaned = [tag.strip() for tag in tags if tag.strip()]
    return ",".join(cleaned) if cleaned else None


@router.get("", response_model=FavoriteListResponse)
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all favorites for current user"""
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(desc(Favorite.created_at))
    )
    favorites = result.scalars().all()
    items: List[FavoriteListItem] = []

    for favorite in favorites:
        lot_result = await db.execute(select(Lot).where(Lot.id == favorite.lot_id))
        lot = lot_result.scalar_one_or_none()
        if not lot:
            continue

        items.append(
            FavoriteListItem(
                id=favorite.id,
                lot_id=lot.id,
                lot_number=lot.lot_number,
                lot_title=lot.title,
                lot_price=lot.price,
                lot_status=lot.status,
                lot_image_url=lot.image_url,
                lot_url=lot.url,
                notes=favorite.notes,
                tags=_serialize_tags(favorite.tags),
                created_at=favorite.created_at,
                price_changed=False,  # TODO: améliorer avec l'historique des prix
            )
        )

    return FavoriteListResponse(items=items)


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a lot to favorites"""
    # Check if lot exists
    lot_result = await db.execute(select(Lot).where(Lot.id == favorite_data.lot_id))
    lot = lot_result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Check if already favorited
    existing_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.lot_id == favorite_data.lot_id
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lot already in favorites"
        )

    # Create favorite
    favorite = Favorite(
        user_id=current_user.id,
        lot_id=favorite_data.lot_id,
        tags=_deserialize_tags(favorite_data.tags),
        notes=favorite_data.notes
    )
    db.add(favorite)

    # Update lot favorite count
    lot.favorite_count += 1

    await db.commit()
    await db.refresh(favorite)

    return FavoriteResponse(
        id=favorite.id,
        lot_id=favorite.lot_id,
        tags=_serialize_tags(favorite.tags),
        notes=favorite.notes,
        user_id=favorite.user_id,
        created_at=favorite.created_at,
    )


@router.patch("/{favorite_id}", response_model=FavoriteResponse)
async def patch_favorite(
    favorite_id: int,
    favorite_data: FavoriteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update favorite tags/notes"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    # Update fields
    if favorite_data.tags is not None:
        favorite.tags = _deserialize_tags(favorite_data.tags)
    if favorite_data.notes is not None:
        favorite.notes = favorite_data.notes

    await db.commit()
    await db.refresh(favorite)

    return FavoriteResponse(
        id=favorite.id,
        lot_id=favorite.lot_id,
        tags=_serialize_tags(favorite.tags),
        notes=favorite.notes,
        user_id=favorite.user_id,
        created_at=favorite.created_at,
    )


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a favorite"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.lot_id == lot_id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    # Update lot favorite count
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()
    if lot and lot.favorite_count > 0:
        lot.favorite_count -= 1

    await db.delete(favorite)
    await db.commit()

    return None


@router.get("/lots", response_model=List[LotResponse])
async def get_all_favorited_lots(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """
    Get all lots that have been favorited by at least one user.
    Used by GitHub Actions to scrape prices.
    Requires CRON_SECRET header.
    """
    result = await db.execute(
        select(Lot)
        .join(Favorite, Favorite.lot_id == Lot.id)
        .options(selectinload(Lot.sale))
        .where(Lot.url.isnot(None))
        .where(Lot.url != "")
        .where(Lot.url != "N/A")
        .where(Lot.is_active == 1)
        .distinct()
    )
    lots = result.scalars().all()

    # Transform to response format
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

    return items
