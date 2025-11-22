"""
Admin routes for job queue management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.core.database import get_async_session_factory, get_session
from app.core.startup import get_startup_controller
from app.core.security import get_current_user, require_role
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.common import MessageResponse
from app.core.cache import get_cache
from app.config.cache_settings import cache_settings

router = APIRouter(prefix="/api/v1/admin/jobs", tags=["admin:jobs"])


@router.get("/status")
async def get_job_status(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get job queue statistics. Cached for 1 minute after first access.
    
    Returns counts of jobs by status.
    """
    # TODO: Add admin role check
    
    
    
    cache = get_cache()
    cache_key = "stats:jobs"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return {"status": "ok", "data": cached}
    
    # Fetch from database
    stats = {}
    for status in JobStatus:
        result = await session.execute(
            select(func.count(Job.id)).where(Job.status == status)
        )
        stats[status.value] = result.scalar() or 0
    
    result = await session.execute(select(func.count(Job.id)))
    stats["total"] = result.scalar() or 0
    
    # Cache for 1 minute
    await cache.set(cache_key, stats, ttl=cache_settings.CACHE_TTL_STATS)
    
    return {
        "status": "ok",
        "data": stats
    }


@router.get("/{job_id}")
async def get_job_detail(
    job_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Get details for a specific job including status and result.
    
    Returns:
    - job_id: Database job ID
    - job_type: Type of job (FILE_INGESTION, etc)
    - status: Current job status (PENDING, PROCESSING, COMPLETED, FAILED)
    - reference_id: ID of entity being processed (file_id, etc)
    - reference_type: Type of entity (file_upload, etc)
    - created_at: Job creation timestamp
    - started_at: When job execution started (null if not started)
    - completed_at: When job execution completed (null if not completed)
    - retry_count: Number of retries so far
    - max_retries: Maximum allowed retries
    - error: Error message if job failed
    - result: Result data if job completed successfully (JSON)
    """
    try:
        job = await session.get(Job, job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        # Parse result JSON if present
        result_data = None
        if job.result:
            try:
                result_data = json.loads(job.result)
            except:
                result_data = job.result
        
        return {
            "status": "ok",
            "data": {
                "job_id": job.id,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "reference_id": job.reference_id,
                "reference_type": job.reference_type,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "error": job.error,
                "result": result_data
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job: {str(e)}"
        )


@router.post("/retry-pending")
async def retry_pending_jobs(current_user = Depends(get_current_user)):
    """
    Manually trigger retry of all pending jobs.
    
    This reschedules all PENDING jobs to run immediately.
    Useful for manual recovery after infrastructure issues.
    """
    # TODO: Add admin role check
    
    try:
        startup_controller = get_startup_controller()
        
        if startup_controller.job_integration is None:
            raise HTTPException(
                status_code=503,
                detail="Job queue not initialized"
            )
        
        # Recover and schedule pending jobs
        count = await startup_controller.job_integration.recover_and_schedule_pending()
        
        return MessageResponse(
            status="ok",
            message=f"Scheduled {count} pending jobs for processing"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry pending jobs: {str(e)}"
        )


@router.delete("/failed")
async def clear_failed_jobs(current_user = Depends(get_current_user)):
    """
    Delete all failed jobs from the queue.
    
    This removes jobs that have exceeded max retries.
    Use with caution as this action cannot be undone.
    """
    # TODO: Add admin role check
    
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            # Get count before delete
            result = await session.execute(
                select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
            )
            count = result.scalar()
            
            # Delete failed jobs
            await session.execute(
                select(Job).where(Job.status == JobStatus.FAILED).delete()
            )
            await session.commit()
            
            return MessageResponse(
                status="ok",
                message=f"Deleted {count} failed jobs"
            )
        
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear jobs: {str(e)}"
            )
