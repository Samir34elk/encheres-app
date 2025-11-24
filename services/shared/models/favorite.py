from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Favorite(Base):
    """User favorite lots model"""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)

    tags = Column(String, nullable=True)  # Custom tags: "to watch", "deal", etc.
    notes = Column(String, nullable=True)  # Personal notes

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="favorites")
    lot = relationship("Lot", back_populates="favorites")

    # Ensure a user can only favorite a lot once
    __table_args__ = (
        UniqueConstraint('user_id', 'lot_id', name='uq_user_lot_favorite'),
    )

    def __repr__(self):
        return f"<Favorite user={self.user_id} lot={self.lot_id}>"
