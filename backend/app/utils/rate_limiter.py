"""
Rate Limiting Utility

Provides configurable rate limiting for FastAPI endpoints using SlowAPI.
Supports both general application-wide limits and endpoint-specific limits.
"""

from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)

# Global limiter instance
_limiter: Optional[Limiter] = None


def get_limiter() -> Limiter:
    """
    Get or create the rate limiter instance.
    
    Returns:
        Configured Limiter instance
    """
    global _limiter
    
    if _limiter is None:
        # Configure storage backend
        if settings.RATE_LIMIT_STORAGE == "redis" and settings.RATE_LIMIT_REDIS_URL:
            # Use Redis for distributed rate limiting
            logger.info(f"Initializing rate limiter with Redis storage: {settings.RATE_LIMIT_REDIS_URL}")
            _limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=settings.RATE_LIMIT_REDIS_URL,
                enabled=settings.RATE_LIMIT_ENABLED
            )
        else:
            # Use in-memory storage (default)
            logger.info("Initializing rate limiter with in-memory storage")
            _limiter = Limiter(
                key_func=get_remote_address,
                enabled=settings.RATE_LIMIT_ENABLED
            )
    
    return _limiter


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on authenticated user or IP address.
    
    For authenticated users, use user_id for more accurate tracking.
    For anonymous users, fall back to IP address.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key (user_id or IP address)
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    
    # Fall back to IP address
    return get_remote_address(request)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a JSON response with rate limit information.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
        
    Returns:
        JSONResponse with error details
    """
    logger.warning(
        f"Rate limit exceeded for {get_rate_limit_key(request)} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else None
        }
    )


def get_general_rate_limit() -> str:
    """
    Get general rate limit string for application-wide limiting.
    
    Returns:
        Rate limit string (e.g., "60/minute;1000/hour")
    """
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute;{settings.RATE_LIMIT_PER_HOUR}/hour"


def get_conversation_rate_limit() -> str:
    """
    Get stricter rate limit string for conversation/RAG endpoints.
    
    Returns:
        Rate limit string (e.g., "10/minute;100/hour")
    """
    return f"{settings.CONVERSATION_RATE_LIMIT_PER_MINUTE}/minute;{settings.CONVERSATION_RATE_LIMIT_PER_HOUR}/hour"


# Export functions for use in routes
__all__ = [
    "get_limiter",
    "get_rate_limit_key",
    "rate_limit_exceeded_handler",
    "get_general_rate_limit",
    "get_conversation_rate_limit"
]
