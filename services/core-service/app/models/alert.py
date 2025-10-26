from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    PRICE_DROP = "price_drop"
    PRICE_BELOW = "price_below"
    ANY_CHANGE = "any_change"
    PRICE_CHANGE = "price_change"  # alias conservé pour compatibilité
    NEW_LOT = "new_lot"
    KEYWORD = "keyword"


class Alert(Base):
    """User alerts model"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=True, index=True)

    alert_type = Column(Enum(AlertType), nullable=False)
    is_active = Column(Boolean, default=True)

    # Alert conditions
    keyword = Column(String, nullable=True)  # For keyword alerts
    target_price = Column(Integer, nullable=True)  # For price alerts
    location = Column(String, nullable=True)  # For location-specific alerts

    # Email notification
    email_enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alerts")
    lot = relationship("Lot", back_populates="alerts")

    def __repr__(self):
        return f"<Alert {self.alert_type} for user={self.user_id} lot={self.lot_id}>"
