"""Notification Service configuration"""
import os
import sys

shared_path = "/app/shared" if os.path.exists("/app/shared") else os.path.join(
    os.path.dirname(__file__), "../../../shared"
)
sys.path.insert(0, shared_path)

from pydantic import Field
from shared.config import BaseServiceConfig


class NotificationServiceConfig(BaseServiceConfig):
    """Configuration for the notification/email microservice"""

    SERVICE_NAME: str = Field(default="notification-service")
    PORT: int = Field(default=8004)


settings = NotificationServiceConfig()
