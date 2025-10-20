from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_active_user
)
from app.core.rate_limit import check_rate_limit
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token

router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set httpOnly cookies for authentication tokens"""
    secure_cookie = settings.COOKIE_SECURE
    same_site = settings.COOKIE_SAMESITE
    cookie_domain = settings.COOKIE_DOMAIN

    # Access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite=same_site,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=cookie_domain
    )

    # Refresh token cookie (long-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite=same_site,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=cookie_domain
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies"""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=settings.COOKIE_DOMAIN
    )


async def auth_rate_limit(request: Request):
    """Rate limit dependency for auth endpoints"""
    await check_rate_limit(
        request,
        max_requests=settings.AUTH_RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(auth_rate_limit)
):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(auth_rate_limit)
):
    """Login with email and password - Sets httpOnly cookies"""
    # Find user by email (using username field from OAuth2 form)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set httpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    # Also return in response body for backward compatibility
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token - Sets httpOnly cookies"""
    access_token = create_access_token(data={"sub": str(current_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(current_user.id)})

    # Set httpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """Logout - Clears httpOnly cookies"""
    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}
