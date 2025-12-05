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

from app.services.error_report_service import ErrorReportService
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
    return await service.create_report(
        user_id=user_id,
        request=request,
        user_agent=user_agent,
        request_context=request_context,
    )


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
    
    # Generate filename
    import uuid
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"error_report_{report_id}_{timestamp}_{unique_id}_{file.filename}"
    
    # TODO: Save file to disk at /data/error_reports/
    # For now, just store the filename in DB
    image_url = f"/data/error_reports/{filename}"
    
    success = await service.attach_image(
        report_id=report_id,
        filename=filename,
        image_url=image_url,
    )
    
    if success:
        return (True, {"message": "Image uploaded successfully", "filename": filename})
    else:
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
    
    return ErrorReportListAdminResponse(
        items=reports,
        total=total,
        limit=limit,
        offset=offset,
        status_counts=status_counts,
    )


async def handle_update_error_report_admin(
    report_id: int,
    update_request: ErrorReportAdminUpdateRequest,
    session: AsyncSession,
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
    return await service.update_report_admin(report_id=report_id, update=update_request)
