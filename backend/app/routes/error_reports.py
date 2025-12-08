"""
Error Reporting API routes.

Routes delegate request handling to handlers for business logic separation.
Requires authentication for all endpoints.

User Endpoints:
- POST /api/error-reports - Create new error report
- GET  /api/error-reports - List user's error reports
- POST /api/error-reports/{report_id}/image - Upload image for error report

Admin Endpoints:
- GET  /api/admin/error-reports - List all error reports (with filters)
- PATCH /api/admin/error-reports/{report_id} - Update error report status/notes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.core import get_logger
from app.schemas.error_report import (
    ErrorReportCreateRequest,
    ErrorReportResponse,
    ErrorReportListResponse,
    ErrorReportDetailResponse,
    ErrorReportAdminUpdateRequest,
    ErrorReportListAdminResponse,
)
from app.handlers.error_report import (
    handle_create_error_report,
    handle_get_user_error_reports,
    handle_upload_error_report_image,
    handle_get_all_error_reports_admin,
    handle_update_error_report_admin,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/error-reports", tags=["error-reports"])
admin_router = APIRouter(prefix="/api/admin/error-reports", tags=["error-reports-admin"])


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@router.post("", response_model=ErrorReportResponse, status_code=201)
async def create_error_report(
    request: ErrorReportCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    request_obj: Request = None,
) -> ErrorReportResponse:
    """Create a new error report."""
    try:
        # Get request context
        user_agent = request_obj.headers.get("user-agent", "") if request_obj else ""
        request_context = {
            "route": "/api/error-reports",
            "method": "POST",
            "conversation_id": request.conversation_id,
        }
        
        success, response = await handle_create_error_report(
            user_id=current_user.id,
            request=request,
            user_agent=user_agent,
            request_context=request_context,
            session=session,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=response.get("message", "Failed to create report"))
        
        return response
    except Exception as e:
        logger.error(f"Error creating error report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=ErrorReportListResponse)
async def get_user_error_reports(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ErrorReportListResponse:
    """Get user's error reports with optional status filter."""
    try:
        return await handle_get_user_error_reports(
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset,
            session=session,
        )
    except Exception as e:
        logger.error(f"Error fetching user error reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{report_id}/image", status_code=200)
async def upload_error_report_image(
    report_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload image for error report (max 5MB, image types only)."""
    try:
        # Validate file size (5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
        
        # Validate file type
        allowed_types = {"image/png", "image/jpeg", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Reset file pointer
        await file.seek(0)
        
        success, response = await handle_upload_error_report_image(
            report_id=report_id,
            file=file,
            user_id=current_user.id,
            session=session,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=response.get("message", "Failed to upload image"))
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading error report image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@admin_router.get("", response_model=ErrorReportListAdminResponse)
async def get_all_error_reports_admin(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ErrorReportListAdminResponse:
    """Get all error reports (admin only)."""
    try:
        # Check admin status
        if not current_user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return await handle_get_all_error_reports_admin(
            status=status,
            category=category,
            limit=limit,
            offset=offset,
            session=session,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin error reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.patch("/{report_id}", response_model=ErrorReportDetailResponse)
async def update_error_report_admin(
    report_id: int,
    update_request: ErrorReportAdminUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ErrorReportDetailResponse:
    """Update error report status and notes (admin only)."""
    try:
        # Check admin status
        if not current_user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success, response = await handle_update_error_report_admin(
            report_id=report_id,
            update_request=update_request,
            session=session,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=response.get("message", "Failed to update report"))
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating error report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
