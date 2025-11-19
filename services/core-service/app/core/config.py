"""Core Service configuration"""
import os
import sys

# Add shared library to path whether running in Docker or locally
shared_path = "/app/shared" if os.path.exists("/app/shared") else os.path.join(
    os.path.dirname(__file__), "../../../shared"
)
sys.path.insert(0, shared_path)

from pydantic import Field
from shared.config import BaseServiceConfig


class CoreServiceConfig(BaseServiceConfig):
    """Configuration for the core domain service"""

    SERVICE_NAME: str = Field(default="core-service")
    PORT: int = Field(default=8002)

    # API specific settings
    MAX_PAGE_SIZE: int = Field(default=50)
    CRON_SECRET: str = Field(default="dev-cron-secret")


settings = CoreServiceConfig()
