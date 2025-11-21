"""File upload operation handlers - business logic for file operations."""

import os
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.services.file_upload import FileUploadService
from app.schemas.file_upload import FileUploadCreate, FileUploadApproveRequest, FileUploadRejectRequest
from app.models.user import User
from app.models.file_upload import FileUpload, FileStatus
from app.core import get_logger


logger = get_logger(__name__)


async def handle_upload_file(
    file_path: str,
    upload_request: FileUploadCreate,
    user: User,
    session: AsyncSession,
    file_hash: str
) -> dict:
    """Upload and create file record."""
    try:
        # Ensure uploaded_by_id is current user
        upload_request.uploaded_by_id = user.id
        
        service = FileUploadService(session)
        file_upload = await service.create_from_form(upload_request, file_path, file_hash)
        
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
                "uploaded_by_id": file_upload.uploaded_by_id,
                "status": file_upload.status.value,
                "security_level": file_upload.security_level.value,
                "is_department_only": file_upload.is_department_only,
                "department_id": file_upload.department_id,
                "file_purpose": file_upload.file_purpose,
                "created_at": file_upload.created_at.isoformat(),
                "updated_at": file_upload.updated_at.isoformat() if file_upload.updated_at else file_upload.created_at.isoformat(),
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
        
        # Get uploader info with department using the service method
        uploader_map = await service.get_file_with_uploaders([file_upload])
        uploader_info = uploader_map.get(file_upload.uploaded_by_id)
        
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "upload_token": file_upload.upload_token,
                "file_name": file_upload.file_name,
                "file_type": file_upload.file_type,
                "file_size": file_upload.file_size,
                "status": file_upload.status.value,
                "security_level": file_upload.security_level.value,
                "is_department_only": file_upload.is_department_only,
                "department_id": file_upload.department_id,
                "file_purpose": file_upload.file_purpose,
                "uploaded_by_id": file_upload.uploaded_by_id,
                "created_at": file_upload.created_at.isoformat(),
                "updated_at": file_upload.updated_at.isoformat(),
                "uploader_info": uploader_info,
                "is_processed": file_upload.is_processed,
                "processing_error": file_upload.processing_error,
                "retry_count": file_upload.retry_count,
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
                    "security_level": f.security_level.value,
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
                    "security_level": f.security_level.value,
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
    """Approve file for processing and trigger ingestion job."""
    try:
        service = FileUploadService(session)
        result = await service.approve_and_ingest(file_id, admin.id)
        
        if not result["success"]:
            await session.rollback()
            logger.warning(f"Approve file failed: {result.get('error')}")
            return {"success": False, "error": result.get("error", "Unknown error")}
        
        await session.commit()
        
        logger.warning(f"File {file_id} approved by admin {admin.id}")
        
        file_upload = result["file_upload"]
        return {
            "success": True,
            "file": {
                "id": file_upload.id,
                "file_name": file_upload.file_name,
                "status": file_upload.status.value,
            },
            "message": result.get("message"),
            "job_id": result.get("job_id"),
            "warning": result.get("warning")
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
        is_admin = user.has_role("admin")
        
        # Call service method (handles auth and deletion)
        result = await service.delete_file_secure(file_id, user.id, is_admin)
        
        if result["success"]:
            await session.commit()
        else:
            await session.rollback()
        
        return result
    except Exception as e:
        await session.rollback()
        logger.error(f"Delete file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_list_admin_files(
    status: Optional[str],
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """List all files for admin with status counts and pagination."""
    try:
        service = FileUploadService(session)
        
        # Get status counts
        counts = await service.get_status_counts()
        
        # Get paginated files
        files, total = await service.get_by_status(status, limit, offset)
        
        # Get uploader information (service handles N+1 prevention)
        uploader_map = await service.get_file_with_uploaders(files)
        
        # Build response with uploader info
        files_data = []
        for f in files:
            file_dict = {
                "id": f.id,
                "upload_token": f.upload_token,
                "file_name": f.file_name,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_by_id": f.uploaded_by_id,
                "status": f.status.value,
                "security_level": f.security_level.value,
                "is_department_only": f.is_department_only,
                "department_id": f.department_id,
                "file_purpose": f.file_purpose,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat() if f.updated_at else f.created_at.isoformat(),
                "uploader_info": uploader_map.get(f.uploaded_by_id)
            }
            files_data.append(file_dict)
        
        return {
            "success": True,
            "counts": counts,
            "files": files_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"List admin files failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_list_user_files_by_status(
    user_id: int,
    status: Optional[str],
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """List user's files with status counts and pagination."""
    try:
        service = FileUploadService(session)
        
        # Get status counts for this user (moved to service)
        counts = await service.get_user_status_counts(user_id)
        
        # Get paginated files with status filter
        files, total = await service.get_user_by_status(user_id, status, limit, offset)
        
        # Build response without uploader info (user sees only their files)
        files_data = []
        for f in files:
            file_dict = {
                "id": f.id,
                "upload_token": f.upload_token,
                "file_name": f.file_name,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_by_id": f.uploaded_by_id,
                "status": f.status.value,
                "security_level": f.security_level.value,
                "is_department_only": f.is_department_only,
                "department_id": f.department_id,
                "file_purpose": f.file_purpose,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat() if f.updated_at else f.created_at.isoformat()
            }
            files_data.append(file_dict)
        
        return {
            "success": True,
            "counts": counts,
            "files": files_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"List user files by status failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_file_content(
    file_id: int,
    user: User,
    session: AsyncSession
) -> dict:
    """Get file content for viewing (text, JSON, CSV, Excel, PDF only)."""
    try:
        service = FileUploadService(session)
        is_admin = user.has_role("admin")
        
        # Call service method (returns error for unsupported types like DOCX)
        result = await service.get_file_content(file_id, user.id, is_admin)
        
        return result
    except Exception as e:
        logger.error(f"Get file content failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_ingest_file(
    file_id: int,
    admin: User,
    session: AsyncSession
) -> dict:
    """Manually trigger ingestion for an approved file."""
    try:
        service = FileUploadService(session)
        result = await service.trigger_ingestion(file_id, admin.id)
        
        if not result["success"]:
            logger.warning(f"Manual ingestion failed for file {file_id}: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
        
        logger.info(f"Admin {admin.id} triggered manual ingestion job {result['job_id']} for file {file_id}")
        
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "message": result.get("message")
        }
    except Exception as e:
        logger.error(f"Handle ingest file failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
