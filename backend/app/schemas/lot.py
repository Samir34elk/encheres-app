from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LotBase(BaseModel):
    """Base lot schema"""
    lot_number: int
    title: str
    description: Optional[str] = None
    price: Optional[int] = None
    status: Optional[str] = None
    depot_location: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class LotCreate(LotBase):
    """Lot creation schema"""
    pass


class LotUpdate(BaseModel):
    """Lot update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    status: Optional[str] = None
    depot_location: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[int] = None


class LotResponse(LotBase):
    """Lot response schema"""
    id: int
    first_seen: datetime
    last_updated: datetime
    is_active: int
    view_count: int
    favorite_count: int

    class Config:
        from_attributes = True


class LotWithFavorite(LotResponse):
    """Lot with user favorite status"""
    is_favorited: bool = False
    user_tags: Optional[str] = None
    user_notes: Optional[str] = None


class LotListResponse(BaseModel):
    """Paginated lot list response"""
    items: List[LotResponse]
    total: int
    page: int
    size: int
    pages: int


class PriceHistoryResponse(BaseModel):
    """Price history response schema"""
    id: int
    price: int
    status: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True
