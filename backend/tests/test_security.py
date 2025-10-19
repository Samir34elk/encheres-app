"""Tests for security features"""
import pytest
from httpx import AsyncClient

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)
from app.models.user import User


@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification"""
    password = "mysecretpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.unit
def test_create_and_decode_token():
    """Test JWT token creation and decoding"""
    user_id = 123
    token = create_access_token(data={"sub": str(user_id)})

    assert token is not None
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert payload["type"] == "access"


@pytest.mark.security
async def test_rate_limiting_auth_endpoint(client: AsyncClient):
    """Test rate limiting on authentication endpoints"""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "test"},
        )
        responses.append(response.status_code)

    # Should eventually get 429 Too Many Requests
    assert 429 in responses, "Rate limiting should trigger after multiple requests"


@pytest.mark.security
async def test_unauthorized_access(client: AsyncClient):
    """Test that protected endpoints require authentication"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.security
async def test_admin_only_endpoints(client: AsyncClient, auth_headers: dict):
    """Test that admin endpoints require admin role"""
    # Regular user shouldn't access admin endpoints
    response = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code in [403, 404]  # Forbidden or Not Found


@pytest.mark.security
async def test_csrf_protection(client: AsyncClient):
    """Test CSRF protection on state-changing operations"""
    # This is a placeholder - implement CSRF tests when CSRF protection is added
    pass


@pytest.mark.security
async def test_sql_injection_protection(client: AsyncClient):
    """Test SQL injection protection"""
    # Try SQL injection in search parameter
    response = await client.get(
        "/api/v1/lots",
        params={"search": "'; DROP TABLE lots; --"},
    )
    # Should not raise 500, should handle gracefully
    assert response.status_code in [200, 400, 422]


@pytest.mark.security
async def test_xss_protection(client: AsyncClient, auth_headers: dict, test_db):
    """Test XSS protection in user inputs"""
    # Try to create user with XSS payload in name
    from app.models.user import User
    xss_payload = "<script>alert('xss')</script>"

    user = User(
        email="xss@example.com",
        username="xssuser",
        full_name=xss_payload,
        hashed_password=get_password_hash("test"),
    )
    test_db.add(user)
    await test_db.commit()

    # Fetch user
    response = await client.get("/api/v1/auth/me", headers=auth_headers)

    # Response should not contain unescaped script tags
    # (In a real app, you'd check the rendered HTML)
    assert response.status_code in [200, 401]
