"""File upload operation handlers - business logic for file operations."""

import os
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.file_upload import FileUploadService, FileStorage
from app.schemas.file_upload import FileUploadCreate, FileUploadApproveRequest, FileUploadRejectRequest
from app.models.user import User
from app.core import get_logger


logger = get_logger(__name__)


async def handle_upload_file(
    file_path: str,
    upload_request: FileUploadCreate,
    user: User,
    session: AsyncSession
) -> dict:
    """Upload and create file record."""
    try:
        # Ensure uploaded_by_id is current user
        upload_request.uploaded_by_id = user.id
        
        service = FileUploadService(session)
        file_upload = await service.create_from_form(upload_request, file_path)
        
        await session.commit()
        
        logger.info(f"File uploaded by user {user.id}: {upload_request.file_name}")
        
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "upload_token": file_upload.upload_token,
                "file_name": file_upload.file_name,
                "file_type": file_upload.file_type,
                "file_size": file_upload.file_size,
                "status": file_upload.status.value,
                "security_level": file_upload.security_level.name,
                "created_at": file_upload.created_at.isoformat(),
            }
        }
    except Exception as e:
        await session.rollback()
        logger.error(f"Upload failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_file(file_id: int, session: AsyncSession) -> dict:
    """Get file details."""
    try:
        service = FileUploadService(session)
        file_upload = await service.get_file(file_id)
        
        if not file_upload:
            return {"success": False, "error": "File not found"}
        
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "upload_token": file_upload.upload_token,
                "file_name": file_upload.file_name,
                "file_type": file_upload.file_type,
                "file_size": file_upload.file_size,
                "status": file_upload.status.value,
                "security_level": file_upload.security_level.name,
                "is_department_only": file_upload.is_department_only,
                "department_id": file_upload.department_id,
                "file_purpose": file_upload.file_purpose,
                "uploaded_by_id": file_upload.uploaded_by_id,
                "created_at": file_upload.created_at.isoformat(),
                "updated_at": file_upload.updated_at.isoformat(),
                "is_processed": file_upload.status.value in ["processed", "failed"],
                "chunks_created": file_upload.chunks_created,
                "processing_time_ms": file_upload.processing_time_ms,
            }
        }
    except Exception as e:
        logger.error(f"Get file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_list_user_files(
    user_id: int,
    limit: int,
    session: AsyncSession
) -> dict:
    """List files uploaded by user."""
    try:
        service = FileUploadService(session)
        files = await service.get_by_user(user_id, limit=limit)
        
        return {
            "success": True,
            "files": [
                {
                    "id": f.id,
                    "file_name": f.file_name,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "status": f.status.value,
                    "security_level": f.security_level.name,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ],
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"List user files failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_list_pending_approval(
    limit: int,
    session: AsyncSession
) -> dict:
    """List files awaiting approval (admin only)."""
    try:
        service = FileUploadService(session)
        files = await service.get_pending_approval(limit=limit)
        
        return {
            "success": True,
            "files": [
                {
                    "id": f.id,
                    "file_name": f.file_name,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "uploaded_by_id": f.uploaded_by_id,
                    "status": f.status.value,
                    "security_level": f.security_level.name,
                    "file_purpose": f.file_purpose,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ],
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"List pending files failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_approve_file(
    file_id: int,
    admin: User,
    session: AsyncSession
) -> dict:
    """Approve file for processing."""
    try:
        service = FileUploadService(session)
        file_upload = await service.approve(file_id, admin.id)
        
        await session.commit()
        
        logger.warning(f"File {file_id} approved by admin {admin.id}")
        
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "file_name": file_upload.file_name,
                "status": file_upload.status.value,
            },
            "message": "File approved"
        }
    except ValueError as e:
        await session.rollback()
        logger.warning(f"Approve file failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        await session.rollback()
        logger.error(f"Approve file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_reject_file(
    file_id: int,
    reason: str,
    admin: User,
    session: AsyncSession
) -> dict:
    """Reject file from processing."""
    try:
        service = FileUploadService(session)
        file_upload = await service.reject(file_id, admin.id, reason=reason)
        
        await session.commit()
        
        logger.warning(f"File {file_id} rejected by admin {admin.id}: {reason}")
        
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "file_name": file_upload.file_name,
                "status": file_upload.status.value,
            },
            "message": "File rejected"
        }
    except ValueError as e:
        await session.rollback()
        logger.warning(f"Reject file failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        await session.rollback()
        logger.error(f"Reject file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_delete_file(
    file_id: int,
    user: User,
    session: AsyncSession
) -> dict:
    """Delete file (user can delete own uploads, admin can delete any)."""
    try:
        service = FileUploadService(session)
        file_upload = await service.get_file(file_id)
        
        if not file_upload:
            return {"success": False, "error": "File not found"}
        
        # Check permissions: owner or admin
        is_admin = any(role.name == "admin" for role in user.roles)
        if file_upload.uploaded_by_id != user.id and not is_admin:
            return {"success": False, "error": "Permission denied"}
        
        # Delete physical file from disk
        storage = FileStorage()
        await storage.delete_file(file_upload.file_path)
        
        # Mark as deleted in database
        deleted_file = await service.delete(file_id)
        await session.commit()
        
        logger.info(f"File {file_id} deleted by user {user.id}")
        
        return {
            "success": True,
            "message": "File deleted"
        }
    except Exception as e:
        await session.rollback()
        logger.error(f"Delete file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
