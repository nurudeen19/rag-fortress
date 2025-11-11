# Job Queue System

Simple job management system for tracking async tasks and enabling recovery after app restarts.

## Overview

The job system provides:
- Persistent job storage in database
- Status tracking (PENDING, PROCESSING, COMPLETED, FAILED)
- Retry mechanism with configurable max retries
- Reference tracking (links jobs to source entities like file uploads)
- Recovery on app restart (unprocessed jobs remain in queue)

## Database Structure

### Table: `jobs`

Minimal fields for straightforward job management:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | INT | Unique job identifier |
| `job_type` | VARCHAR | Job category (file_ingestion, embedding_generation, etc) |
| `status` | VARCHAR | Current state (pending, processing, completed, failed) |
| `reference_id` | INT | ID of source entity (e.g., file_upload ID) |
| `reference_type` | VARCHAR | Type of source (e.g., "file_upload") |
| `payload` | TEXT | JSON payload with job parameters |
| `result` | TEXT | JSON result after completion |
| `error` | TEXT | Error message if failed or retrying |
| `retry_count` | INT | Current retry attempt (0 = first attempt) |
| `max_retries` | INT | Maximum retries allowed (default: 3) |
| `created_at` | DATETIME | Job creation time |
| `updated_at` | DATETIME | Last update time |

### Indexes

- `ix_jobs_job_type` - Find jobs by type
- `ix_jobs_status` - Find jobs by status
- `ix_jobs_reference_id` - Find jobs by reference
- `ix_jobs_reference_type` - Find jobs by reference type
- `ix_jobs_status_type` - Find pending jobs of specific type
- `ix_jobs_reference` - Find job for specific entity

## Job Lifecycle

```
User uploads file
    ↓
create_job(reference_id=file.id, reference_type="file_upload")
    ↓
Job status = PENDING
    ↓
App loads pending jobs on startup
    ↓
process_job(job_id)
    ↓
Job status = PROCESSING
    ↓
If success: mark_completed(job_id, result={...})
If fails:   mark_failed(job_id, error="...", retry=True)
    ↓
If retryable: Job status = PENDING (will retry)
If final failure: Job status = FAILED
    ↓
Completed jobs can be cleaned up after N days
```

## Enums

### JobStatus
- `PENDING` - Waiting to be processed
- `PROCESSING` - Currently being processed
- `COMPLETED` - Successfully completed
- `FAILED` - Failed (max retries exceeded)

### JobType
- `FILE_INGESTION` - Process uploaded file
- `EMBEDDING_GENERATION` - Generate embeddings
- `VECTOR_STORAGE` - Store vectors
- `CLEANUP` - Cleanup tasks

## Usage Examples

### Create a Job

```python
from app.services.job_service import JobService
from app.models.job import JobType

service = JobService(session)

job = await service.create(
    job_type=JobType.FILE_INGESTION,
    reference_id=file_id,
    reference_type="file_upload",
    payload={"file_path": "/path/to/file.pdf"},
    max_retries=3
)
```

### Get Pending Jobs

```python
# Get all pending jobs
pending_jobs = await service.get_pending()

# Get pending jobs of specific type
pending_file_jobs = await service.get_pending(job_type=JobType.FILE_INGESTION)
```

### Process a Job

```python
try:
    # Mark as processing
    job = await service.mark_processing(job_id)
    
    # Do work here
    result = await process_file(job.payload)
    
    # Mark completed
    await service.mark_completed(job_id, result=result)
except Exception as e:
    # Mark failed (will retry if under max_retries)
    await service.mark_failed(job_id, str(e), retry=True)
    await session.commit()
```

### Get Job by Reference

```python
# Find job for specific file upload
job = await service.get_by_reference("file_upload", file_id)
```

### Cleanup Old Completed Jobs

```python
# Delete completed jobs older than 7 days
count = await service.cleanup_completed(days=7)
```

## Migration

Run migration to create the jobs table:

```bash
alembic upgrade head
```

Downgrade:

```bash
alembic downgrade -1
```

## Recovery on App Restart

The job system survives app restarts automatically:

1. All PENDING jobs remain in the queue
2. PROCESSING jobs are reset to PENDING (will be retried)
3. App startup routine can query pending jobs and resume processing
4. Retry counter ensures we don't retry forever

## Recovery Handler Example

```python
async def recover_pending_jobs():
    """Resume processing of pending jobs after app restart."""
    service = JobService(session)
    pending_jobs = await service.get_pending()
    
    for job in pending_jobs:
        # Resume processing
        await process_job(job)
```
