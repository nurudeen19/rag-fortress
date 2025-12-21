"""
Simple caching layer - Redis with in-memory fallback.
"""

import json
from typing import Any, Optional, Union
from datetime import timedelta

from app.core import get_logger
from app.config.settings import settings


logger = get_logger(__name__)


class RedisBackend:
    """Redis cache backend."""
    
    def __init__(self, url: str, **redis_options):
        self.url = url
        self.redis_options = redis_options
        self._redis = None
    
    async def _get_redis(self):
        """Initialize Redis connection."""
        if self._redis is None:
            import redis.asyncio as aioredis
            
            options = {
                "encoding": "utf-8",
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_keepalive": True,
                **self.redis_options
            }
            
            self._redis = await aioredis.from_url(self.url, **options)
            await self._redis.ping()
            logger.info("✓ Redis cache connected")
        return self._redis
    
    async def get(self, key: str) -> Optional[str]:
        try:
            redis = await self._get_redis()
            return await redis.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        try:
            redis = await self._get_redis()
            if ttl:
                await redis.setex(key, ttl, value)
            else:
                await redis.set(key, value)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            await redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis pattern delete failed: {e}")
            return 0
    
    async def close(self):
        if self._redis:
            await self._redis.close()


class MemoryBackend:
    """In-memory cache backend."""
    
    def __init__(self):
        self._cache = {}
        self._ttls = {}
    
    async def get(self, key: str) -> Optional[str]:
        import time
        if key in self._ttls and time.time() > self._ttls[key]:
            del self._cache[key]
            del self._ttls[key]
            return None
        return self._cache.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        import time
        self._cache[key] = value
        if ttl:
            self._ttls[key] = time.time() + ttl
        return True
    
    async def delete(self, key: str) -> bool:
        self._cache.pop(key, None)
        self._ttls.pop(key, None)
        return True
    
    async def invalidate_pattern(self, pattern: str) -> int:
        pattern = pattern.replace('*', '')
        keys = [k for k in list(self._cache.keys()) if k.startswith(pattern)]
        for key in keys:
            del self._cache[key]
            self._ttls.pop(key, None)
        return len(keys)
    
    async def close(self):
        pass


class Cache:
    """Simple cache with JSON serialization."""
    
    def __init__(self, backend):
        self.backend = backend
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            value = await self.backend.get(key)
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in cache."""
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            value_str = json.dumps(value)
            return await self.backend.set(key, value_str, ttl)
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return await self.backend.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            return await self.backend.invalidate_pattern(pattern)
        except Exception as e:
            logger.warning(f"Cache pattern error for {pattern}: {e}")
            return 0
    
    async def close(self):
        """Close cache connection."""
        await self.backend.close()


# Global cache instance
_cache_instance: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _cache_instance


async def initialize_cache(
    redis_url: Optional[str] = None,
    use_redis: bool = True,
    redis_options: Optional[dict] = None
):
    """
    Initialize cache with automatic fallback to in-memory.
    
    The use_redis parameter is controlled by startup settings:
    - True when CACHE_ENABLED=true AND CACHE_BACKEND=redis
    - False otherwise (uses memory backend)
    """
    global _cache_instance
    
    if _cache_instance is not None:
        return _cache_instance
    
    backend = None
    
    # Try Redis if enabled
    if use_redis:
        try:
            from app.config.cache_settings import cache_settings
            url = redis_url or cache_settings.get_redis_url()
            options = redis_options or cache_settings.get_redis_options()
            
            backend = RedisBackend(url, **options)
            await backend._get_redis()
            logger.info("✓ Redis cache initialized")
        
        except ImportError:
            logger.warning("⚠ redis package not installed, using in-memory cache")
            backend = None
        except Exception as e:
            logger.warning(f"⚠ Redis failed: {e}, using in-memory cache")
            backend = None
    
    # Fallback to memory
    if backend is None:
        backend = MemoryBackend()
        logger.info("✓ In-memory cache initialized")
    
    _cache_instance = Cache(backend)
    return _cache_instance


async def close_cache():
    """Close cache connection."""
    global _cache_instance
    if _cache_instance:
        await _cache_instance.close()
        _cache_instance = None

