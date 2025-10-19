"""Tests for authentication endpoints"""
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.integration
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data  # Should not expose password


@pytest.mark.integration
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """Test registration with duplicate email"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "username": "differentusername",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_register_duplicate_username(client: AsyncClient, test_user: User):
    """Test registration with duplicate username"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "different@example.com",
            "username": test_user.username,
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "username already taken" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Check cookies are set
    assert "access_token" in response.cookies or "Set-Cookie" in response.headers


@pytest.mark.integration
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Test login with wrong password"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "password"},
    )

    assert response.status_code == 401


@pytest.mark.integration
async def test_get_current_user(client: AsyncClient, auth_headers: dict, test_user: User):
    """Test getting current user info"""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


@pytest.mark.integration
async def test_refresh_token(client: AsyncClient, auth_headers: dict):
    """Test token refresh"""
    response = await client.post("/api/v1/auth/refresh", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.integration
async def test_logout(client: AsyncClient, auth_headers: dict):
    """Test logout"""
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)

    assert response.status_code == 200
    assert "successfully logged out" in response.json()["message"].lower()
