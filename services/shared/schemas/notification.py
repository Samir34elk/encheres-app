from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str
    message: str
    notification_type: Optional[str] = "info"
    link: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Notification creation schema"""
    user_id: int


class NotificationResponse(NotificationBase):
    """Notification response schema"""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response"""
    items: List[NotificationResponse]
    total: int
    unread_count: int
