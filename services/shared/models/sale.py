from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base


class Sale(Base):
    """Sale/Auction model"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, closed, upcoming
    total_lots = Column(Integer, default=0)
    url = Column(String(500), nullable=True)
    is_scraped = Column(Boolean, default=False)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    lots = relationship("Lot", back_populates="sale")
