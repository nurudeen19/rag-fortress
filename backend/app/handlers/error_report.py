"""
Error Report request handlers.

Handlers delegate to service layer for:
- Creating error reports from user input
- Retrieving user's own error reports
- Attaching images to error reports
- Listing all reports (admin view)
- Updating report status and notes (admin)

Service layer handles:
- Business logic (validation, authorization)
- Serialization (model to dict)
- Transaction management
- Error handling
"""

import logging
from typing import Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

# Generate filename
import uuid
from datetime import datetime

from app.services.error_report_service import ErrorReportService
from app.services.notification_service import NotificationService
from app.config.settings import settings
from pathlib import Path
from app.models.user import User
from app.schemas.error_report import (
    ErrorReportCreateRequest,
    ErrorReportResponse,
    ErrorReportListResponse,
    ErrorReportDetailResponse,
    ErrorReportAdminUpdateRequest,
    ErrorReportListAdminResponse,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ERROR REPORT MANAGEMENT HANDLERS
# ============================================================================

async def handle_create_error_report(
    user_id: int,
    request: ErrorReportCreateRequest,
    user_agent: str,
    request_context: dict,
    session: AsyncSession,
    reporter: Optional[User] = None,
) -> Tuple[bool, ErrorReportResponse]:
    """
    Handle create error report request.
    
    Args:
        user_id: User ID creating the report
        request: Error report creation request data
        user_agent: User agent string from request
        request_context: Request context (route, params, etc.)
        session: Database session
        
    Returns:
        Tuple of (success: bool, response: ErrorReportResponse or error dict)
    """
    logger.info(f"Creating error report for user {user_id}: {request.title}")
    service = ErrorReportService(session)
    success, response = await service.create_report(
        user_id=user_id,
        request=request,
        user_agent=user_agent,
        request_context=request_context,
    )

    if success:
        try:
            notif_service = NotificationService(session)
            reporter_name = None
            if reporter:
                reporter_name = f"{reporter.first_name} {reporter.last_name}".strip()
                reporter_name = reporter_name or reporter.email
            await notif_service.notify_admins_new_error_report(
                report=response,
                reporter_name=reporter_name,
            )
            await session.commit()
        except Exception:
            logger.warning("Failed to send admin notification for new error report", exc_info=True)

    return success, response


async def handle_get_user_error_reports(
    user_id: int,
    status: Optional[str],
    limit: int,
    offset: int,
    session: AsyncSession,
) -> ErrorReportListResponse:
    """
    Handle get user error reports request.
    
    Args:
        user_id: User ID to fetch reports for
        status: Optional status filter
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        ErrorReportListResponse with paginated reports
    """
    logger.info(f"Fetching error reports for user {user_id}")
    service = ErrorReportService(session)
    reports = await service.get_user_reports(
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    count = await service.get_user_reports_count(user_id=user_id, status=status)
    
    return ErrorReportListResponse(
        items=reports,
        total=count,
        limit=limit,
        offset=offset,
    )


async def handle_upload_error_report_image(
    report_id: int,
    file: UploadFile,
    user_id: int,
    session: AsyncSession,
) -> Tuple[bool, dict]:
    """
    Handle upload error report image request.
    
    Args:
        report_id: Error report ID
        file: Uploaded file
        user_id: User ID (for authorization check)
        session: Database session
        
    Returns:
        Tuple of (success: bool, response dict)
    """
    logger.info(f"Uploading image for error report {report_id} by user {user_id}")
    service = ErrorReportService(session)
    
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    original_name = Path(file.filename).name
    filename = f"error_report_{report_id}_{timestamp}_{unique_id}_{original_name}"
    
    # Persist file to disk under DATA_DIR/error_reports
    storage_dir = Path(settings.DATA_DIR) / "error_reports"
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / filename
    
    content = await file.read()
    file_path.write_bytes(content)
    
    image_url = f"/static/error-reports/{filename}"
    
    success = await service.attach_image(
        report_id=report_id,
        filename=filename,
        image_url=image_url,
        user_id=user_id,
    )
    
    if success:
        return (True, {"message": "Image uploaded successfully", "filename": filename, "image_url": image_url})
    else:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        return (False, {"message": "Failed to attach image to report"})


async def handle_get_all_error_reports_admin(
    status: Optional[str],
    category: Optional[str],
    limit: int,
    offset: int,
    session: AsyncSession,
) -> ErrorReportListAdminResponse:
    """
    Handle get all error reports request (admin).
    
    Args:
        status: Optional status filter
        category: Optional category filter
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        ErrorReportListAdminResponse with paginated reports and metrics
    """
    logger.info(f"Fetching all error reports (admin view)")
    service = ErrorReportService(session)
    reports, total, status_counts = await service.get_all_reports_admin(
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    
    # Map service response into the schema expected by the route
    return ErrorReportListAdminResponse(
        reports=reports,
        total=total,
        open_count=status_counts.get("open", 0),
        investigating_count=status_counts.get("investigating", 0),
        resolved_count=status_counts.get("resolved", 0),
    )


async def handle_update_error_report_admin(
    report_id: int,
    update_request: ErrorReportAdminUpdateRequest,
    session: AsyncSession,
    acting_admin: Optional[User] = None,
) -> Tuple[bool, ErrorReportDetailResponse]:
    """
    Handle update error report request (admin).
    
    Args:
        report_id: Error report ID to update
        update_request: Update request with new status, notes, assigned_to
        session: Database session
        
    Returns:
        Tuple of (success: bool, response: ErrorReportDetailResponse or error dict)
    """
    logger.info(f"Updating error report {report_id} (admin)")
    service = ErrorReportService(session)
    success, detail = await service.update_report_admin(report_id=report_id, update=update_request)

    if success and detail:
        try:
            notif_service = NotificationService(session)
            await notif_service.notify_error_report_status_changed(
                report=detail,
                acting_admin=acting_admin,
            )
            await session.commit()
        except Exception:
            logger.warning("Failed to send status update notification for error report", exc_info=True)
    
    return success, detail
