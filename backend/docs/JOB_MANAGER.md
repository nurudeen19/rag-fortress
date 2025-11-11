# Job Manager - Background Task Scheduling

Simple, lightweight background job scheduling using APScheduler.

## Overview

The `JobManager` handles asynchronous task execution without blocking the main application thread. Perfect for:
- Document ingestion processing
- Email sending
- Report generation
- Any long-running task that shouldn't block HTTP responses

## Architecture

**Why APScheduler?**
- ✅ Lightweight (no external dependencies like Redis needed)
- ✅ In-process scheduling (BackgroundScheduler runs in application thread pool)
- ✅ Thread-based execution (ideal for I/O-bound tasks)
- ✅ Call on-the-fly (schedule jobs dynamically)
- ✅ Singleton pattern (one scheduler per application)

**Design Principles**
- Modular (follows same pattern as loader, chunker, storage)
- Simple API (3 main methods for 3 job types)
- Thread-safe (APScheduler handles concurrency)
- Scalable (easy to extend with new job types)

## Usage

### 1. Immediate Execution (Fire-and-Forget)

```python
from app.services.jobs import get_job_manager

job_manager = get_job_manager()
job_manager.start()

# Execute immediately in background
job_id = job_manager.add_immediate_job(
    process_pending_documents,
    job_id="ingest_1"
)
```

### 2. Scheduled Execution (Run at Specific Time)

```python
from datetime import datetime, timezone, timedelta

# Schedule for 5 minutes from now
run_at = datetime.now(timezone.utc) + timedelta(minutes=5)

job_id = job_manager.add_scheduled_job(
    send_email,
    run_at=run_at,
    "user@example.com",
    job_id="email_scheduled"
)
```

### 3. Recurring Execution (Run at Regular Intervals)

```python
# Run every 30 minutes
job_id = job_manager.add_recurring_job(
    process_pending_documents,
    interval_seconds=1800,  # 30 minutes
    job_id="recurring_ingest"
)
```

## API Reference

### JobManager Methods

#### `start()`
Start the scheduler. Must be called before adding jobs.

#### `add_immediate_job(func, *args, job_id=None, **kwargs)`
Execute a function immediately in background.

**Returns:** Job ID (string)

#### `add_scheduled_job(func, run_at, *args, job_id=None, **kwargs)`
Schedule function to run at specific time.

**Args:**
- `func`: Callable to execute
- `run_at`: datetime (must be timezone-aware)
- `*args`: Positional arguments
- `**kwargs`: Keyword arguments

**Returns:** Job ID (string)

#### `add_recurring_job(func, interval_seconds, *args, job_id=None, max_instances=1, **kwargs)`
Schedule function to run at regular intervals.

**Args:**
- `func`: Callable to execute
- `interval_seconds`: Seconds between executions
- `max_instances`: Max concurrent runs (default: 1)

**Returns:** Job ID (string)

#### `remove_job(job_id)`
Remove a scheduled job.

**Returns:** True if removed, False if not found

#### `get_job(job_id)`
Get job details (next_run_time, trigger, etc).

**Returns:** Dict or None

#### `get_jobs()`
List all scheduled jobs.

**Returns:** List of job info dicts

#### `pause_job(job_id)`
Pause a job (don't remove, just pause execution).

#### `resume_job(job_id)`
Resume a paused job.

#### `shutdown(wait=True)`
Gracefully shutdown scheduler. Wait for running jobs by default.

## Integration Examples

### FastAPI Route

```python
from fastapi import FastAPI
from app.services.jobs import get_job_manager

app = FastAPI()
job_manager = get_job_manager()
job_manager.start()

@app.post("/ingest")
async def trigger_ingestion():
    """Trigger ingestion without blocking response."""
    job_id = job_manager.add_immediate_job(
        process_pending_documents,
        job_id=f"ingest_{datetime.now().timestamp()}"
    )
    return {
        "message": "Ingestion started",
        "job_id": job_id,
        "status": "processing"
    }

@app.get("/jobs")
async def list_jobs():
    """List all scheduled jobs."""
    return job_manager.get_jobs()
```

### With Document Ingestion

```python
async def process_documents():
    """Background job for document ingestion."""
    from app.core.database import get_async_session
    from app.services.vector_store.storage import DocumentStorageService
    
    session = get_async_session()
    storage = DocumentStorageService(session)
    
    result = await storage.ingest_pending_files()
    logger.info(f"Ingested {result['chunks_generated']} chunks")


# In your route or service
job_manager = get_job_manager()
job_id = job_manager.add_immediate_job(process_documents)
```

### With Email Sending

```python
def send_bulk_emails():
    """Background job for sending emails."""
    from app.services.email import EmailService
    
    email_service = EmailService()
    # Send emails...


# Schedule hourly email job
job_manager.add_recurring_job(
    send_bulk_emails,
    interval_seconds=3600,  # Every hour
    job_id="hourly_emails"
)
```

## Application Initialization

Add to your application startup (e.g., in `main.py`):

```python
from contextlib import asynccontextmanager
from app.services.jobs import get_job_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    job_manager = get_job_manager()
    job_manager.start()
    logger.info("Job scheduler started")
    
    yield
    
    # Shutdown
    job_manager.shutdown(wait=True)
    logger.info("Job scheduler shutdown")

app = FastAPI(lifespan=lifespan)
```

## Key Features

✅ **Singleton Pattern**
- Only one scheduler instance across entire application
- Safe for concurrent access

✅ **Job ID Management**
- Each job has unique ID for tracking/management
- Can remove/pause/resume by ID

✅ **Thread-Safe**
- Built-in thread pool management
- max_instances prevents concurrent duplicates

✅ **Timezone Aware**
- All scheduling uses UTC by default
- Timezone conversion handled automatically

✅ **Error Handling**
- Failed jobs are logged
- Job removal/pause failures are gracefully handled

## Performance Characteristics

| Job Type | Execution | Use Case |
|----------|-----------|----------|
| Immediate | Now (async) | Fire-and-forget tasks |
| Scheduled | Specific time | One-time future tasks |
| Recurring | Fixed interval | Periodic background jobs |

## Logging

All operations are logged via app logger:

```python
# Enable debug logging for APScheduler
import logging
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
```

## File Structure

```
app/services/jobs/
├── __init__.py           # Exports JobManager and get_job_manager
└── job_manager.py        # Main JobManager class

examples/
└── job_manager_examples.py  # Usage examples
```

## Next Steps / Future Enhancements

- [ ] Persistent job store (SQLAlchemy JobStore)
- [ ] Job retry policies
- [ ] Job result tracking/storage
- [ ] WebSocket updates on job completion
- [ ] Admin dashboard for job monitoring

---

**Status:** ✅ Production Ready
