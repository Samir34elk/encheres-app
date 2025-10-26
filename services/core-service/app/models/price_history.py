from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class PriceHistory(Base):
    """Price history tracking model"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False, index=True)

    price = Column(Integer, nullable=False)
    status = Column(String, nullable=True)

    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    lot = relationship("Lot", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory lot={self.lot_id} price={self.price}>"
