import json
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


def image_url_to_str(value: Any) -> Any:
    """La colonne image_url peut être du texte ou du JSONB (liste d'URLs) selon
    le service qui a créé la table : on renvoie toujours du texte, que le
    frontend sait décoder (voir frontend/src/utils/normalizeImageUrl.ts)."""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


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
    categories: Optional[List[str]] = None
    caracteristiques: Optional[Dict[str, Any]] = None
    professionnel: bool = False
    price_reserve: Optional[int] = None

    _image_url_to_str = field_validator("image_url", mode="before")(image_url_to_str)


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
    categories: Optional[List[str]] = None
    caracteristiques: Optional[Dict[str, Any]] = None
    professionnel: Optional[bool] = None
    price_reserve: Optional[int] = None


class LotResponse(LotBase):
    """Lot response schema"""
    id: int
    sale_id: Optional[int] = None
    sale_end_date: Optional[datetime] = None
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
