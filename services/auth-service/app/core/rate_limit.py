"""Rate limiting utilities"""
from fastapi import Request

async def check_rate_limit(request: Request,max_requests: int,window_seconds: int):
        """
        Placeholder for rate limiting.
	Real rate limiting is handled by NGINX API Gateway.
        """
        pass
