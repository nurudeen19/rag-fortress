"""
Admin routes for job queue management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_session_factory
from app.core.startup import get_startup_controller
from app.core.security import get_current_user
from app.models.job import Job, JobStatus
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/api/v1/admin/jobs", tags=["admin:jobs"])


@router.get("/status")
async def get_job_status(current_user = Depends(get_current_user)):
    """
    Get job queue statistics.
    
    Returns counts of jobs by status.
    """
    # TODO: Add admin role check
    
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        stats = {}
        for status in JobStatus:
            result = await session.execute(
                select(func.count(Job.id)).where(Job.status == status)
            )
            stats[status.value] = result.scalar()
        
        result = await session.execute(select(func.count(Job.id)))
        stats["total"] = result.scalar()
    
    return {
        "status": "ok",
        "data": stats
    }


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
