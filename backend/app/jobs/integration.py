"""
Integrated Job Queue Architecture

Combines persistent job tracking with in-process scheduling:
- JobService: Persistent storage in database (survives app restart)
- JobManager: In-process scheduler (fires jobs immediately/scheduled)

Flow:
1. Event triggers job creation → JobService.create() → saved to DB
2. Jobs are scheduled with JobManager for immediate execution
3. JobManager executes in background threads with isolated event loops
4. Job status updates use sync database to avoid async conflicts
5. Handlers run async but manage their own database sessions
"""

import json
from typing import Optional, Callable
import asyncio

from app.models.job import Job, JobStatus, JobType
from app.services.job_service import JobService
from app.services.document_ingestion import DocumentIngestionService
from app.services.email import get_email_service
from app.jobs import get_job_manager
from app.core import get_logger
from app.core.sync_db import get_sync_session
from app.utils.log_sanitizer import sanitize_log_data


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
    
    def schedule_pending_jobs_sync(self) -> int:
        """
        Programmatically schedule all pending jobs (sync wrapper for manual triggers).
        
        This is useful for manual job recovery via API or CLI.
        
        Returns:
            Number of jobs scheduled
        """
        import asyncio
        
        # Create new event loop for this sync operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.recover_and_schedule_pending())
        finally:
            loop.close()
    
    def _sync_job_wrapper(self, job_id: int, handler: Callable) -> None:
        """
        Synchronous wrapper for async job execution.
        
        This is called by APScheduler (which expects sync functions).
        Uses asyncio.run() with proper event loop isolation.
        
        Args:
            job_id: Database job ID
            handler: Async handler to execute
        """
        logger.info(f"Starting job {job_id} with handler {handler.__name__}")
        try:
            # Run in a subprocess-like isolated context
            import concurrent.futures
            
            def _run_async():
                """Run async code in isolated event loop."""
                return asyncio.run(self._job_wrapper(job_id, handler))
            
            # Execute in thread pool to isolate from main loop
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(_run_async).result(timeout=300)  # 5 min timeout
        
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}", exc_info=True)
    
    async def _job_wrapper(self, job_id: int, handler: Callable) -> None:
        """
        Wrapper executed by JobManager in isolated event loop.
        Handles job status updates using SYNC database to avoid event loop conflicts.
        
        CRITICAL: This runs in asyncio.run() which creates a NEW event loop.
        Any async database connections from the main loop will fail here.
        Therefore, we use SYNC sessions for job status updates.
        
        Retries:
        - On failure, increments retry_count in database
        - When retry_count < max_retries, job is set back to PENDING
        - Retry is automatic next time job is scheduled/recovered
        
        Args:
            job_id: Database job ID
            handler: Async handler to execute (gets fresh async session inside)
        """
        # Use SYNC session for job status tracking (avoids event loop conflicts)
        sync_session = get_sync_session()
        job = None
        
        try:
            from sqlalchemy import select
            result = sync_session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found in database")
                return
            
            logger.info(f"Processing job {job_id}: type={job.job_type}, reference={job.reference_type}/{job.reference_id}, attempt={job.retry_count + 1}/{job.max_retries + 1}")
            
            # Mark as processing (sync update)
            job.status = JobStatus.PROCESSING
            sync_session.commit()
            
            # Execute handler (async - handler manages its own async sessions)
            logger.info(f"Executing job {job_id} handler: {handler.__name__}")
            result_data = await handler(job)
            
            # Ensure result_data is JSON-serializable
            if result_data:
                try:
                    result_data = json.loads(json.dumps(result_data, default=str))
                except Exception as serialize_err:
                    logger.warning(f"Could not serialize result: {serialize_err}, using string instead")
                    result_data = {"status": "success", "message": str(result_data)}
            
            # Mark completed (sync update)
            job.status = JobStatus.COMPLETED
            job.result = json.dumps(result_data) if result_data else None
            sync_session.commit()
            
            logger.info(f"Job {job_id} completed successfully: {result_data}")
        
        except Exception as e:
            logger.error(f"Job {job_id} failed (attempt {job.retry_count + 1 if job else 0}/{job.max_retries + 1 if job else 1}): {e}", exc_info=True)
            
            # Mark failed with retry logic
            if job:
                try:
                    if job.retry_count < job.max_retries:
                        # Retry: increment counter and set back to PENDING
                        job.retry_count += 1
                        job.status = JobStatus.PENDING
                        job.error = f"Retry {job.retry_count}/{job.max_retries}: {str(e)}"
                        logger.info(f"Job {job_id} marked for retry ({job.retry_count}/{job.max_retries})")
                    else:
                        # Max retries exceeded: mark as FAILED
                        job.status = JobStatus.FAILED
                        job.error = f"Max retries exceeded. Last error: {str(e)}"
                        logger.error(f"Job {job_id} failed permanently (max retries exceeded)")
                    
                    sync_session.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update job {job_id} status: {update_error}")
        
        finally:
            # Close sync session
            try:
                sync_session.close()
            except Exception as close_err:
                logger.warning(f"Error closing session for job {job_id}: {close_err}")
    
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
            JobType.PASSWORD_CHANGED_EMAIL: self._handle_password_changed_email,
        }
        
        handler = handlers.get(job_type)
        if not handler:
            raise ValueError(f"No handler for job type: {job_type}")
        
        return handler
    
    async def _handle_file_ingestion(self, job: Job) -> dict:
        """Handle file ingestion job - coordinate DocumentIngestionService pipeline."""
        try:
            payload = json.loads(job.payload) if job.payload else {}
            file_id = payload.get("file_id") or job.reference_id
            batch_mode = payload.get("batch_mode", False)
            triggered_by_admin_id = payload.get("triggered_by_admin_id")
            
            logger.info(f"Starting file ingestion job: file_id={file_id}, batch_mode={batch_mode}")
            
            # Create ingestion service (it manages its own sessions)
            ingestion_service = DocumentIngestionService()
            
            if batch_mode:
                # Process all approved files
                result = await ingestion_service.ingest_batch()
                
                # Create completion notification for admin if triggered by admin
                # Note: This is now a sync call (uses sync session to avoid event loop conflicts)
                if triggered_by_admin_id:
                    self._create_batch_completion_notification(
                        admin_id=triggered_by_admin_id,
                        job_id=job.id,
                        result=result
                    )
            else:
                # Process single file
                result = await ingestion_service.ingest_single_file(file_id)
            
            logger.info(f"File ingestion completed: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error in file ingestion handler: {e}", exc_info=True)
            
            # Create failure notification for admin if triggered by admin
            # Note: This is now a sync call (uses sync session to avoid event loop conflicts)
            payload = json.loads(job.payload) if job.payload else {}
            triggered_by_admin_id = payload.get("triggered_by_admin_id")
            if triggered_by_admin_id and payload.get("batch_mode"):
                try:
                    self._create_batch_failure_notification(
                        admin_id=triggered_by_admin_id,
                        job_id=job.id,
                        error=str(e)
                    )
                except Exception as notif_err:
                    logger.error(f"Failed to create failure notification: {notif_err}")
            
            raise
    
    def _create_batch_completion_notification(
        self,
        admin_id: int,
        job_id: int,
        result: dict
    ) -> None:
        """
        Create notification for admin when batch ingestion completes.
        
        CRITICAL: Uses SYNC session because this is called from background job thread
        with isolated event loop. Async sessions would fail with "attached to different loop" error.
        """
        try:
            from app.models.notification import Notification
            from datetime import datetime, timezone
            
            sync_session = get_sync_session()
            
            try:
                errors = result.get("errors", [])
                error_count = len(errors)
                
                if error_count == 0:
                    message = f"✅ Batch ingestion completed successfully (Job #{job_id})"
                else:
                    message = f"⚠️ Batch ingestion completed with some errors (Job #{job_id})"
                
                notification = Notification(
                    user_id=admin_id,
                    message=message,
                    notification_type="batch_ingestion_completed",
                    related_file_id=None,
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                
                sync_session.add(notification)
                sync_session.commit()
                logger.info(f"Created completion notification for admin {admin_id}, job {job_id}")
                
                # Invalidate notification cache (use sync redis client)
                self._invalidate_notification_cache_sync(admin_id)
            
            finally:
                sync_session.close()
        
        except Exception as e:
            logger.error(f"Failed to create completion notification: {e}", exc_info=True)
    
    def _invalidate_notification_cache_sync(self, user_id: int) -> None:
        """
        Invalidate notification cache using sync Redis client.
        
        CRITICAL: Uses sync operations because this is called from background job thread.
        Cannot use async cache operations due to event loop isolation.
        """
        try:
            from app.config.cache_settings import cache_settings
            
            # Only attempt if cache is enabled
            if not cache_settings.CACHE_ENABLED:
                return
            
            # Create sync Redis connection for this operation
            try:
                import redis
                redis_client = redis.from_url(
                    cache_settings.get_redis_url(),
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                
                # Delete cache keys synchronously
                redis_client.delete(f"notif:unread_count:{user_id}")
                redis_client.delete(f"dashboard:user:metrics:{user_id}")
                redis_client.delete("dashboard:admin:metrics")
                
                redis_client.close()
                logger.info(f"Invalidated notification cache for user {user_id}")
            
            except ImportError:
                logger.debug("Redis not available for cache invalidation (in-memory cache mode)")
            except Exception as redis_err:
                logger.warning(f"Redis cache invalidation failed: {redis_err} (cache may be stale)")
        
        except Exception as e:
            logger.error(f"Failed to invalidate notification cache: {e}", exc_info=True)
    
    def _create_batch_failure_notification(
        self,
        admin_id: int,
        job_id: int,
        error: str
    ) -> None:
        """
        Create notification for admin when batch ingestion fails.
        
        CRITICAL: Uses SYNC session because this is called from background job thread
        with isolated event loop. Async sessions would fail with "attached to different loop" error.
        """
        try:
            from app.models.notification import Notification
            from datetime import datetime, timezone
            
            sync_session = get_sync_session()
            
            try:
                message = (
                    f"❌ Batch ingestion failed (Job #{job_id}). "
                    f"Error: {error[:100]}"
                )
                
                notification = Notification(
                    user_id=admin_id,
                    message=message,
                    notification_type="batch_ingestion_failed",
                    related_file_id=None,
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                
                sync_session.add(notification)
                sync_session.commit()
                logger.info(f"Created failure notification for admin {admin_id}, job {job_id}")
                
                # Invalidate notification cache (use sync redis client)
                self._invalidate_notification_cache_sync(admin_id)
            
            finally:
                sync_session.close()
        
        except Exception as e:
            logger.error(f"Failed to create failure notification: {e}", exc_info=True)
    
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
        try:
            payload = json.loads(job.payload) if job.payload else {}
            
            logger.info(f"Password reset email job payload: {payload}")
            
            email_service = get_email_service()
            
            recipient_email = payload.get("recipient_email")
            recipient_name = payload.get("recipient_name")
            reset_token = payload.get("reset_token")
            reset_link_template = payload.get("reset_link_template")
            
            logger.info(
                f"Processing password reset email: "
                f"email={recipient_email}, name={recipient_name}"
            )
            
            if not all([recipient_email, recipient_name, reset_token]):
                missing = []
                if not recipient_email:
                    missing.append("recipient_email")
                if not recipient_name:
                    missing.append("recipient_name")
                if not reset_token:
                    missing.append("reset_token")
                raise ValueError(f"Missing required payload fields: {', '.join(missing)}")
            
            success = await email_service.send_password_reset(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                reset_token=reset_token,
                reset_link_template=reset_link_template
            )
            
            if success:
                logger.info(f"Password reset email sent to {recipient_email}")
                return {"status": "sent", "recipient_email": recipient_email}
            else:
                raise Exception(f"Failed to send password reset email to {recipient_email}")
        
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}", exc_info=True)
            raise

    async def _handle_password_changed_email(self, job: Job) -> dict:
        """Handle password changed notification email job."""
        try:
            payload = json.loads(job.payload) if job.payload else {}
            logger.info(f"Password changed email job payload: {payload}")
            
            email_service = get_email_service()
            
            recipient_email = payload.get("recipient_email")
            recipient_name = payload.get("recipient_name")
            
            logger.info(
                f"Processing password changed email: "
                f"email={recipient_email}, name={recipient_name}"
            )
            
            if not all([recipient_email, recipient_name]):
                missing = []
                if not recipient_email:
                    missing.append("recipient_email")
                if not recipient_name:
                    missing.append("recipient_name")
                raise ValueError(f"Missing required payload fields: {', '.join(missing)}")
            
            success = await email_service.send_password_changed(
                recipient_email=recipient_email,
                recipient_name=recipient_name
            )
            
            if success:
                logger.info(f"Password changed notification sent to {recipient_email}")
                return {"status": "sent", "recipient_email": recipient_email}
            else:
                raise Exception(f"Failed to send password changed notification to {recipient_email}")
        
        except Exception as e:
            logger.error(f"Error sending password changed notification: {e}", exc_info=True)
            raise


async def get_job_integration(session_factory) -> JobQueueIntegration:
    """Create or get JobQueueIntegration instance."""
    return JobQueueIntegration(session_factory)
