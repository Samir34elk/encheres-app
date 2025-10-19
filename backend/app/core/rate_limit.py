"""Rate limiting middleware for API endpoints"""
from fastapi import Request, HTTPException, status
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is allowed based on rate limit

        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            bool: True if request is allowed, False otherwise
        """
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)

            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]

            # Check if limit exceeded
            if len(self.requests[identifier]) >= max_requests:
                return False

            # Add current request
            self.requests[identifier].append(now)
            return True

    async def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Periodically cleanup old entries to prevent memory leak"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=max_age_seconds)

            keys_to_delete = []
            for identifier, requests in self.requests.items():
                if not requests or all(req_time < cutoff for req_time in requests):
                    keys_to_delete.append(identifier)

            for key in keys_to_delete:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    max_requests: int,
    window_seconds: int = 60,
    identifier: Optional[str] = None
):
    """
    Dependency to check rate limit

    Args:
        request: FastAPI request object
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        identifier: Optional custom identifier (defaults to client IP)

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use custom identifier or fall back to client IP
    client_id = identifier or request.client.host

    allowed = await rate_limiter.is_allowed(
        identifier=client_id,
        max_requests=max_requests,
        window_seconds=window_seconds
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
            headers={"Retry-After": str(window_seconds)}
        )
