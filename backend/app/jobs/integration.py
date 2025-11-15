"""
Integrated Job Queue Architecture

Combines persistent job tracking with in-process scheduling:
- JobService: Persistent storage in database (survives app restart)
- JobManager: In-process scheduler (fires jobs immediately/scheduled)

Flow:
1. Event triggers job creation → JobService.create() → saved to DB
2. App recovers pending jobs on startup → loads from DB
3. Recovered jobs + new jobs → scheduled with JobManager
4. JobManager executes → update status in JobService (mark_processing/mark_completed)
"""

import json
from typing import Optional, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.models.job import Job, JobStatus, JobType
from app.services.job_service import JobService
from app.jobs import get_job_manager
from app.core import get_logger


logger = get_logger(__name__)


class JobQueueIntegration:
    """Bridge between persistent JobService and in-process JobManager."""
    
    def __init__(self, session_factory):
        """
        Initialize integration layer.
        
        Args:
            session_factory: AsyncSession factory for database access
        """
        self.session_factory = session_factory
        self.job_manager = get_job_manager()
    
    async def create_and_schedule(
        self,
        job_type: JobType,
        reference_id: int,
        reference_type: str,
        handler: Callable,
        payload: Optional[dict] = None,
        max_retries: int = 3,
        job_id: Optional[str] = None,
    ) -> Job:
        """
        Create persistent job and immediately schedule it.
        
        Args:
            job_type: Type of job (FILE_INGESTION, etc)
            reference_id: ID of source entity (file_id, etc)
            reference_type: Type of source (file_upload, etc)
            handler: Async function to execute job
            payload: Optional job parameters
            max_retries: Max retry attempts
            job_id: Optional unique job ID
        
        Returns:
            Created Job record
        """
        # Create persistent job record
        async with self.session_factory() as session:
            job_service = JobService(session)
            job = await job_service.create(
                job_type=job_type,
                reference_id=reference_id,
                reference_type=reference_type,
                payload=payload,
                max_retries=max_retries
            )
            await session.commit()
        
        # Schedule with JobManager for immediate execution
        job_id_str = job_id or f"{job_type.value}_{reference_id}_{job.id}"
        self.job_manager.add_immediate_job(
            self._sync_job_wrapper,
            job.id,
            handler,
            job_id=job_id_str
        )
        
        logger.info(f"Created and scheduled job {job.id}: {job_type.value}")
        return job
    
    async def recover_and_schedule_pending(self) -> int:
        """
        On app startup: recover pending jobs from DB and reschedule them.
        
        Returns:
            Number of jobs recovered
        """
        async with self.session_factory() as session:
            job_service = JobService(session)
            pending_jobs = await job_service.get_pending(limit=1000)
            
            count = 0
            for job in pending_jobs:
                try:
                    # Get handler based on job type
                    handler = self._get_handler_for_job_type(job.job_type)
                    
                    # Schedule job
                    job_id_str = f"{job.job_type.value}_{job.reference_id}_{job.id}"
                    self.job_manager.add_immediate_job(
                        self._sync_job_wrapper,
                        job.id,
                        handler,
                        job_id=job_id_str
                    )
                    count += 1
                
                except Exception as e:
                    logger.error(f"Failed to schedule recovered job {job.id}: {e}")
            
            logger.info(f"Recovered and scheduled {count} pending jobs")
            return count
    
    def _sync_job_wrapper(self, job_id: int, handler: Callable) -> None:
        """
        Synchronous wrapper for async job execution.
        
        This is called by APScheduler (which expects sync functions).
        It runs the async _job_wrapper in a new event loop.
        
        Args:
            job_id: Database job ID
            handler: Async handler to execute
        """
        try:
            # Get or create event loop for this thread
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async wrapper
            loop.run_until_complete(self._job_wrapper(job_id, handler))
        
        except Exception as e:
            logger.error(f"Error in sync job wrapper for job {job_id}: {e}", exc_info=True)
    
    async def _job_wrapper(self, job_id: int, handler: Callable) -> None:
        """
        Wrapper executed by JobManager.
        Handles job status updates in database.
        
        Args:
            job_id: Database job ID
            handler: Async handler to execute
        """
        async with self.session_factory() as session:
            job_service = JobService(session)
            
            try:
                # Mark as processing
                job = await job_service.mark_processing(job_id)
                await session.commit()
                
                # Execute handler
                logger.info(f"Executing job {job_id}")
                result = await handler(job)
                
                # Mark completed
                await job_service.mark_completed(job_id, result=result)
                await session.commit()
                
                logger.info(f"Job {job_id} completed successfully")
            
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                
                # Mark failed with retry logic
                try:
                    await job_service.mark_failed(job_id, str(e), retry=True)
                    await session.commit()
                except Exception as retry_error:
                    logger.error(f"Failed to update job {job_id} status: {retry_error}")
    
    def _get_handler_for_job_type(self, job_type: JobType) -> Callable:
        """
        Get the handler function for a job type.
        
        Args:
            job_type: Type of job
        
        Returns:
            Handler coroutine
        """
        # Map job types to handlers
        handlers = {
            JobType.FILE_INGESTION: self._handle_file_ingestion,
            JobType.EMBEDDING_GENERATION: self._handle_embedding,
            JobType.VECTOR_STORAGE: self._handle_vector_storage,
            JobType.CLEANUP: self._handle_cleanup,
            JobType.PASSWORD_RESET_EMAIL: self._handle_password_reset_email,
        }
        
        handler = handlers.get(job_type)
        if not handler:
            raise ValueError(f"No handler for job type: {job_type}")
        
        return handler
    
    async def _handle_file_ingestion(self, job: Job) -> dict:
        """Handle file ingestion job."""
        # TODO: Implement actual file ingestion logic
        payload = json.loads(job.payload) if job.payload else {}
        logger.info(f"Processing file ingestion: {payload}")
        return {"status": "ingested", "file_id": job.reference_id}
    
    async def _handle_embedding(self, job: Job) -> dict:
        """Handle embedding generation job."""
        # TODO: Implement actual embedding logic
        payload = json.loads(job.payload) if job.payload else {}
        logger.info(f"Generating embeddings: {payload}")
        return {"status": "embedded", "chunk_id": job.reference_id}
    
    async def _handle_vector_storage(self, job: Job) -> dict:
        """Handle vector storage job."""
        # TODO: Implement actual vector storage logic
        payload = json.loads(job.payload) if job.payload else {}
        logger.info(f"Storing vectors: {payload}")
        return {"status": "stored", "document_id": job.reference_id}
    
    async def _handle_cleanup(self, job: Job) -> dict:
        """Handle cleanup job."""
        # TODO: Implement actual cleanup logic
        logger.info("Running cleanup")
        return {"status": "cleaned"}
    
    async def _handle_password_reset_email(self, job: Job) -> dict:
        """Handle password reset email job."""
        payload = json.loads(job.payload) if job.payload else {}
        
        try:
            from app.services.email import get_email_service
            
            email_service = get_email_service()
            
            recipient_email = payload.get("recipient_email")
            recipient_name = payload.get("recipient_name")
            reset_token = payload.get("reset_token")
            
            if not all([recipient_email, recipient_name, reset_token]):
                raise ValueError("Missing required payload fields: recipient_email, recipient_name, reset_token")
            
            success = await email_service.send_password_reset(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                reset_token=reset_token
            )
            
            if success:
                logger.info(f"Password reset email sent to {recipient_email}")
                return {"status": "sent", "recipient_email": recipient_email}
            else:
                raise Exception(f"Failed to send password reset email to {recipient_email}")
        
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}", exc_info=True)
            raise


async def get_job_integration(session_factory) -> JobQueueIntegration:
    """Create or get JobQueueIntegration instance."""
    return JobQueueIntegration(session_factory)
