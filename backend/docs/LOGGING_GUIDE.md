# Logging Guide

## Overview

RAG Fortress uses a comprehensive logging system with colored console output for development and structured JSON logs for production.

## Features

✅ **Colored Console Output** - Easy-to-read logs in development  
✅ **Rotating File Logs** - Automatic log rotation (10MB per file, 5 backups)  
✅ **Structured JSON Logs** - Easy to parse and analyze  
✅ **Environment-Aware** - Different formats for dev/prod  
✅ **Module-Specific Loggers** - Track which module generated each log  
✅ **Third-Party Logger Control** - Suppresses noisy library logs  

## Quick Start

### Basic Usage

```python
from app.core import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### With Exception Tracebacks

```python
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
```

## Configuration

Logging is configured via environment variables in `.env`:

```bash
# Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log File Path
LOG_FILE=logs/app.log

# Environment (affects log format)
ENVIRONMENT=development  # or production
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info | Variable values, function calls |
| **INFO** | General informational messages | Request received, operation completed |
| **WARNING** | Something unexpected but handled | Deprecated function used, config missing |
| **ERROR** | Error occurred but app continues | API call failed, database error |
| **CRITICAL** | Serious error, app may crash | Out of memory, critical service down |

## Output Formats

### Development (Console)

Colored output with detailed information:
```
12:34:56 - RAG Fortress - INFO - process_query:45 - Processing user query
12:34:57 - RAG Fortress - DEBUG - _embed_text:102 - Generated embeddings: shape=(1, 384)
```

Colors:
- 🔵 DEBUG - Cyan
- 🟢 INFO - Green
- 🟡 WARNING - Yellow
- 🔴 ERROR - Red
- 🟣 CRITICAL - Magenta

### Production (Console)

Simple format without colors:
```
2025-11-01 12:34:56 - RAG Fortress - INFO - Processing user query
```

### File Logs (JSON)

Structured JSON for easy parsing:
```json
{"time": "2025-11-01 12:34:56", "name": "RAG Fortress.services.rag", "level": "INFO", "function": "process_query", "line": 45, "message": "Processing user query"}
```

## Common Patterns

### 1. Service Class

```python
from app.core import get_logger

class DocumentService:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def upload_document(self, file_path: str):
        self.logger.info(f"Uploading document: {file_path}")
        
        try:
            # Upload logic
            self.logger.debug(f"Document size: {size} bytes")
            self.logger.info("Document uploaded successfully")
        except Exception as e:
            self.logger.error(f"Upload failed: {e}", exc_info=True)
            raise
```

### 2. FastAPI Endpoint

```python
from fastapi import APIRouter
from app.core import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/chat")
async def chat(query: str):
    logger.info(f"Chat request received: {query[:50]}...")
    
    try:
        response = await process_chat(query)
        logger.info("Chat response generated")
        return response
    except Exception as e:
        logger.error("Chat processing failed", exc_info=True)
        raise
```

### 3. Background Task

```python
from app.core import get_logger
import time

logger = get_logger(__name__)

def process_embeddings_batch(documents):
    start_time = time.time()
    logger.info(f"Processing {len(documents)} documents")
    
    for i, doc in enumerate(documents):
        logger.debug(f"Processing document {i+1}/{len(documents)}")
        # Process document
    
    duration = time.time() - start_time
    logger.info(f"Batch completed in {duration:.2f}s")
```

### 4. Request Tracking

```python
import uuid
from app.core import get_logger

logger = get_logger(__name__)

async def handle_request(request_data):
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{request_id}] Request started")
    
    try:
        result = await process(request_data)
        logger.info(f"[{request_id}] Request completed")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] Request failed: {e}", exc_info=True)
        raise
```

### 5. Performance Monitoring

```python
from app.core import get_logger
import time

logger = get_logger(__name__)

def timed_operation(name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            logger.debug(f"{name} started")
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"{name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"{name} failed after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

@timed_operation("RAG Query")
async def process_rag_query(query: str):
    # Process query
    pass
```

## Advanced Features

### Custom Logger Configuration

```python
from app.core import setup_logging

# Custom logger with different settings
custom_logger = setup_logging(
    name="custom_service",
    log_level="DEBUG",
    log_file="logs/custom.log"
)
```

### Conditional Debug Logging

```python
from app.config import settings
from app.core import get_logger

logger = get_logger(__name__)

if settings.DEBUG:
    logger.debug("Detailed debug info")
    logger.debug(f"Request payload: {payload}")
```

### Structured Logging Context

```python
logger.info(
    "Operation completed",
    extra={
        'user_id': user_id,
        'duration': duration,
        'status': 'success'
    }
)
```

## Log File Management

### Rotation

Logs automatically rotate when they reach 10MB:
- Current log: `logs/app.log`
- Backup logs: `logs/app.log.1`, `logs/app.log.2`, etc.
- Keeps 5 backup files (oldest is deleted)

### Viewing Logs

```bash
# Tail current log
tail -f logs/app.log

# Search logs
grep "ERROR" logs/app.log

# Parse JSON logs
cat logs/app.log | jq '.message'

# Filter by time
grep "2025-11-01 12:" logs/app.log
```

## Third-Party Loggers

The system automatically suppresses noisy logs from:
- httpx/httpcore (HTTP clients)
- urllib3 (HTTP library)
- chromadb (Vector database)
- sentence_transformers (Embeddings)
- transformers (Models)
- torch (PyTorch)

These are set to WARNING level to reduce noise.

## Best Practices

### ✅ Do

1. **Use module-specific loggers**
   ```python
   logger = get_logger(__name__)
   ```

2. **Log exceptions with tracebacks**
   ```python
   logger.error("Error occurred", exc_info=True)
   ```

3. **Include context in messages**
   ```python
   logger.info(f"Processing {count} items for user {user_id}")
   ```

4. **Use appropriate log levels**
   - DEBUG for detailed diagnostics
   - INFO for important events
   - ERROR for errors

5. **Log at boundaries**
   - API endpoint entry/exit
   - Service method start/complete
   - External API calls

### ❌ Don't

1. **Don't log sensitive data**
   ```python
   # Bad
   logger.info(f"User password: {password}")
   
   # Good
   logger.info(f"User authenticated: {user_id}")
   ```

2. **Don't log in tight loops**
   ```python
   # Bad
   for item in million_items:
       logger.debug(f"Processing {item}")
   
   # Good
   logger.info(f"Processing {len(million_items)} items")
   # ... process ...
   logger.info("Processing complete")
   ```

3. **Don't swallow exceptions silently**
   ```python
   # Bad
   try:
       risky_op()
   except:
       pass
   
   # Good
   try:
       risky_op()
   except Exception as e:
       logger.error("Operation failed", exc_info=True)
       raise
   ```

4. **Don't use print() statements**
   ```python
   # Bad
   print("Processing...")
   
   # Good
   logger.info("Processing...")
   ```

## Troubleshooting

### Logs not appearing

Check settings:
```python
from app.config import settings
print(settings.LOG_LEVEL)  # Should be DEBUG or INFO
print(settings.LOG_FILE)   # Should be valid path
```

### Too many logs

Increase log level:
```bash
# In .env
LOG_LEVEL=WARNING  # Only warnings and errors
```

### File permission errors

Ensure logs directory is writable:
```bash
chmod 755 logs/
```

### Colors not showing

Colors only work in terminal (TTY). They're automatically disabled when:
- Output redirected to file
- Running in non-interactive environment
- In production mode

## Integration Examples

### With FastAPI Middleware

```python
from fastapi import FastAPI, Request
from app.core import get_logger
import time

app = FastAPI()
logger = get_logger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {duration:.3f}s"
    )
    
    return response
```

### With Celery Tasks

```python
from celery import Task
from app.core import get_logger

class LoggedTask(Task):
    def __call__(self, *args, **kwargs):
        logger = get_logger(self.name)
        logger.info(f"Task {self.name} started")
        
        try:
            result = super().__call__(*args, **kwargs)
            logger.info(f"Task {self.name} completed")
            return result
        except Exception as e:
            logger.error(f"Task {self.name} failed", exc_info=True)
            raise
```

## Summary

The logging system provides:
- 🎨 Colored console output for development
- 📝 Structured JSON logs for production
- 🔄 Automatic log rotation
- 📊 Easy parsing and analysis
- 🔇 Third-party logger suppression
- ⚙️ Environment-aware configuration

Start logging with:
```python
from app.core import get_logger
logger = get_logger(__name__)
logger.info("Hello, logging!")
```
