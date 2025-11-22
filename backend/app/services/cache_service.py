"""
Simple cache service - get, set, invalidate.

No events, no abstractions, just straightforward caching.
"""

from typing import Any, Optional
from datetime import timedelta
from app.core.cache import get_cache
from app.core import get_logger

logger = get_logger(__name__)


class CacheService:
    """Simple cache operations."""
    
    @staticmethod
    async def get(key: str, default: Any = None) -> Any:
        """Get value from cache."""
        cache = get_cache()
        return await cache.get(key, default=default)
    
    @staticmethod
    async def set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL (seconds)."""
        cache = get_cache()
        return await cache.set(key, value, ttl=ttl)
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache."""
        cache = get_cache()
        return await cache.delete(key)
    
    @staticmethod
    async def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern (e.g., 'user:123:*')."""
        cache = get_cache()
        return await cache.invalidate_pattern(pattern)
