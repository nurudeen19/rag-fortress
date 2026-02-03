# Caching Guide

## Overview

RAG Fortress provides a flexible caching layer with Redis (production) and in-memory (development) backends. The cache supports TTL-based expiration, automatic invalidation, and optional encryption for sensitive data like conversation history.

**Features:**
- Cache-aside pattern with JSON serialization
- Pattern-based invalidation
- Optional at-rest encryption for conversation history
- Automatic fallback (Redis → in-memory)

## Configuration

### Basic Settings

```bash
# Backend Selection
CACHE_BACKEND=redis          # "redis" or "memory"
CACHE_ENABLED=true

# Redis Connection
CACHE_REDIS_URL=redis://localhost:6379/0
# OR
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
CACHE_REDIS_PASSWORD=         # Optional
CACHE_REDIS_SSL=false

# TTL Configuration (seconds)
CACHE_TTL_DEFAULT=300         # 5 minutes
CACHE_TTL_STATS=60            # 1 minute (stats)
CACHE_TTL_CONFIG=3600         # 1 hour (config)
CACHE_TTL_USER_DATA=300       # 5 minutes (user data)
CACHE_TTL_HISTORY=3600        # 1 hour (conversation history)
```

### Conversation History Encryption

Optionally encrypt conversation history in cache:

```bash
# Enable encryption for history (default: false)
ENABLE_CACHE_HISTORY_ENCRYPTION=false
```

**When to encrypt:**
- Healthcare/PII data
- Compliance requirements (HIPAA, GDPR, SOC 2)
- Extra security for cached conversations

**Trade-off:** ~5-10% CPU overhead vs plaintext caching

## Usage

### Direct Cache Access

```python
from app.core.cache import get_cache

cache = get_cache()

# Basic operations
await cache.set("user:123", {"name": "John"}, ttl=300)
user_data = await cache.get("user:123")
await cache.delete("user:123")
await cache.invalidate_pattern("user:*")
```

### Simple Decorator

```python
from functools import wraps
from app.core.cache import get_cache

def cached(key_builder, ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            key = key_builder(*args, **kwargs)
            val = await cache.get(key)
            if val is not None:
                return val
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator

@cached(lambda user_id: f"user:{user_id}", ttl=300)
async def get_user(user_id: int):
    return await db.query(User).filter(User.id == user_id).first()
```

### Statistics Caching

```python
from app.services.stats_cache import StatsCache

# Cached stats
stats = await StatsCache.get_job_stats(session)

# Force refresh
stats = await StatsCache.get_job_stats(session, force_refresh=True)
```

## Cache Invalidation

### Automatic (Event-based)

```python
# After data changes
await cache.invalidate_pattern("documents:list*")
await cache.delete(f"document:{123}")
await cache.invalidate_pattern("jobs:*")
```

### Manual

```python
from app.services.stats_cache import StatsCache

await StatsCache.invalidate_file_stats(user_id=123)  # User-specific
await StatsCache.invalidate_job_stats()               # All job stats
await StatsCache.invalidate_all_stats()               # Everything
```

## Recommended TTLs

| Data Type | TTL | Encryption |
|-----------|-----|------------|
| Conversation history | 1 hour | Optional |
| Stats/counts | 60s | No |
| App config | 1 hour | No |
| User profiles | 5 min | No |
| Search results | 5 min | No |

## Troubleshooting

**Cache not working?**
```bash
# Check if enabled
echo $CACHE_ENABLED

# Test connection
from app.core.cache import get_cache
cache = get_cache()
await cache.set("test", "value")
print(await cache.get("test"))  # Should print: value
```

**Redis connection issues?**
```bash
# Verify Redis is running
redis-cli ping  # Should return: PONG

# Check connection URL
echo $CACHE_REDIS_URL
```

**Stale data?**
- Check TTL settings
- Verify invalidation handlers are triggered
- Force refresh: `?force_refresh=true`
