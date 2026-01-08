"""Job service for managing async jobs and background processing."""

import json
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, JobType
from app.core import get_logger


logger = get_logger(__name__)


class JobService:
    """Manage async jobs for processing and recovery on restart."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        job_type: JobType,
        reference_id: int,
        reference_type: str,
        payload: Optional[dict] = None,
        max_retries: int = 3
    ) -> Job:
        """Create new job."""
        job = Job(
            job_type=job_type,
            status=JobStatus.PENDING,
            reference_id=reference_id,
            reference_type=reference_type,
            payload=json.dumps(payload) if payload else None,
            max_retries=max_retries,
            retry_count=0,
        )
        self.session.add(job)
        await self.session.flush()
        
        return job
    
    async def get(self, job_id: int) -> Optional[Job]:
        """Get job by ID."""
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def get_pending(self, job_type: Optional[JobType] = None, limit: int = 100) -> List[Job]:
        """Get pending jobs, optionally filtered by type."""
        query = select(Job).where(Job.status == JobStatus.PENDING)
        
        if job_type:
            query = query.where(Job.job_type == job_type)
        
        query = query.order_by(Job.created_at.asc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_reference(
        self,
        reference_type: str,
        reference_id: int
    ) -> Optional[Job]:
        """Get job by reference (file_upload, etc)."""
        result = await self.session.execute(
            select(Job).where(
                Job.reference_type == reference_type,
                Job.reference_id == reference_id
            )
        )
        return result.scalar_one_or_none()
    
    async def mark_processing(self, job_id: int) -> Job:
        """Mark job as processing."""
        job = await self.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = JobStatus.PROCESSING
        await self.session.flush()
        
        logger.info(f"Job {job_id} marked processing")
        return job
    
    async def mark_completed(self, job_id: int, result: Optional[dict] = None) -> Job:
        """Mark job as completed."""
        job = await self.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = JobStatus.COMPLETED
        if result:
            job.result = json.dumps(result)
        
        await self.session.flush()
        
        logger.info(f"Job {job_id} completed")
        return job
    
    async def mark_failed(self, job_id: int, error: str, retry: bool = True) -> Job:
        """Mark job as failed. If retryable, increment retry count; otherwise mark as failed."""
        job = await self.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if retry and job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = JobStatus.PENDING
            job.error = f"Retry {job.retry_count}/{job.max_retries}: {error}"
            logger.warning(f"Job {job_id} will retry ({job.retry_count}/{job.max_retries}): {error}")
        else:
            job.status = JobStatus.FAILED
            job.error = error
            logger.error(f"Job {job_id} failed (max retries reached): {error}")
        
        await self.session.flush()
        return job
    
    async def delete(self, job_id: int) -> None:
        """Delete job."""
        job = await self.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        await self.session.delete(job)
        await self.session.flush()
        
        logger.info(f"Job {job_id} deleted")
    
    async def cleanup_completed(self, days: int = 7) -> int:
        """Delete completed jobs older than specified days."""
        from datetime import datetime, timedelta, timezone
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.session.execute(
            select(Job).where(
                Job.status == JobStatus.COMPLETED,
                Job.updated_at < cutoff_date
            )
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            await self.session.delete(job)
        
        await self.session.flush()
        count = len(jobs)
        
        if count > 0:
            logger.info(f"Cleaned up {count} completed jobs")
        
        return count
