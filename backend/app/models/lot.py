from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Lot(Base):
    """Auction lot model"""
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)
    lot_number = Column(Integer, index=True, nullable=False)

    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    status = Column(String, nullable=True)
    depot_location = Column(String, nullable=True, index=True)

    url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 0 = archived, 1 = active

    # Popularity metrics
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)

    # Relationships
    sale = relationship("Sale", back_populates="lots")
    favorites = relationship("Favorite", back_populates="lot", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="lot", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="lot", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="lot", cascade="all, delete-orphan")

    # Indexes for performance
    # Note: GIN trigram index requires pg_trgm extension which may not be available on free tier
    # Using standard indexes instead for compatibility
    __table_args__ = (
        Index('idx_lot_active', 'is_active', 'last_updated'),
    )

    def __repr__(self):
        return f"<Lot {self.lot_number}: {self.title}>"
