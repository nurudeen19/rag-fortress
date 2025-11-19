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
                "security_level": file_upload.security_level.name,
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
        
        # Collect all uploader IDs
        uploader_ids = [f.uploaded_by_id for f in files if f.uploaded_by_id]
        
        # Fetch all uploaders in a single query (avoid N+1)
        uploader_map = {}
        if uploader_ids:
            from sqlalchemy import select
            from app.models.user import User
            
            uploader_stmt = select(User).where(User.id.in_(uploader_ids))
            uploader_result = await session.execute(uploader_stmt)
            uploaders = uploader_result.scalars().all()
            
            uploader_map = {
                u.id: {
                    "full_name": u.full_name or f"User #{u.id}",
                    "department_name": u.department.name if u.department else None
                }
                for u in uploaders
            }
        
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
                "security_level": f.security_level.name,
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
        
        # Get status counts for this user
        counts = {}
        total_user_files = 0
        
        for s in FileStatus:
            result = await session.execute(
                select(func.count(FileUpload.id)).where(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == s
                )
            )
            count = result.scalar() or 0
            counts[s.value] = count
            total_user_files += count
        
        counts["all"] = total_user_files
        
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
                "security_level": f.security_level.name,
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
    """Get file content for viewing (supports text, JSON, CSV, Excel, PDF, DOCX)."""
    try:
        service = FileUploadService(session)
        
        # Get file record
        file_record = await session.get(FileUpload, file_id)
        if not file_record:
            return {"success": False, "error": "File not found"}
        
        # Check authorization
        is_owner = file_record.uploaded_by_id == user.id
        is_admin = user.has_role("admin")
        
        if not (is_owner or is_admin):
            return {"success": False, "error": "Access denied"}
        
        # Resolve file path: relative path -> full path
        import os
        from docx2html import convert
        
        base_dir = os.getenv("FILES_DIR", "data/files")
        full_path = os.path.join(base_dir, file_record.file_path)
        
        try:
            # Check if file is DOCX and convert to HTML for viewing
            if file_record.file_type in ("docx", "doc") or full_path.lower().endswith((".docx", ".doc")):
                logger.info(f"Converting DOCX to HTML for file_id={file_id}")
                
                try:
                    # Convert DOCX to HTML using docx2html (pure Python, no external dependencies)
                    html_content = convert(full_path)
                    
                    # Wrap HTML with styling for better display
                    styled_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                line-height: 1.6;
                                padding: 20px;
                                background-color: #f5f5f5;
                            }}
                            .content {{
                                background-color: white;
                                padding: 20px;
                                border-radius: 8px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                max-width: 900px;
                                margin: 0 auto;
                            }}
                            table {{
                                border-collapse: collapse;
                                width: 100%;
                                margin: 15px 0;
                            }}
                            td, th {{
                                border: 1px solid #ddd;
                                padding: 12px;
                                text-align: left;
                            }}
                            th {{
                                background-color: #f0f0f0;
                                font-weight: bold;
                            }}
                            ul, ol {{
                                margin: 10px 0;
                                padding-left: 30px;
                            }}
                            h1, h2, h3, h4, h5, h6 {{
                                margin-top: 15px;
                                margin-bottom: 10px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="content">
                            {html_content}
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Return HTML as text content
                    file_content = styled_html.encode('utf-8')
                    logger.info(f"Successfully converted DOCX to HTML for file_id={file_id}")
                    
                    return {
                        "success": True,
                        "content": file_content,
                        "filename": file_record.file_name.rsplit(".", 1)[0] + ".html",
                        "file_type": "html"  # Set type to html so frontend treats it as HTML
                    }
                except Exception as conv_err:
                    logger.warning(f"DOCX to HTML conversion failed, trying plain text extraction: {conv_err}")
                    # Fallback: Extract plain text from DOCX
                    try:
                        from docx import Document
                        doc = Document(full_path)
                        text_content = "\n".join([para.text for para in doc.paragraphs])
                        file_content = text_content.encode('utf-8')
                        return {
                            "success": True,
                            "content": file_content,
                            "filename": file_record.file_name.rsplit(".", 1)[0] + ".txt",
                            "file_type": "txt"
                        }
                    except Exception as fallback_err:
                        logger.error(f"DOCX plain text fallback also failed: {fallback_err}")
                        return {"success": False, "error": f"Failed to process DOCX file: {str(fallback_err)}"}
            else:
                # For non-DOCX files, return as-is
                with open(full_path, "rb") as f:
                    file_content = f.read()
                
                logger.info(f"Retrieved file content for file_id={file_id}, user_id={user.id}")
                
                return {
                    "success": True,
                    "content": file_content,
                    "filename": file_record.file_name,
                    "file_type": file_record.file_type
                }
        except FileNotFoundError:
            logger.error(f"File not found on disk: {full_path}")
            return {"success": False, "error": "File not found on disk"}
    
    except Exception as e:
        logger.error(f"Get file content failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
