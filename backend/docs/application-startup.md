# Application Startup System

## Overview

The **StartupController** manages initialization of critical components when the RAG Fortress application starts. This ensures all required services are ready before handling requests.

## Architecture

```
Server Start → FastAPI Lifespan → StartupController.initialize()
                                          ↓
                                  1. Initialize Embeddings
                                  2. Warm up services
                                  3. Test connectivity
                                          ↓
                                  Application Ready ✓
```

## Components

### 1. StartupController (`app/core/startup.py`)

Central controller that orchestrates initialization:

```python
from app.core.startup import get_startup_controller

# Get the global instance
startup_controller = get_startup_controller()

# Initialize all services
await startup_controller.initialize()

# Check if ready
if startup_controller.is_ready():
    print("Application ready!")
```

**Responsibilities:**
- Initialize embedding provider
- Warm up services with test requests
- Validate configurations
- Future: Initialize vector store, database connections, caches, etc.

### 2. FastAPI Lifespan (`app/main.py`)

Uses FastAPI's modern `lifespan` context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    startup_controller = get_startup_controller()
    await startup_controller.initialize()
    
    yield
    
    # Shutdown
    await startup_controller.shutdown()
```

### 3. Health Check Endpoint

```http
GET /health
```

Returns application readiness status:

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

Status values:
- `healthy` - All services initialized and ready
- `starting` - Still initializing

## Running the Application

### Development Mode

```bash
# From backend directory
python run.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Features:
- Auto-reload on code changes
- Detailed logging
- Single worker process

### Production Mode

```bash
# From backend directory
python run_production.py

# Or with uvicorn directly
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

Features:
- Multiple worker processes (4 by default)
- No auto-reload
- Optimized for performance

## Startup Sequence

### 1. Server Initialization
```
Server starts → Load settings → Create FastAPI app
```

### 2. Lifespan Startup
```
Enter lifespan context → StartupController.initialize()
```

### 3. Component Initialization

**Current:**
1. **Embedding Provider**
   - Load embedding model
   - Test with sample text
   - Verify embedding dimension
   - Log initialization status

**Future (to be added):**
2. **Vector Store**
   - Connect to vector database
   - Verify connection
   - Initialize connection pool

3. **Database**
   - Connect to PostgreSQL/SQLite
   - Run migrations
   - Initialize connection pool

4. **Cache**
   - Initialize Redis cache
   - Warm up common queries

5. **Background Jobs**
   - Start job queue workers
   - Initialize task scheduler

### 4. Ready to Serve

```
Initialization complete → Server ready → Start accepting requests
```

## Startup Logs

Successful startup:

```
2025-11-03 10:00:00 - app.core.startup - INFO - Starting application initialization...
2025-11-03 10:00:00 - app.core.startup - INFO - Initializing embedding provider...
2025-11-03 10:00:01 - app.core.startup - INFO - ✓ Embedding provider initialized (dimension: 384)
2025-11-03 10:00:01 - app.core.startup - INFO - ✓ Application initialization completed successfully
2025-11-03 10:00:01 - app.main - INFO - Application is ready to handle requests
```

Failed startup:

```
2025-11-03 10:00:00 - app.core.startup - INFO - Starting application initialization...
2025-11-03 10:00:00 - app.core.startup - INFO - Initializing embedding provider...
2025-11-03 10:00:01 - app.core.startup - ERROR - Failed to initialize embedding provider: Model not found
2025-11-03 10:00:01 - app.core.startup - ERROR - ✗ Application initialization failed
```

## Adding New Services

To add a new service to startup:

1. **Add initialization method to StartupController:**

```python
# app/core/startup.py

async def _initialize_vector_store(self):
    """Initialize vector store connection."""
    logger.info("Initializing vector store...")
    
    try:
        from app.services.vector_store.factory import get_vector_store
        
        self.vector_store = get_vector_store()
        await self.vector_store.connect()
        
        # Test connection
        health = await self.vector_store.health_check()
        if health:
            logger.info("✓ Vector store initialized")
        else:
            raise RuntimeError("Vector store health check failed")
    
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise
```

2. **Call it in initialize() method:**

```python
async def initialize(self):
    """Initialize all critical components."""
    # ... existing code ...
    
    # Initialize embedding provider
    await self._initialize_embeddings()
    
    # Add new service initialization
    await self._initialize_vector_store()
    
    # ... rest of code ...
```

3. **Add cleanup in shutdown() method:**

```python
async def shutdown(self):
    """Cleanup resources on shutdown."""
    # ... existing code ...
    
    # Close vector store connection
    if hasattr(self, 'vector_store') and self.vector_store:
        await self.vector_store.disconnect()
        logger.info("✓ Vector store connection closed")
    
    # ... rest of code ...
```

## Configuration

Startup behavior can be configured via environment variables:

```env
# .env file

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/rag_fortress.log

# Server
HOST=0.0.0.0
PORT=8000

# Environment
ENVIRONMENT=development  # or production
```

## Error Handling

If startup fails:
1. Exception is logged with full traceback
2. Application exits (no partial initialization)
3. Client receives 503 Service Unavailable until ready

## Testing Startup

```bash
# Test that server starts successfully
curl http://localhost:8000/health

# Expected response
{"status": "healthy", "version": "1.0.0"}
```

## Best Practices

✅ **Do:**
- Initialize expensive resources once at startup
- Test connections during initialization
- Log each initialization step
- Fail fast if critical service unavailable
- Clean up resources on shutdown

❌ **Don't:**
- Initialize on first request (causes delays)
- Ignore initialization failures
- Keep retrying indefinitely
- Initialize non-critical services at startup

## Future Enhancements

Planned additions:

1. **Graceful Degradation**
   - Mark services as optional vs required
   - Continue with reduced functionality if optional service fails

2. **Health Metrics**
   - Expose detailed health checks per service
   - Prometheus metrics

3. **Startup Timeout**
   - Maximum time allowed for initialization
   - Fail if timeout exceeded

4. **Readiness Probes**
   - Kubernetes-compatible readiness endpoint
   - Liveness checks

## Related Documentation

- [Background Ingestion](./background-ingestion.md)
- [Configuration Guide](../README.md)
