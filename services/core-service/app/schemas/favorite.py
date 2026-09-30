from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.schemas.lot import LotResponse, image_url_to_str


class FavoriteBase(BaseModel):
    """Base favorite schema"""
    lot_id: int
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class FavoriteCreate(FavoriteBase):
    """Favorite creation schema"""
    pass


class FavoriteUpdate(BaseModel):
    """Favorite update schema"""
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class FavoriteResponse(FavoriteBase):
    """Favorite response schema"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteWithLot(FavoriteResponse):
    """Favorite with lot details"""
    lot: LotResponse


class FavoriteListItem(BaseModel):
    """Favorite item returned to frontend"""
    id: int
    lot_id: int
    lot_number: int
    lot_title: str
    lot_price: Optional[int] = None
    lot_status: Optional[str] = None
    lot_image_url: Optional[str] = None
    lot_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    price_changed: bool = False

    _image_url_to_str = field_validator("lot_image_url", mode="before")(image_url_to_str)


class FavoriteListResponse(BaseModel):
    """Favorite list response payload"""
    items: List[FavoriteListItem]
