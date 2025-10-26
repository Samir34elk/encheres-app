"""Auth Service configuration"""
import sys
import os
from typing import List

# Add shared library to path
# In Docker: /app/shared, in local dev: ../../../shared
shared_path = "/app/shared" if os.path.exists("/app/shared") else os.path.join(os.path.dirname(__file__), "../../../shared")
sys.path.insert(0, shared_path)

from shared.config import BaseServiceConfig
from pydantic import Field


class AuthServiceConfig(BaseServiceConfig):
    """Configuration for Auth Service"""

    SERVICE_NAME: str = Field(default="auth-service")
    PORT: int = Field(default=8001)

    # Auth specific settings
    COOKIE_SECURE: bool = Field(default=False)
    COOKIE_SAMESITE: str = Field(default="lax")
    COOKIE_DOMAIN: str = Field(default=None)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # OAuth2
    GOOGLE_CLIENT_ID: str = Field(default=None)
    GOOGLE_CLIENT_SECRET: str = Field(default=None)
    GITHUB_CLIENT_ID: str = Field(default=None)
    GITHUB_CLIENT_SECRET: str = Field(default=None)

    # Rate limiting
    AUTH_RATE_LIMIT_PER_MINUTE: int = Field(default=5)


settings = AuthServiceConfig()
