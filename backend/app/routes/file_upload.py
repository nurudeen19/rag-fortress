"""File upload endpoints."""

import os
import json
import tempfile
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user, require_role
from app.schemas.file_upload import (
    FileUploadCreate,
    FileUploadResponse,
    FileUploadDetailResponse,
    FileUploadListResponse,
    FileUploadListWithCountsResponse,
    FileUploadApproveRequest,
    FileUploadRejectRequest,
    SecurityLevelEnum,
)
from app.schemas.user import SuccessResponse
from app.models.user import User
from app.core import get_logger
from app.handlers.file_upload import (
    handle_upload_file,
    handle_get_file,
    handle_list_user_files,
    handle_list_pending_approval,
    handle_approve_file,
    handle_reject_file,
    handle_delete_file,
    handle_list_admin_files,
    handle_list_user_files_by_status,
    handle_get_file_content,
)
from app.services.file_upload import FileValidator, FileStorage, StructuredDataParser


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    file_purpose: Optional[str] = Query(None),
    security_level: SecurityLevelEnum = Query(SecurityLevelEnum.GENERAL),
    is_department_only: bool = Query(False),
    department_id: Optional[int] = Query(None),
    field_selection: Optional[str] = Query(None),  # JSON string of selected fields
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload file and create database record."""
    # Use 'uploaded' category for user-uploaded files
    storage = FileStorage(category="uploaded")
    
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file
        is_valid, error_msg, file_type = FileValidator.validate_file(
            file.filename,
            file_size,
            file.content_type
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Save file to disk (returns relative path like "uploaded/filename.pdf")
        file_path = await storage.save_file(file.filename, content)
        
        # Calculate file hash
        file_hash = await FileStorage.calculate_hash(file_path)
        
        # Parse field_selection from query param
        selected_fields = []
        if field_selection:
            try:
                selected_fields = json.loads(field_selection)
                if not isinstance(selected_fields, list):
                    selected_fields = []
            except json.JSONDecodeError:
                logger.warning(f"Invalid field_selection JSON: {field_selection}")
                selected_fields = []
        
        # Extract fields from structured data if applicable
        available_fields = []
        if file_type in ("json", "csv", "xlsx", "xls"):
            try:
                available_fields = StructuredDataParser.extract_fields(file_path, file_type)
                
                # Validate selected fields exist in file
                if selected_fields:
                    selected_fields = StructuredDataParser.validate_field_selection(
                        available_fields,
                        selected_fields
                    )
            except Exception as e:
                logger.warning(f"Failed to extract fields from {file.filename}: {e}")
                available_fields = []
        
        # Create upload request
        upload_request = FileUploadCreate(
            file_name=file.filename,
            file_type=file_type,
            file_size=file_size,
            uploaded_by_id=user.id,
            file_purpose=file_purpose,
            security_level=security_level,
            is_department_only=is_department_only,
            department_id=department_id,
            field_selection=selected_fields if selected_fields else None,
        )
        
        # Call handler
        result = await handle_upload_file(file_path, upload_request, user, session, file_hash)
        
        if not result.get("success"):
            await storage.delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Upload failed")
            )
        
        return FileUploadResponse(**result["file"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


@router.get("/list", response_model=FileUploadListWithCountsResponse)
async def list_files(
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, processed, failed, all)"),
    limit: int = Query(50, ge=1, le=200, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List files with status counts and pagination.
    
    Automatically returns:
    - All files (if user is admin)
    - User's own files (if user is regular user)
    
    Query Parameters:
    - status_filter: Filter by status (pending, approved, rejected, processed, failed, or null for all)
    - limit: Number of items per page (1-200)
    - offset: Pagination offset
    """
    # Handler automatically checks user role and returns appropriate data
    # Admin sees all files, regular users see only their own
    if user.has_role("admin"):
        # Admin sees all files
        result = await handle_list_admin_files(status_filter, limit, offset, session)
    else:
        # Regular user sees only their own files
        result = await handle_list_user_files_by_status(user.id, status_filter, limit, offset, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to list files")
        )
    
    return FileUploadListWithCountsResponse(
        counts=result["counts"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        items=[FileUploadResponse(**f) for f in result["files"]]
    )


@router.get("/{file_id}", response_model=FileUploadDetailResponse)
async def get_file(
    file_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get file details."""
    result = await handle_get_file(file_id, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "File not found")
        )
    
    return FileUploadDetailResponse(**result["file"])


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get file content for viewing in browser.
    Supports: PDF, Excel, CSV, DOCX, JSON, Markdown, TXT
    """
    result = await handle_get_file_content(file_id, user, session)
    
    if not result.get("success"):
        status_code = status.HTTP_403_FORBIDDEN if "Access denied" in result.get("error", "") else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Failed to retrieve file")
        )
    
    # Return file as streaming response
    file_content = result["content"]
    filename = result["filename"]
    
    # Determine media type based on file extension
    file_ext = filename.lower().split(".")[-1]
    media_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "csv": "text/csv",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain"
    }
    media_type = media_types.get(file_ext, "application/octet-stream")
    
    return StreamingResponse(
        iter([file_content]),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/", response_model=FileUploadListResponse)
async def list_my_files(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List files uploaded by current user."""
    result = await handle_list_user_files(user.id, limit, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return FileUploadListResponse(
        total=result["total"],
        items=[FileUploadResponse(**f) for f in result["files"]]
    )


@router.get("/admin/pending", response_model=FileUploadListResponse)
async def list_pending_approval(
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """List files awaiting approval (admin only)."""
    result = await handle_list_pending_approval(limit, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return FileUploadListResponse(
        total=result["total"],
        items=[FileUploadResponse(**f) for f in result["files"]]
    )


@router.post("/{file_id}/approve", response_model=SuccessResponse)
async def approve_file(
    file_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Approve file for processing (admin only)."""
    result = await handle_approve_file(file_id, admin, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return SuccessResponse(message=result.get("message", "File approved"))


@router.post("/{file_id}/reject", response_model=SuccessResponse)
async def reject_file(
    file_id: int,
    reason: str = Query(..., min_length=1),
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Reject file from processing (admin only)."""
    result = await handle_reject_file(file_id, reason, admin, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return SuccessResponse(message=result.get("message", "File rejected"))


@router.delete("/{file_id}", response_model=SuccessResponse)
async def delete_file(
    file_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete file (owner or admin only)."""
    result = await handle_delete_file(file_id, user, session)
    
    if not result.get("success"):
        status_code = status.HTTP_403_FORBIDDEN if "Permission" in result.get("error", "") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error")
        )
    
    return SuccessResponse(message=result.get("message", "File deleted"))

