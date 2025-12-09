# Caching Strategy Guide

## Overview

RAG Fortress implements a flexible caching layer that supports both **Redis** and **in-memory** backends. The system uses a **cache-aside pattern** with automatic invalidation on data changes.

## Architecture

### Components

1. **Cache Backend** (`app/core/cache.py`)
   - Abstract interface supporting multiple backends
   - Redis backend 
   - In-memory backend 

2. **Cache Manager** (`app/core/cache.py`)
   - Unified API for cache operations
   - Automatic JSON serialization
   - Key namespacing
   - TTL management
   - Pattern-based invalidation

3. **Stats Cache Service** (`app/services/stats_cache.py`)
   - Specialized caching for statistics
   - Automatic invalidation on data changes
   - Event handlers for cache updates

### Why Redis?

- ✅ **Async-first**: Perfect for FastAPI's async architecture
- ✅ **Scalable**: Supports clustering and replication
- ✅ **Flexible**: Multiple data structures (strings, hashes, lists, sets)
- ✅ **TTL Management**: Built-in expiration
- ✅ **Pub/Sub**: Future real-time notifications support
- ✅ **Persistent**: Optional durability for important cached data

## Configuration

### Environment Variables

```bash
# Cache Backend Selection
CACHE_BACKEND=redis          # Options: "redis" or "memory"
CACHE_ENABLED=true           # Enable/disable caching

# Redis Connection (if using Redis)
CACHE_REDIS_URL=redis://localhost:6379/0
# OR configure components:
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
CACHE_REDIS_PASSWORD=          # Optional
CACHE_REDIS_SSL=false

# TTL Configuration (seconds)
CACHE_TTL_DEFAULT=300          # 5 minutes
CACHE_TTL_STATS=60             # 1 minute for stats
CACHE_TTL_CONFIG=3600          # 1 hour for app config
CACHE_TTL_USER_DATA=300        # 5 minutes for user data
```

### Development Setup (In-Memory)

For local development without Redis:

```bash
CACHE_BACKEND=memory
CACHE_ENABLED=true
```

### Production Setup (Redis)

1. **Install Redis**:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

2. **Configure Environment**:
```bash
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
```

3. **Install Python Package**:
```bash
pip install redis>=5.0.0
```

## Usage Patterns

### 1. Direct Cache Access

```python
from app.core.cache import get_cache

# Get cache instance
cache = get_cache()

# Set value with TTL
await cache.set("user:123", {"name": "John"}, ttl=300)

# Get value
user_data = await cache.get("user:123")

# Delete specific key
await cache.delete("user:123")

# Delete by pattern
await cache.invalidate_pattern("user:*")
```

### 2. Helper-based Caching (no built-in decorator)

The core cache implementation (`app/core/cache.py`) exposes a `Cache` API and a global `get_cache()` helper.

Example: direct use

```python
from datetime import timedelta
from app.core.cache import get_cache

async def get_user_profile_cached(user_id: int):
    cache = get_cache()
    key = f"user:profile:{user_id}"
    data = await cache.get(key)
    if data is not None:
        return data

    # Fallback to DB and then cache
    profile = await db.query(User).filter(User.id == user_id).first()
    await cache.set(key, profile, ttl=int(timedelta(minutes=5).total_seconds()))
    return profile
```

Example: minimal async decorator using the cache

```python
from functools import wraps
from app.core.cache import get_cache
from datetime import timedelta

def simple_cached(key_builder, ttl: timedelta):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            key = key_builder(*args, **kwargs)
            val = await cache.get(key)
            if val is not None:
                return val
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl= int(ttl.total_seconds()))
            return result
        return wrapper
    return decorator

# Usage
@simple_cached(lambda user_id: f"user:profile:{user_id}", ttl=timedelta(minutes=5))
async def get_user_profile(user_id: int):
    return await db.query(User).filter(User.id == user_id).first()
```

### 3. Statistics Caching

```python
from app.services.stats_cache import StatsCache

# Get cached job stats
stats = await StatsCache.get_job_stats(session)

# Force refresh (bypass cache)
stats = await StatsCache.get_job_stats(session, force_refresh=True)

# Get file stats for specific user
user_stats = await StatsCache.get_file_stats(session, user_id=123)
```

## Cache Invalidation Strategy

### Automatic Invalidation

The system should invalidate relevant cache entries when the underlying data changes. The cache implementation provides `delete` and `invalidate_pattern` for this purpose; how you trigger invalidation is up to your application logic (handlers, services, or background jobs).

General examples:

```python
# Example: resource created
await on_resource_created(resource_type="document", resource_id=123)
# Suggested invalidation: invalidate listings or summaries for that resource type
await cache.invalidate_pattern("documents:list*")

# Example: resource updated
await on_resource_updated(resource_type="document", resource_id=123)
# Suggested invalidation: invalidate the resource's cache key and any derived summaries
await cache.delete(f"document:{123}")
await cache.invalidate_pattern("documents:*summary*")

# Example: job status changed
await on_job_status_changed(job_id=42, old_status="running", new_status="completed")
# Suggested invalidation: job status caches and any dashboards
await cache.invalidate_pattern("jobs:*")
```

### Manual Invalidation

```python
from app.services.stats_cache import StatsCache

# Invalidate specific stats
await StatsCache.invalidate_file_stats(user_id=123)  # User stats only
await StatsCache.invalidate_file_stats()              # All file stats
await StatsCache.invalidate_job_stats()               # Job stats

# Invalidate all stats
await StatsCache.invalidate_all_stats()
```



## Integration Points

### 1. Event handlers (Automatic Invalidation)

Cache invalidation is typically triggered from event handlers when resources change. Keep handlers generic (resource type + id) and let service-layer code decide which cache keys/patterns to invalidate.

```python
# app/handlers/resource.py
async def handle_create_resource(resource_type: str, resource_id: int, session):
    # ... create logic ...
    await session.commit()

    # Trigger domain-level invalidation
    from app.services.cache_invalidation import on_resource_created
    await on_resource_created(resource_type, resource_id)
```

### 2. Routes (Cached Endpoints)

API endpoints can use cached data:

```python
# app/routes/jobs.py

@router.get("/status")
async def get_job_status(
    force_refresh: bool = False,
    session: AsyncSession = Depends(get_session)
):
    from app.services.stats_cache import StatsCache
    
    stats = await StatsCache.get_job_stats(session, force_refresh=force_refresh)
    
    return {
        "status": "ok",
        "data": stats,
        "cached": not force_refresh
    }
```

### 3. Job Handlers (Bulk Operations)

After bulk operations, warm or rebuild caches for the affected resource sets. Use service-layer warming functions to avoid hammering the cache from many concurrent workers.

```python
# After processing many resources
async def bulk_process_handler():
    # ... processing logic ...

    # Warm cache for quick access (example service)
    from app.services.cache_warmer import warm_resource_caches
    await warm_resource_caches(session, resource_type="document")
```

## Best Practices

### 1. Choose Appropriate TTLs

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Stats (counts) | 60s | Changes frequently with uploads |
| App config | 1 hour | Rarely changes |
| User profiles | 5 min | Balance freshness vs load |
| Search results | 5 min | User-specific, moderate change rate |

### 2. Handle Cache Failures Gracefully

```python
try:
    stats = await StatsCache.get_job_stats(session)
except Exception as e:
    logger.warning(f"Cache failed, using direct query: {e}")
    stats = await calculate_stats_directly(session)
```

### 3. Use Patterns for Bulk Invalidation

```python
# Good: Pattern-based invalidation
await cache.invalidate_pattern("user:*:profile")

# Avoid: Individual deletions in loop
for user_id in user_ids:
    await cache.delete(f"user:{user_id}:profile")  # Slow!
```

### 4. Monitor Cache Performance

```python
# Add metrics in routes
stats = await StatsCache.get_job_stats(session)

return {
    "data": stats,
    "cached": not force_refresh,
    "cache_backend": settings.cache_backend
}
```

## Troubleshooting

### Cache Not Working

1. Check if cache is enabled:
```bash
echo $CACHE_ENABLED
```

2. Verify cache initialization in logs:
```
✓ Cache initialized (redis backend)
```

3. Test cache connection:
```python
from app.core.cache import get_cache

cache = get_cache()
await cache.set("test", "value")
result = await cache.get("test")
print(result)  # Should print: value
```

### Redis Connection Issues

1. Check Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

2. Verify connection URL:
```bash
echo $CACHE_REDIS_URL
```

3. Check firewall/network:
```bash
telnet localhost 6379
```

### Cache Staleness

If data is stale:

1. Check TTL settings
2. Verify invalidation handlers are called
3. Force refresh temporarily:
```bash
curl "http://localhost:8000/api/v1/admin/jobs/status?force_refresh=true"
```

## Future Enhancements

### 1. Real-time Notifications (Redis Pub/Sub)

Replace polling with pub/sub:

```python
# Subscribe to notification channel
async def notification_listener():
    pubsub = redis.pubsub()
    await pubsub.subscribe("notifications:user:123")
    
    async for message in pubsub.listen():
        # Push to frontend via WebSocket
        await websocket.send_json(message)
```

### 2. Distributed Locks

For coordinating operations across multiple servers:

```python
from redis.lock import Lock

async with Lock(redis, "ingestion:file:123", timeout=300):
    # Only one worker processes this file
    await ingest_file(file_id)
```

### 3. Cache Analytics

Track cache hit rates:

```python
@router.get("/admin/cache/stats")
async def get_cache_stats():
    return {
        "hit_rate": cache.get_hit_rate(),
        "miss_rate": cache.get_miss_rate(),
        "size": cache.get_size()
    }
```
