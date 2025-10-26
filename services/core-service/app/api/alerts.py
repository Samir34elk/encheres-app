from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.alert import Alert, AlertType
from app.models.lot import Lot
from app.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertListItem,
    AlertListResponse,
)

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def get_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all alerts for current user"""
    result = await db.execute(
        select(Alert).where(Alert.user_id == current_user.id)
    )
    alerts = result.scalars().all()

    items: list[AlertListItem] = []
    for alert in alerts:
        if not alert.lot_id:
            # On ne renvoie que les alertes liées à un lot spécifique pour le frontend
            continue

        lot_result = await db.execute(select(Lot).where(Lot.id == alert.lot_id))
        lot = lot_result.scalar_one_or_none()
        if not lot:
            # Lot supprimé : on ignore l'alerte associée
            continue

        items.append(
            AlertListItem(
                id=alert.id,
                lot_id=lot.id,
                lot_number=lot.lot_number,
                lot_title=lot.title,
                lot_price=lot.price,
                alert_type=alert.alert_type,
                target_price=alert.target_price,
                is_active=alert.is_active,
                created_at=alert.created_at,
                last_triggered=alert.last_triggered,
            )
        )

    return AlertListResponse(items=items)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new alert"""
    lot_result = await db.execute(select(Lot).where(Lot.id == alert_data.lot_id))
    lot = lot_result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # Eviter les doublons pour le même lot / type d'alerte
    existing_result = await db.execute(
        select(Alert).where(
            Alert.user_id == current_user.id,
            Alert.lot_id == alert_data.lot_id,
            Alert.alert_type == alert_data.alert_type
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert already exists for this lot"
        )

    alert = Alert(
        user_id=current_user.id,
        lot_id=alert_data.lot_id,
        alert_type=alert_data.alert_type,
        target_price=alert_data.target_price,
        email_enabled=alert_data.email_enabled,
        is_active=alert_data.is_active
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an alert"""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert_data.alert_type is not None:
        alert.alert_type = alert_data.alert_type
    if alert_data.target_price is not None:
        alert.target_price = alert_data.target_price
    if alert_data.is_active is not None:
        alert.is_active = alert_data.is_active
    if alert_data.email_enabled is not None:
        alert.email_enabled = alert_data.email_enabled

    await db.commit()
    await db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an alert"""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    return None
