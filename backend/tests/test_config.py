"""Tests for configuration"""
import pytest
from app.core.config import settings


@pytest.mark.unit
def test_settings_loaded():
    """Test that settings are loaded correctly"""
    assert settings.APP_NAME == "Enchères du Domaine"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_V1_PREFIX == "/api/v1"


@pytest.mark.unit
def test_secret_key_is_secure():
    """Test that SECRET_KEY is set and secure"""
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) >= 32
    assert settings.SECRET_KEY != "your-secret-key-change-in-production"


@pytest.mark.unit
def test_cors_origins():
    """Test CORS origins are configured"""
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
    assert len(settings.BACKEND_CORS_ORIGINS) > 0


@pytest.mark.unit
def test_rate_limiting_config():
    """Test rate limiting configuration"""
    assert settings.RATE_LIMIT_PER_MINUTE > 0
    assert settings.AUTH_RATE_LIMIT_PER_MINUTE > 0
    assert settings.AUTH_RATE_LIMIT_PER_MINUTE <= settings.RATE_LIMIT_PER_MINUTE


@pytest.mark.unit
def test_database_pool_config():
    """Test database pool configuration"""
    assert settings.DB_POOL_SIZE > 0
    assert settings.DB_MAX_OVERFLOW >= 0
    assert settings.DB_POOL_RECYCLE > 0
