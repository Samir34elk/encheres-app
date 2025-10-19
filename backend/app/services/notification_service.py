from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from datetime import datetime

from app.models.notification import Notification
from app.models.alert import Alert, AlertType
from app.models.lot import Lot
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and alerts"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link: Optional[str] = None
    ) -> Notification:
        """Create a new notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def trigger_price_alerts(
        self,
        lot: Lot,
        new_price: Optional[int],
        previous_price: Optional[int] = None
    ):
        """Trigger alerts for price changes"""
        if new_price is None:
            return

        # Get all active price alerts
        result = await self.db.execute(
            select(Alert).where(
                Alert.is_active == True,
                Alert.lot_id == lot.id,
                Alert.alert_type.in_([
                    AlertType.PRICE_DROP,
                    AlertType.PRICE_BELOW,
                    AlertType.PRICE_CHANGE,
                    AlertType.ANY_CHANGE
                ])
            )
        )
        alerts = result.scalars().all()

        for alert in alerts:
            should_notify = False
            notification_type = "info"

            if alert.alert_type in (AlertType.PRICE_CHANGE, AlertType.ANY_CHANGE):
                if previous_price is None or new_price != previous_price:
                    should_notify = True
            elif alert.alert_type == AlertType.PRICE_DROP:
                if previous_price is not None and new_price < previous_price:
                    should_notify = True
                    notification_type = "success"
            elif alert.alert_type == AlertType.PRICE_BELOW:
                if alert.target_price is not None and new_price <= alert.target_price:
                    should_notify = True
                    notification_type = "warning"

            # Optional price threshold for custom scenarios
            if alert.target_price and new_price > alert.target_price:
                # Pour PRICE_BELOW on garde la condition précédente
                if alert.alert_type != AlertType.PRICE_BELOW:
                    should_notify = False

            # Check location filter (legacy)
            if alert.location and alert.location.lower() not in (lot.depot_location or "").lower():
                should_notify = False

            if should_notify:
                alert.last_triggered = datetime.utcnow()
                await self.create_notification(
                    user_id=alert.user_id,
                    title=f"Prix modifié: {lot.title[:50]}...",
                    message=f"Le lot #{lot.lot_number} a un nouveau prix: {new_price}€",
                    notification_type=notification_type,
                    link=f"/lots/{lot.id}"
                )
                logger.info(f"Price alert triggered for user {alert.user_id}, lot {lot.lot_number}")

    async def trigger_new_lot_alerts(self, lot: Lot):
        """Trigger alerts for new lots"""
        # Get all active new lot alerts
        result = await self.db.execute(
            select(Alert).where(
                Alert.is_active == True,
                Alert.alert_type == AlertType.NEW_LOT
            )
        )
        alerts = result.scalars().all()

        for alert in alerts:
            should_notify = True

            # Check keyword
            if alert.keyword:
                keyword_lower = alert.keyword.lower()
                if keyword_lower not in (lot.title or "").lower() and \
                   keyword_lower not in (lot.description or "").lower():
                    should_notify = False

            # Check price threshold
            if alert.target_price and lot.price and lot.price > alert.target_price:
                should_notify = False

            # Check location
            if alert.location and alert.location.lower() not in (lot.depot_location or "").lower():
                should_notify = False

            if should_notify:
                await self.create_notification(
                    user_id=alert.user_id,
                    title=f"Nouveau lot: {lot.title[:50]}...",
                    message=f"Un nouveau lot correspond à vos critères: #{lot.lot_number}",
                    notification_type="success",
                    link=f"/lots/{lot.id}"
                )
                logger.info(f"New lot alert triggered for user {alert.user_id}, lot {lot.lot_number}")

    async def trigger_keyword_alerts(self, lot: Lot):
        """Trigger keyword-based alerts"""
        # Get all active keyword alerts
        result = await self.db.execute(
            select(Alert).where(
                Alert.is_active == True,
                Alert.alert_type == AlertType.KEYWORD,
                Alert.keyword.isnot(None)
            )
        )
        alerts = result.scalars().all()

        for alert in alerts:
            keyword_lower = alert.keyword.lower()
            if keyword_lower in (lot.title or "").lower() or \
               keyword_lower in (lot.description or "").lower():

                await self.create_notification(
                    user_id=alert.user_id,
                    title=f"Mot-clé trouvé: {alert.keyword}",
                    message=f"Le lot #{lot.lot_number} correspond à votre recherche",
                    notification_type="info",
                    link=f"/lots/{lot.id}"
                )
