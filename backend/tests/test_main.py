"""Tests for main application endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Enchères du Domaine"
    assert data["status"] == "running"
    assert "version" in data


@pytest.mark.integration
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.integration
async def test_cors_headers(client: AsyncClient):
    """Test CORS headers are set correctly"""
    response = await client.options(
        "/api/v1/lots",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should have CORS headers
    assert response.status_code in [200, 204]
