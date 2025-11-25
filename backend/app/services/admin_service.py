"""
Admin Service - Business logic for admin-specific operations.
"""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.core.startup import get_startup_controller
from app.models.job import JobType
from app.services.notification_service import NotificationService


logger = get_logger(__name__)


class AdminService:
    """Manages admin-specific operations like batch ingestion."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    async def trigger_batch_ingestion(self, admin_id: int) -> Dict:
        """
        Create and schedule batch ingestion job for all approved files.
        
        Uses existing DocumentIngestionService.ingest_batch() through job system.
        Creates notification for admin when job completes.
        
        Args:
            admin_id: Admin user triggering the operation
            
        Returns:
            Dict with success status, job_id, and message
        """
        try:
            from app.models.file_upload import FileUpload, FileStatus
            from sqlalchemy import select, func
            
            # Count pending files
            result = await self.session.execute(
                select(func.count(FileUpload.id)).where(
                    (FileUpload.status == FileStatus.APPROVED) &
                    (FileUpload.is_processed == False)
                )
            )
            pending_file_count = result.scalar() or 0
            
            if pending_file_count == 0:
                logger.info("No approved unprocessed files found for batch ingestion")
                return {
                    "success": False,
                    "error": "No files are ready to be processed"
                }
            
            logger.info(
                f"Creating batch ingestion job for admin {admin_id}, "
                f"{pending_file_count} files pending"
            )
            
            # Get job integration from startup controller
            startup_controller = get_startup_controller()
            job_integration = startup_controller.job_integration
            
            if job_integration is None:
                raise Exception("Job integration not initialized")
            
            # Create and schedule batch ingestion job
            job = await job_integration.create_and_schedule(
                job_type=JobType.FILE_INGESTION,
                reference_id=0,  # 0 indicates batch mode
                reference_type="batch",
                handler=job_integration._handle_file_ingestion,
                payload={
                    "batch_mode": True,
                    "triggered_by_admin_id": admin_id,
                    "pending_file_count": pending_file_count
                },
                max_retries=1  # Batch jobs don't retry to avoid reprocessing
            )
            
            logger.info(f"Created batch ingestion job {job.id} for admin {admin_id}")
            
            # Create initial notification for admin
            notification_service = NotificationService(self.session)
            await notification_service.create(
                user_id=admin_id,
                message=f"Batch ingestion started (Job #{job.id})",
                notification_type="batch_ingestion_started",
                related_file_id=None
            )
            
            # Commit notification
            await self.session.commit()
            
            logger.info(f"Created notification for admin {admin_id} about batch job {job.id}")
            
            return {
                "success": True,
                "job_id": job.id,
                "message": "Batch ingestion job has been started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger batch ingestion: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
