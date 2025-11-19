"""Admin Service configuration"""
import os
import sys

shared_path = "/app/shared" if os.path.exists("/app/shared") else os.path.join(
    os.path.dirname(__file__), "../../../shared"
)
sys.path.insert(0, shared_path)

from pydantic import Field
from shared.config import BaseServiceConfig


class AdminServiceConfig(BaseServiceConfig):
    """Configuration for the admin orchestration service"""

    SERVICE_NAME: str = Field(default="admin-service")
    PORT: int = Field(default=8005)

    ENABLE_INTERNAL_SCRAPER: bool = Field(default=True)
    SALE_REFRESH_HOURS: int = Field(default=24)


settings = AdminServiceConfig()
