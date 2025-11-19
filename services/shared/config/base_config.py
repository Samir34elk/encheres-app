"""Base configuration for all microservices"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class BaseServiceConfig(BaseSettings):
    """Base configuration shared by all services"""

    # Service Info
    SERVICE_NAME: str = Field(default="base-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: Optional[str] = Field(default=None)
    DATABASE_URL_SYNC: Optional[str] = Field(default=None)
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_RECYCLE: int = Field(default=1800)

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # Message Bus (RabbitMQ)
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@rabbitmq:5672/")

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )

    # Service URLs (for inter-service communication)
    AUTH_SERVICE_URL: str = Field(default="http://auth-service:8001")
    CORE_SERVICE_URL: str = Field(default="http://core-service:8002")
    SCRAPER_SERVICE_URL: str = Field(default="http://scraper-service:8003")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification-service:8004")
    ADMIN_SERVICE_URL: str = Field(default="http://admin-service:8005")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_database_url() -> str:
    """Get database URL with automatic driver conversion"""
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def get_database_url_sync() -> str:
    """Get synchronous database URL"""
    url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url
