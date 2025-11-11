"""File upload endpoints."""

import os
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user, require_role
from app.schemas.file_upload import (
    FileUploadCreate,
    FileUploadResponse,
    FileUploadDetailResponse,
    FileUploadListResponse,
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
)


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/files", tags=["files"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    file_purpose: Optional[str] = Query(None),
    security_level: SecurityLevelEnum = Query(SecurityLevelEnum.GENERAL),
    is_department_only: bool = Query(False),
    department_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload file and create database record."""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required"
            )
        
        # Get file extension
        file_parts = file.filename.rsplit(".", 1)
        if len(file_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have an extension"
            )
        
        file_name, file_ext = file_parts
        file_ext = file_ext.lower()
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (100MB max)
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 100MB limit"
            )
        
        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create upload request
        upload_request = FileUploadCreate(
            file_name=file_name,
            file_type=file_ext,
            file_size=file_size,
            uploaded_by_id=user.id,
            file_purpose=file_purpose,
            security_level=security_level,
            is_department_only=is_department_only,
            department_id=department_id,
        )
        
        # Call handler
        result = await handle_upload_file(file_path, upload_request, user, session)
        
        if not result.get("success"):
            if os.path.exists(file_path):
                os.remove(file_path)
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
