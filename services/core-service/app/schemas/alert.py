from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.alert import AlertType


class AlertBase(BaseModel):
    """Base alert schema"""
    alert_type: AlertType
    lot_id: Optional[int] = None
    keyword: Optional[str] = None
    target_price: Optional[int] = None
    location: Optional[str] = None
    email_enabled: bool = True
    is_active: bool = True


class AlertCreate(AlertBase):
    """Alert creation schema"""
    lot_id: int


class AlertUpdate(BaseModel):
    """Alert update schema"""
    alert_type: Optional[AlertType] = None
    target_price: Optional[int] = None
    is_active: Optional[bool] = None
    email_enabled: Optional[bool] = None


class AlertResponse(AlertBase):
    """Alert response schema"""
    id: int
    user_id: int
    created_at: datetime
    last_triggered: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertListItem(BaseModel):
    """Alert item returned to the frontend"""
    id: int
    lot_id: int
    lot_number: int
    lot_title: str
    lot_price: Optional[int] = None
    alert_type: AlertType
    target_price: Optional[int] = None
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None


class AlertListResponse(BaseModel):
    """List response wrapper"""
    items: List[AlertListItem]
