from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.db.base import Base


class Notification(Base):
    """User notifications model"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=True)  # info, warning, success, error

    is_read = Column(Boolean, default=False, index=True)
    link = Column(String, nullable=True)  # Optional link to related resource

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.title} for user={self.user_id}>"
