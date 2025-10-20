from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    """Application settings with environment variables support"""

    # Application
    APP_NAME: str = "Enchères du Domaine"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/encheres"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/encheres"

    # Security - CRITICAL: Must be set in environment variables!
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate secure key if not provided
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Optional[str] = None

    # OAuth2
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # CORS - Restricted to specific origins
    BACKEND_CORS_ORIGINS: List[str] | str = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 5

    # Email
    MAIL_USERNAME: str = "noreply@encheres.com"
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@encheres.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Scraper
    SCRAPER_INTERVAL_MINUTES: int = 15
    AUCTION_BASE_URL: str = "https://encheres-domaine.gouv.fr"
    AUCTION_SALE_NUMBER: int = 42
    SALE_REFRESH_HOURS: int = 24

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 10000

    # Database Pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Convert postgresql:// to postgresql+asyncpg:// for async support
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Validate critical settings
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            import logging
            logging.warning("SECRET_KEY is not set or too short. Using generated key. SET THIS IN PRODUCTION!")
        if self.DEBUG:
            import logging
            logging.warning("DEBUG mode is ON. Disable in production!")

        # Normalize CORS origins if provided as comma-separated string
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            self.BACKEND_CORS_ORIGINS = [
                origin.strip()
                for origin in self.BACKEND_CORS_ORIGINS.split(",")
                if origin.strip()
            ]

        # Normalize cookie SameSite setting
        self.COOKIE_SAMESITE = (self.COOKIE_SAMESITE or "lax").lower()

        # Adjust cookie settings in production
        if not self.DEBUG:
            # Ensure secure cookies by default when not in debug mode
            self.COOKIE_SECURE = True
            # SameSite must be 'none' for cross-site cookies when secure
            if not self.COOKIE_SAMESITE or self.COOKIE_SAMESITE == "lax":
                self.COOKIE_SAMESITE = "none"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
