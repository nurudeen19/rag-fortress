"""Admin operation handlers - business logic for admin operations."""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core import get_logger
from app.models.file_upload import FileUpload, FileStatus
from app.models.user import User
from app.services.admin_service import AdminService

logger = get_logger(__name__)


async def handle_trigger_batch_ingestion(
    admin: User,
    session: AsyncSession
) -> Dict:
    """
    Trigger batch ingestion of all approved unprocessed files.
    
    Creates a background job that will:
    1. Load all approved files
    2. Process through ingestion pipeline
    3. Create notification on completion
    
    Args:
        admin: Admin user triggering the operation
        session: Database session
        
    Returns:
        Dict with success status and job_id
    """
    try:
        logger.info(f"Admin {admin.id} attempting to trigger batch ingestion")
        
        # Use service to create and schedule job
        service = AdminService(session)
        result = await service.trigger_batch_ingestion(admin_id=admin.id)
        
        if not result["success"]:
            logger.warning(f"Batch ingestion job creation failed: {result.get('error')}")
            return result
        
        logger.info(f"Batch ingestion job {result['job_id']} created by admin {admin.id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Handle trigger batch ingestion failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
