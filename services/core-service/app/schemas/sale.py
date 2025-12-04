from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SaleBase(BaseModel):
    """Base sale schema"""
    sale_number: int
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "active"
    url: Optional[str] = None


class SaleCreate(SaleBase):
    """Sale creation schema"""
    pass


class SaleUpdate(BaseModel):
    """Sale update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    total_lots: Optional[int] = None
    is_scraped: Optional[bool] = None
    last_scraped_at: Optional[datetime] = None


class SaleResponse(SaleBase):
    """Sale response schema"""
    id: int
    total_lots: Optional[int] = None
    is_scraped: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    """Paginated sale list response"""
    items: List[SaleResponse]
    total: int
    page: int
    size: int
    pages: int
