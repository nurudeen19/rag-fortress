# Rate Limiting Guide

## Overview

RAG Fortress implements configurable rate limiting to protect the application from abuse and ensure fair resource usage. Rate limiting is applied at two levels:

1. **General Application-Wide Rate Limiting** - Applies to all endpoints
2. **Conversation-Specific Rate Limiting** - Stricter limits for RAG pipeline endpoints

## Architecture

### Components

- **SlowAPI** - FastAPI-compatible rate limiting library
- **Storage Backend** - In-memory (default) or Redis for distributed systems
- **Rate Limiter Utility** (`app/utils/rate_limiter.py`) - Centralized configuration
- **Configuration** (`app/config/app_settings.py`) - Environment-based settings

### Rate Limit Keys

Rate limits are tracked per:
- **Authenticated Users** - By user ID (`user:123`)
- **Anonymous Users** - By IP address

This ensures accurate tracking for logged-in users and prevents IP-based evasion.

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# General rate limits (all endpoints)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Conversation endpoint limits (RAG pipeline)
CONVERSATION_RATE_LIMIT_PER_MINUTE=10
CONVERSATION_RATE_LIMIT_PER_HOUR=100

# Storage backend: "memory" or "redis"
RATE_LIMIT_STORAGE=memory

# Redis URL (only needed if RATE_LIMIT_STORAGE=redis)
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
```

### Default Values

| Setting | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `60` | General limit per minute |
| `RATE_LIMIT_PER_HOUR` | `1000` | General limit per hour |
| `CONVERSATION_RATE_LIMIT_PER_MINUTE` | `10` | Conversation limit per minute |
| `CONVERSATION_RATE_LIMIT_PER_HOUR` | `100` | Conversation limit per hour |
| `RATE_LIMIT_STORAGE` | `memory` | Storage backend |

### Storage Backends

#### In-Memory Storage (Default)

- **Pros**: Simple, no dependencies, fast
- **Cons**: Not suitable for multi-instance deployments (each instance has separate limits)
- **Use Case**: Single-server deployments, development, testing

```env
RATE_LIMIT_STORAGE=memory
```

#### Redis Storage

- **Pros**: Distributed, shared across instances, persistent
- **Cons**: Requires Redis server
- **Use Case**: Production with multiple application instances, load-balanced setups

```env
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
```

## Rate Limiting Levels

### 1. General Application-Wide Limits

Applied to all endpoints by default:
- **60 requests/minute** (1 per second average)
- **1000 requests/hour**

This prevents general API abuse while allowing normal usage patterns.

### 2. Conversation Endpoint Limits

Stricter limits for RAG pipeline endpoints (`/api/v1/conversations/{id}/respond`):
- **10 requests/minute** (RAG operations are expensive)
- **100 requests/hour**

These protect the computationally intensive RAG pipeline from abuse.

## Response Format

When rate limit is exceeded, the API returns:

```json
{
  "success": false,
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "detail": "10 per 1 minute"
}
```

**HTTP Status Code**: `429 Too Many Requests`

## Implementation Details

### Rate Limiter Initialization

The rate limiter is initialized in `app/main.py`:

```python
from app.utils.rate_limiter import get_limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# In create_app()
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

### Applying Rate Limits to Endpoints

#### Decorator Pattern

```python
from app.utils.rate_limiter import get_limiter, get_conversation_rate_limit

limiter = get_limiter()

@router.post("/{conversation_id}/respond")
@limiter.limit(get_conversation_rate_limit())
async def stream_conversation_response(
    http_request: Request,  # Required for rate limiter
    conversation_id: str,
    request: ConversationGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Endpoint logic
    pass
```

**Important**: The endpoint must accept a `Request` parameter for the rate limiter to work.

## Monitoring

### Logging

Rate limit events are logged:

```
WARNING - Rate limit exceeded for user:123 on /api/v1/conversations/abc123/respond
```

### Metrics to Track

1. **Rate Limit Hits** - How often users hit limits
2. **User Patterns** - Which users frequently hit limits
3. **Endpoint Distribution** - Which endpoints are rate-limited most
4. **Time Patterns** - Peak usage times

### Activity Logs

Rate limit violations can be logged to the activity log system for analysis:

```python
await activity_logger_service.log_activity(
    db=session,
    user_id=user_id,
    incident_type="rate_limit_exceeded",
    severity="warning",
    description=f"Rate limit exceeded on {endpoint}",
    details={"endpoint": endpoint, "limit": limit}
)
```

## Testing

### Manual Testing

#### Test General Rate Limit

```bash
# Send 65 requests in rapid succession (exceeds 60/minute limit)
for i in {1..65}; do
  curl -X GET http://localhost:8000/api/v1/conversations \
    -H "Authorization: Bearer YOUR_TOKEN"
done
```

Expected: First 60 succeed, remaining 5 return 429.

#### Test Conversation Rate Limit

```bash
# Send 12 requests to conversation endpoint
for i in {1..12}; do
  curl -X POST http://localhost:8000/api/v1/conversations/abc123/respond \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Test query"}'
done
```

Expected: First 10 succeed, remaining 2 return 429.

### Automated Testing

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_conversation_rate_limit():
    """Test conversation endpoint rate limiting."""
    async with httpx.AsyncClient() as client:
        # Send 11 requests (limit is 10/minute)
        responses = []
        for i in range(11):
            response = await client.post(
                "http://localhost:8000/api/v1/conversations/test/respond",
                json={"message": "test"},
                headers={"Authorization": f"Bearer {token}"}
            )
            responses.append(response)
        
        # First 10 should succeed
        assert all(r.status_code in [200, 201] for r in responses[:10])
        
        # 11th should be rate limited
        assert responses[10].status_code == 429
        assert "rate_limit_exceeded" in responses[10].json()["error"]
```

## Tuning Guidelines

### Adjust Limits Based On

1. **User Feedback** - If legitimate users hit limits, increase them
2. **Server Capacity** - Higher capacity = higher limits
3. **Abuse Patterns** - Frequent attacks = stricter limits
4. **Business Requirements** - Premium users might need higher limits

### Recommended Limits by Environment

#### Development
```env
RATE_LIMIT_PER_MINUTE=120
CONVERSATION_RATE_LIMIT_PER_MINUTE=20
```

#### Staging
```env
RATE_LIMIT_PER_MINUTE=60
CONVERSATION_RATE_LIMIT_PER_MINUTE=10
```

#### Production (Single Instance)
```env
RATE_LIMIT_PER_MINUTE=60
CONVERSATION_RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_STORAGE=memory
```

#### Production (Multi-Instance)
```env
RATE_LIMIT_PER_MINUTE=60
CONVERSATION_RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_REDIS_URL=redis://redis-server:6379/0
```

## Per-User Rate Limits

For implementing per-user or tier-based limits:

```python
from app.utils.rate_limiter import get_limiter

limiter = get_limiter()

def get_user_rate_limit(user: User) -> str:
    """Get rate limit based on user tier."""
    if user.is_premium:
        return "100/minute;5000/hour"
    elif user.is_standard:
        return "50/minute;2000/hour"
    else:
        return "20/minute;500/hour"

@router.post("/endpoint")
@limiter.limit(lambda: get_user_rate_limit(current_user))
async def endpoint(
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    pass
```

## Disabling Rate Limiting

### For Development

```env
RATE_LIMIT_ENABLED=false
```

### For Specific Tests

```python
import pytest
from app.config.settings import get_settings

@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for tests."""
    settings = get_settings()
    original = settings.app.RATE_LIMIT_ENABLED
    settings.app.RATE_LIMIT_ENABLED = False
    yield
    settings.app.RATE_LIMIT_ENABLED = original
```

## Troubleshooting

### Problem: Users Hit Limits Too Quickly

**Solution**: Increase limits or implement user tiers

```env
RATE_LIMIT_PER_MINUTE=120  # Increase from 60
CONVERSATION_RATE_LIMIT_PER_MINUTE=20  # Increase from 10
```

### Problem: Rate Limits Not Working in Multi-Instance Setup

**Solution**: Switch to Redis storage

```env
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_REDIS_URL=redis://redis-server:6379/0
```

### Problem: Redis Connection Errors

**Check**:
1. Redis server is running
2. Redis URL is correct
3. Network connectivity to Redis

**Fallback**: Switch to memory storage temporarily

### Problem: Import Errors for SlowAPI

**Solution**: Ensure slowapi is installed

```bash
pip install slowapi
```

## Best Practices

1. **Start Conservative** - Begin with strict limits, loosen based on usage
2. **Monitor Actively** - Track rate limit violations and adjust
3. **Communicate Limits** - Document limits in API documentation
4. **Provide Feedback** - Return clear error messages with retry information
5. **Use Redis in Production** - For multi-instance deployments
6. **Implement Tiers** - Different limits for different user types
7. **Log Violations** - Track patterns for security analysis
8. **Test Thoroughly** - Verify limits work as expected
9. **Consider Geography** - Higher limits for specific regions if needed
10. **Review Regularly** - Adjust limits based on usage patterns

## Future Enhancements

1. **Dynamic Rate Limiting** - Adjust based on server load
2. **User Tier Integration** - Premium users get higher limits
3. **Endpoint-Specific Limits** - Fine-grained control per endpoint
4. **Burst Allowance** - Allow short bursts above limit
5. **Rate Limit Dashboard** - Visual monitoring of limits
6. **Auto-Scaling Integration** - Increase limits when scaling up
7. **Geographic Limits** - Different limits per region
8. **API Key Rate Limits** - Per API key tracking
9. **Whitelist/Blacklist** - Bypass or extra restrict specific users
10. **Custom Error Pages** - Better UX for rate limit errors

## Related Documentation

- [Exception Handling Guide](./EXCEPTION_HANDLING_GUIDE.md)
- [Logging Guide](./LOGGING_GUIDE.md)

## API Reference

### Functions

#### `get_limiter()`
Get or create rate limiter instance.

**Returns**: `Limiter` instance

#### `get_rate_limit_key(request: Request)`
Get rate limit key (user ID or IP).

**Args**:
- `request`: FastAPI Request object

**Returns**: Rate limit key string

#### `get_general_rate_limit()`
Get general rate limit string.

**Returns**: Rate limit string (e.g., "60/minute;1000/hour")

#### `get_conversation_rate_limit()`
Get conversation rate limit string.

**Returns**: Rate limit string (e.g., "10/minute;100/hour")

#### `rate_limit_exceeded_handler(request, exc)`
Handle rate limit exceeded errors.

**Args**:
- `request`: FastAPI Request
- `exc`: RateLimitExceeded exception

**Returns**: JSONResponse with error details
