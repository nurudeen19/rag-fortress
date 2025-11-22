"""
Caching layer for RAG Fortress.

Supports both Redis (production) and in-memory (development) backends.
Implements cache-aside pattern with automatic invalidation.
"""

import json
import hashlib
from typing import Any, Optional, Callable, Union
from datetime import timedelta
from functools import wraps
from abc import ABC, abstractmethod

from app.core import get_logger
from app.config.settings import settings


logger = get_logger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern. Returns count deleted."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close cache connection."""
        pass


class RedisBackend(CacheBackend):
    """Redis cache backend using redis.asyncio."""
    
    def __init__(self, url: str, **redis_options):
        self.url = url
        self.redis_options = redis_options
        self._redis = None
    
    async def _get_redis(self):
        """Lazy initialization of Redis connection with all options."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                
                # Merge default options with custom options
                options = {
                    "encoding": "utf-8",
                    "decode_responses": True,
                    "socket_connect_timeout": 5,
                    "socket_keepalive": True,
                    **self.redis_options  # Override with custom options
                }
                
                self._redis = await aioredis.from_url(self.url, **options)
                await self._redis.ping()
                logger.info(f"Redis cache backend initialized: {self.url}")
            except ImportError:
                logger.error("redis package not installed. Run: pip install redis>=5.0.0")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis at {self.url}: {e}")
                raise
        return self._redis
    
    async def get(self, key: str) -> Optional[str]:
        try:
            redis = await self._get_redis()
            return await redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        try:
            redis = await self._get_redis()
            if ttl:
                return await redis.setex(key, ttl, value)
            else:
                return await redis.set(key, value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            result = await redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            return await redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        try:
            redis = await self._get_redis()
            await redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def close(self):
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache connection closed")


class MemoryBackend(CacheBackend):
    """In-memory cache backend for development/testing."""
    
    def __init__(self):
        self._cache = {}
        self._ttls = {}
        logger.info("In-memory cache backend initialized")
    
    async def get(self, key: str) -> Optional[str]:
        # Check TTL expiration
        import time
        if key in self._ttls:
            if time.time() > self._ttls[key]:
                del self._cache[key]
                del self._ttls[key]
                return None
        return self._cache.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self._cache[key] = value
        if ttl:
            import time
            self._ttls[key] = time.time() + ttl
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self._ttls.pop(key, None)
            return True
        return False
    
    async def delete_pattern(self, pattern: str) -> int:
        # Simple pattern matching (prefix matching)
        pattern = pattern.replace('*', '')
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
        for key in keys_to_delete:
            del self._cache[key]
            self._ttls.pop(key, None)
        return len(keys_to_delete)
    
    async def exists(self, key: str) -> bool:
        await self.get(key)  # Trigger TTL check
        return key in self._cache
    
    async def clear(self) -> bool:
        self._cache.clear()
        self._ttls.clear()
        return True
    
    async def close(self):
        self._cache.clear()
        self._ttls.clear()


class CacheManager:
    """
    Central cache manager implementing cache-aside pattern.
    
    Features:
    - Automatic JSON serialization/deserialization
    - Key namespacing
    - TTL management
    - Pattern-based invalidation
    - Graceful fallback on cache failures
    """
    
    def __init__(self, backend: CacheBackend, namespace: str = "rag_fortress"):
        self.backend = backend
        self.namespace = namespace
        self._enabled = True
    
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with automatic JSON deserialization.
        
        Returns default if key not found or cache error occurs.
        """
        if not self._enabled:
            return default
        
        try:
            cached = await self.backend.get(self._make_key(key))
            if cached is None:
                return default
            return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache with automatic JSON serialization.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live (seconds or timedelta)
        """
        if not self._enabled:
            return False
        
        try:
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            serialized = json.dumps(value)
            return await self.backend.set(self._make_key(key), serialized, ttl)
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete specific cache key."""
        try:
            return await self.backend.delete(self._make_key(key))
        except Exception as e:
            logger.warning(f"Cache delete failed for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching pattern.
        
        Example: invalidate_pattern("file_stats:*")
        """
        try:
            full_pattern = self._make_key(pattern)
            return await self.backend.delete_pattern(full_pattern)
        except Exception as e:
            logger.warning(f"Cache pattern invalidation failed for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.backend.exists(self._make_key(key))
        except Exception as e:
            logger.warning(f"Cache exists check failed for {key}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache entries (use with caution!)."""
        try:
            return await self.backend.clear()
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False
    
    async def close(self):
        """Close cache backend connection."""
        await self.backend.close()
    
    def disable(self):
        """Temporarily disable caching."""
        self._enabled = False
        logger.warning("Cache disabled")
    
    def enable(self):
        """Re-enable caching."""
        self._enabled = True
        logger.info("Cache enabled")


# Decorator for automatic caching
def cached(
    key_prefix: str,
    ttl: Optional[Union[int, timedelta]] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for automatic function result caching.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live for cached result
        key_builder: Optional function to build cache key from args/kwargs
    
    Example:
        @cached("user_profile", ttl=300)
        async def get_user_profile(user_id: int):
            return await db.query(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: hash all args and kwargs
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_hash = hashlib.md5(":".join(key_parts).encode()).hexdigest()[:8]
                cache_key = f"{key_prefix}:{key_hash}"
            
            # Try to get from cache
            cache = get_cache()
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get global cache instance (singleton)."""
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
    Initialize cache backend with automatic fallback.
    
    Attempts to connect to Redis if configured, automatically falls back
    to in-memory cache if Redis is unavailable or not configured.
    
    Args:
        redis_url: Redis connection URL (default from settings)
        use_redis: If False, skip Redis and use in-memory
        redis_options: Additional Redis connection options
    
    Returns:
        Initialized CacheManager instance
    """
    global _cache_instance
    
    if _cache_instance is not None:
        logger.warning("Cache already initialized")
        return _cache_instance
    
    backend = None
    
    # Try Redis if enabled and configured
    if use_redis and settings.CACHE_ENABLED:
        try:
            from app.config.cache_settings import cache_settings
            url = redis_url or cache_settings.get_redis_url()
            options = redis_options or cache_settings.get_redis_options()
            
            backend = RedisBackend(url, **options)
            # Test connection by initializing
            await backend._get_redis()
            
            logger.info(f"✓ Redis cache initialized: {url}")
        
        except ImportError:
            logger.warning("⚠ redis package not installed, falling back to in-memory cache")
            logger.info("  Install Redis support: pip install redis>=5.0.0")
            backend = None
        
        except Exception as e:
            logger.warning(f"⚠ Redis connection failed: {e}")
            logger.info("  Falling back to in-memory cache")
            backend = None
    
    # Fallback to memory backend
    if backend is None:
        backend = MemoryBackend()
        if use_redis:
            logger.info("✓ In-memory cache initialized (fallback mode)")
        else:
            logger.info("✓ In-memory cache initialized (development mode)")
    
    _cache_instance = CacheManager(backend, namespace=settings.cache_key_prefix)
    logger.info("Cache manager ready")
    return _cache_instance


async def close_cache():
    """Close cache connection."""
    global _cache_instance
    if _cache_instance:
        await _cache_instance.close()
        _cache_instance = None
        logger.info("Cache closed")
