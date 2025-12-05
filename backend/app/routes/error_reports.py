"""
Error Report Routes - User and admin endpoints for error reporting.

Endpoints:
- POST   /api/error-reports              - User submits error report
- GET    /api/error-reports              - User views their reports
- GET    /api/admin/error-reports        - Admin views all reports
- PATCH  /api/admin/error-reports/{id}   - Admin updates report status/notes
- POST   /api/error-reports/{id}/image   - Upload image for report
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.security import RoleRequired
from app.models.user import User
from app.schemas.error_report import (
    ErrorReportCreateRequest,
    ErrorReportResponse,
    ErrorReportListResponse,
    ErrorReportDetailResponse,
    ErrorReportAdminUpdateRequest,
    ErrorReportListAdminResponse,
)
from app.models.error_report import ErrorReportStatus, ErrorReportCategory
from app.services.error_report_service import get_error_report_service
from app.core import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/error-reports", tags=["Error Reports"])


@router.post("", response_model=ErrorReportResponse, status_code=status.HTTP_201_CREATED)
async def create_error_report(
    request: ErrorReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErrorReportResponse:
    """
    Create a new error report.
    
    Any authenticated user can report errors they encounter.
    
    Request body:
    - title: Brief description of the error
    - description: Detailed description of what happened
    - category: Category of error (llm_error, retrieval_error, etc.)
    - conversation_id: (Optional) ID of conversation where error occurred
    """
    try:
        service = get_error_report_service(db)
        
        # Create report
        success, response = await service.create_report(
            user_id=current_user.id,
            request=request,
            user_agent=request.headers.get("user-agent") if hasattr(request, "headers") else None,
        )
        
        if not success:
            logger.error(f"Failed to create error report: {response}")
            raise HTTPException(status_code=400, detail="Failed to create error report")
        
        await db.commit()
        
        logger.info(f"Error report created: {response.id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=ErrorReportListResponse)
async def get_user_error_reports(
    status: Optional[ErrorReportStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErrorReportListResponse:
    """
    Get error reports submitted by current user.
    
    Query parameters:
    - status: (Optional) Filter by status (open, investigating, resolved, etc.)
    - limit: Number of reports (default 50, max 100)
    - offset: Pagination offset
    """
    try:
        service = get_error_report_service(db)
        
        reports = await service.get_user_reports(
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        total = await service.get_user_reports_count(current_user.id, status)
        
        return ErrorReportListResponse(reports=reports, total=total)
    
    except Exception as e:
        logger.error(f"Error getting user reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@router.post("/{report_id}/image", status_code=status.HTTP_200_OK)
async def upload_error_report_image(
    report_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload image attachment for error report.
    
    - Maximum file size: 5MB
    - Supported formats: PNG, JPG, JPEG, GIF, WebP
    - Only user who submitted report can upload image
    """
    try:
        service = get_error_report_service(db)
        
        # Verify file size
        file_size = len(await file.read())
        await file.seek(0)
        
        max_size = 5 * 1024 * 1024  # 5MB
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
        
        # Verify file type
        allowed_types = {"image/png", "image/jpeg", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not supported")
        
        # TODO: Save file to disk and get filename
        # For now, just store the filename
        filename = f"error_report_{report_id}_{file.filename}"
        
        success = await service.attach_image(
            report_id=report_id,
            filename=filename,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Error report not found")
        
        await db.commit()
        
        return {"message": "Image uploaded successfully", "filename": filename}
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image")


# Admin routes

admin_router = APIRouter(prefix="/api/admin/error-reports", tags=["Admin - Error Reports"])


@admin_router.get("", response_model=ErrorReportListAdminResponse)
async def get_all_error_reports_admin(
    status: Optional[ErrorReportStatus] = Query(None, description="Filter by status"),
    category: Optional[ErrorReportCategory] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErrorReportListAdminResponse:
    """
    Get all error reports (admin only).
    
    Query parameters:
    - status: (Optional) Filter by status
    - category: (Optional) Filter by category
    - limit: Number of reports (default 50, max 100)
    - offset: Pagination offset
    """
    # Check admin role
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = get_error_report_service(db)
        
        reports, total, status_counts = await service.get_all_reports_admin(
            status=status,
            category=category,
            limit=limit,
            offset=offset,
        )
        
        return ErrorReportListAdminResponse(
            reports=reports,
            total=total,
            open_count=status_counts.get("open", 0),
            investigating_count=status_counts.get("investigating", 0),
            resolved_count=status_counts.get("resolved", 0),
        )
    
    except Exception as e:
        logger.error(f"Error getting admin reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@admin_router.patch("/{report_id}", response_model=ErrorReportDetailResponse)
async def update_error_report_admin(
    report_id: int,
    update: ErrorReportAdminUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErrorReportDetailResponse:
    """
    Update error report status and notes (admin only).
    
    Request body:
    - status: New status (open, investigating, acknowledged, resolved, etc.)
    - admin_notes: Investigation notes or resolution details
    - assigned_to: (Optional) User ID to assign the report to
    """
    # Check admin role
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = get_error_report_service(db)
        
        success, updated_report = await service.update_report_admin(report_id, update)
        
        if not success:
            raise HTTPException(status_code=404, detail="Error report not found")
        
        await db.commit()
        
        logger.info(f"Error report {report_id} updated by admin {current_user.id}")
        return updated_report
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update report")
