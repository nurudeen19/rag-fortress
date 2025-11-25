"""Admin-only API routes for system management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_role
from app.models.user import User
from app.services.permission_service import PermissionService
from app.handlers.admin import handle_trigger_batch_ingestion

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/files/trigger-batch-ingestion")
async def trigger_batch_ingestion(
    admin_user: User =  Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Trigger batch ingestion of all approved unprocessed files.
    
    This creates a background job that will process all files with:
    - status = APPROVED
    - is_processed = False
    
    Admin will receive notifications when job starts and completes.
    
    **Requires:** Admin role
    
    **Returns:**
    - job_id: Database job ID for tracking
    - message: Success message if files are ready, error if no files to process
    """
    result = await handle_trigger_batch_ingestion(admin_user, session)
    
    if not result["success"]:
        error_msg = result.get("error", "")
        if "No files are ready to be processed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg or "Failed to trigger batch ingestion"
        )
    
    return {
        "status": "ok",
        "data": {
            "job_id": result["job_id"]
        },
        "message": result["message"]
    }
