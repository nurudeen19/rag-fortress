"""
File Upload Service - Manages file upload lifecycle and database operations.
Core service for tracking uploads, approvals, and processing status.
"""

import uuid
import json
from typing import Optional, List, Dict, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload, FileStatus, SecurityLevel
from app.schemas.file_upload import FileUploadCreate
from app.core import get_logger


logger = get_logger(__name__)


class FileUploadService:
    """Manages file upload lifecycle: creation, approval, processing."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    async def create_from_form(self, data: FileUploadCreate, file_path: str, file_hash: str) -> FileUpload:
        """
        Create file upload from form submission (recommended for frontend).
        
        Args:
            data: FileUploadCreate schema with all required fields
            file_path: Full path where file is stored
            file_hash: SHA-256 hash of file
        
        Returns:
            FileUpload record
        """
        try:
            # Convert security level enum to value
            security_level = SecurityLevel[data.security_level.value]
            
            file_upload = FileUpload(
                upload_token=str(uuid.uuid4()),
                file_name=data.file_name,
                file_type=data.file_type,
                file_size=data.file_size,
                file_path=file_path,
                file_hash=file_hash,
                uploaded_by_id=data.uploaded_by_id,
                department_id=data.department_id,
                is_department_only=data.is_department_only,
                security_level=security_level,
                file_purpose=data.file_purpose,
                field_selection=json.dumps(data.field_selection) if data.field_selection else None,
            )
            
            self.session.add(file_upload)
            await self.session.flush()
            
            logger.info(
                f"Created upload: {data.file_name} "
                f"(size={data.file_size}, security={security_level.name}, dept={data.department_id})"
            )
            return file_upload
        
        except Exception as e:
            logger.error(f"Failed to create upload for {data.file_name}: {e}")
            raise
    
    async def create_upload(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        file_size: int,
        file_hash: str,
        uploaded_by_id: int,
        security_level: SecurityLevel = SecurityLevel.GENERAL,
        file_purpose: Optional[str] = None,
        field_selection: Optional[List[str]] = None,
        department_id: Optional[int] = None,
        is_department_only: bool = False,
    ) -> FileUpload:
        """
        Create file upload record (for programmatic use).
        For frontend forms, use create_from_form() instead.
        
        Args:
            file_path: Full file path
            file_name: Original filename
            file_type: Extension (pdf, txt, csv, etc)
            file_size: Size in bytes
            file_hash: SHA-256 hash of file
            uploaded_by_id: Uploader user ID
            security_level: Security classification
            file_purpose: Optional purpose/description
            field_selection: Optional fields to extract
            department_id: Optional department ID
            is_department_only: If True, only department can access
        
        Returns:
            FileUpload record
        """
        try:
            file_upload = FileUpload(
                upload_token=str(uuid.uuid4()),
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_path=file_path,
                file_hash=file_hash,
                uploaded_by_id=uploaded_by_id,
                department_id=department_id,
                is_department_only=is_department_only,
                security_level=security_level,
                file_purpose=file_purpose,
                field_selection=json.dumps(field_selection) if field_selection else None,
            )
            
            self.session.add(file_upload)
            await self.session.flush()
            
            logger.info(f"Created upload: {file_name} (size={file_size}, security={security_level.name})")
            return file_upload
        
        except Exception as e:
            logger.error(f"Failed to create upload for {file_name}: {e}")
            raise
    
    async def get_file(self, file_id: int) -> Optional[FileUpload]:
        """Get file by ID."""
        result = await self.session.execute(
            select(FileUpload).where(FileUpload.id == file_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_token(self, token: str) -> Optional[FileUpload]:
        """Get file by upload token."""
        result = await self.session.execute(
            select(FileUpload).where(FileUpload.upload_token == token)
        )
        return result.scalar_one_or_none()
    
    async def approve(
        self,
        file_id: int,
        approved_by_id: int,
        reason: str = ""
    ) -> FileUpload:
        """Approve file for processing."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        if file_upload.status != FileStatus.PENDING:
            raise ValueError(f"File not pending (status={file_upload.status.name})")
        
        file_upload.mark_approved(approved_by_id, reason)
        await self.session.flush()
        
        logger.info(f"Approved: {file_upload.file_name}")
        return file_upload
    
    async def approve_and_ingest(
        self,
        file_id: int,
        approved_by_id: int,
        reason: str = ""
    ) -> Dict:
        """
        Approve file and trigger ingestion job.
        
        Returns:
            Dict with keys:
            - success: bool
            - file_upload: FileUpload object
            - job_id: int (if job created successfully)
            - message: str
            - warning: Optional[str] (if job creation failed)
            - error: Optional[str] (if approval failed)
        """
        try:
            # Approve the file
            file_upload = await self.approve(file_id, approved_by_id, reason)
            
            # Trigger ingestion job
            try:
                from app.models.job import JobType
                from app.jobs.integration import JobQueueIntegration
                from app.core.database import get_session_factory
                
                session_factory = get_session_factory()
                job_integration = JobQueueIntegration(session_factory)
                
                job = await job_integration.create_and_schedule(
                    job_type=JobType.FILE_INGESTION,
                    reference_id=file_id,
                    reference_type="file_upload",
                    handler=job_integration._handle_file_ingestion,
                    payload={"file_id": file_id},
                    max_retries=2
                )
                
                logger.info(f"Created ingestion job {job.id} for file {file_id}")
                
                return {
                    "success": True,
                    "file_upload": file_upload,
                    "job_id": job.id,
                    "message": "File approved and ingestion started"
                }
            
            except Exception as job_err:
                logger.error(f"Failed to create ingestion job for file {file_id}: {job_err}")
                # File is approved, but job creation failed
                # Return partial success - admin can manually trigger ingestion later
                return {
                    "success": True,
                    "file_upload": file_upload,
                    "message": "File approved",
                    "warning": "Ingestion job creation failed - manual ingestion may be needed"
                }
        
        except Exception as e:
            logger.error(f"Approval failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def trigger_ingestion(self, file_id: int, triggered_by_admin_id: int) -> Dict:
        """
        Manually trigger ingestion for an approved file.
        
        Returns:
            Dict with keys:
            - success: bool
            - job_id: int (if job created successfully)
            - message: str
            - error: Optional[str] (if failed)
        """
        try:
            # Verify file exists and is approved
            file_upload = await self.get_file(file_id)
            if not file_upload:
                return {"success": False, "error": "File not found"}
            
            if file_upload.status != FileStatus.APPROVED:
                return {
                    "success": False,
                    "error": f"File status is {file_upload.status.value}. Only APPROVED files can be ingested."
                }
            
            logger.info(f"Admin {triggered_by_admin_id} triggered manual ingestion for file {file_id}")
            
            # Create and schedule ingestion job
            try:
                from app.models.job import JobType
                from app.jobs.integration import JobQueueIntegration
                from app.core.database import get_session_factory
                
                session_factory = get_session_factory()
                job_integration = JobQueueIntegration(session_factory)
                
                job = await job_integration.create_and_schedule(
                    job_type=JobType.FILE_INGESTION,
                    reference_id=file_id,
                    reference_type="file_upload",
                    handler=job_integration._handle_file_ingestion,
                    payload={
                        "file_id": file_id,
                        "triggered_by": "manual",
                        "triggered_by_admin_id": triggered_by_admin_id
                    },
                    max_retries=2
                )
                
                logger.info(f"Created ingestion job {job.id} for file {file_id}")
                
                return {
                    "success": True,
                    "job_id": job.id,
                    "message": f"Ingestion job created (job_id={job.id})"
                }
            
            except Exception as job_err:
                logger.error(f"Failed to create ingestion job for file {file_id}: {job_err}")
                return {
                    "success": False,
                    "error": f"Failed to create ingestion job: {str(job_err)}"
                }
        
        except Exception as e:
            logger.error(f"Error triggering ingestion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reject(
        self,
        file_id: int,
        rejected_by_id: int,
        reason: str = ""
    ) -> FileUpload:
        """Reject file from processing."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        if file_upload.status != FileStatus.PENDING:
            raise ValueError(f"File not pending (status={file_upload.status.name})")
        
        file_upload.mark_rejected(rejected_by_id, reason)
        await self.session.flush()
        
        logger.info(f"Rejected: {file_upload.file_name}")
        return file_upload
    
    async def mark_processed(
        self,
        file_id: int,
        chunks_created: int,
        processing_time_ms: int,
    ) -> FileUpload:
        """Mark file as successfully processed."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        file_upload.mark_processed(chunks_created, processing_time_ms)
        await self.session.flush()
        
        logger.info(f"Processed: {file_upload.file_name} (chunks={chunks_created}, time={processing_time_ms}ms)")
        return file_upload
    
    async def mark_failed(self, file_id: int, error: str) -> FileUpload:
        """Mark file processing as failed."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        file_upload.mark_failed(error)
        await self.session.flush()
        
        status = "will retry" if file_upload.can_retry() else "max retries exceeded"
        logger.error(f"Failed: {file_upload.file_name} ({status}): {error}")
        return file_upload
    
    async def get_pending_approval(self, limit: int = 50) -> List[FileUpload]:
        """Get files awaiting approval."""
        result = await self.session.execute(
            select(FileUpload)
            .where(FileUpload.status == FileStatus.PENDING)
            .order_by(FileUpload.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_approved_files(self, limit: int = 50) -> List[FileUpload]:
        """Get approved files ready for processing."""
        result = await self.session.execute(
            select(FileUpload)
            .where(FileUpload.status == FileStatus.APPROVED)
            .order_by(FileUpload.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_user(self, user_id: int, limit: int = 100) -> List[FileUpload]:
        """Get files uploaded by user."""
        result = await self.session.execute(
            select(FileUpload)
            .where(FileUpload.uploaded_by_id == user_id)
            .order_by(FileUpload.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def delete(self, file_id: int) -> FileUpload:
        """Mark file as deleted in database."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        file_upload.status = FileStatus.DELETED
        await self.session.flush()
        
        logger.info(f"Marked as deleted: {file_upload.file_name}")
        return file_upload
    
    async def get_status_counts(self) -> dict:
        """Get count of files per status."""
        counts = {}
        total_all = 0
        for status in FileStatus:
            result = await self.session.execute(
                select(func.count(FileUpload.id)).where(FileUpload.status == status)
            )
            count = result.scalar() or 0
            counts[status.value] = count
            total_all += count
        # Add total "all" count
        counts["all"] = total_all
        return counts
    
    async def get_by_status(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[FileUpload], int]:
        """Get files by status with pagination. Returns (files, total_count)."""
        if status and status != "all":
            try:
                status_enum = FileStatus(status)
                count_query = select(func.count(FileUpload.id)).where(FileUpload.status == status_enum)
                query = select(FileUpload).where(FileUpload.status == status_enum).order_by(FileUpload.created_at.desc())
            except ValueError:
                # Invalid status, return empty
                return [], 0
        else:
            count_query = select(func.count(FileUpload.id))
            query = select(FileUpload).order_by(FileUpload.created_at.desc())
        
        # Get total count efficiently
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.session.execute(
            query.limit(limit).offset(offset)
        )
        files = result.scalars().all()
        
        return files, total
    
    async def get_user_by_status(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[FileUpload], int]:
        """Get user's files by status with pagination. Returns (files, total_count)."""
        if status and status != "all":
            try:
                status_enum = FileStatus(status)
                count_query = select(func.count(FileUpload.id)).where(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == status_enum
                )
                query = select(FileUpload).where(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == status_enum
                ).order_by(FileUpload.created_at.desc())
            except ValueError:
                # Invalid status, return empty
                return [], 0
        else:
            count_query = select(func.count(FileUpload.id)).where(FileUpload.uploaded_by_id == user_id)
            query = select(FileUpload).where(FileUpload.uploaded_by_id == user_id).order_by(FileUpload.created_at.desc())
        
        # Get total count efficiently
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.session.execute(
            query.limit(limit).offset(offset)
        )
        files = result.scalars().all()
        
        return files, total
    
    async def get_user_status_counts(self, user_id: int) -> dict:
        """Get status counts for a specific user's files."""
        from app.models.file_upload import FileStatus
        
        counts = {}
        total_user_files = 0
        
        for s in FileStatus:
            result = await self.session.execute(
                select(func.count(FileUpload.id)).where(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == s
                )
            )
            count = result.scalar() or 0
            counts[s.value] = count
            total_user_files += count
        
        counts["all"] = total_user_files
        return counts
    
    async def get_file_with_uploaders(
        self,
        files: List[FileUpload]
    ) -> dict:
        """
        Enrich file list with uploader information (for admin views).
        
        Args:
            files: List of FileUpload objects
        
        Returns:
            Dictionary mapping uploader IDs to user info
        """
        from app.models.user import User
        
        uploader_ids = [f.uploaded_by_id for f in files if f.uploaded_by_id]
        uploader_map = {}
        
        if uploader_ids:
            uploader_stmt = select(User).where(User.id.in_(uploader_ids))
            uploader_result = await self.session.execute(uploader_stmt)
            uploaders = uploader_result.scalars().all()
            
            uploader_map = {
                u.id: {
                    "full_name": u.full_name or f"User #{u.id}",
                    "department_name": u.department.name if u.department else None
                }
                for u in uploaders
            }
        
        return uploader_map
    
    async def get_file_content(
        self,
        file_id: int,
        user_id: int,
        is_admin: bool
    ) -> dict:
        """
        Retrieve file content with support for DOCX conversion.
        
        Args:
            file_id: File upload ID
            user_id: Current user ID
            is_admin: Whether user is admin
        
        Returns:
            Dict with success status, content, filename, file_type
        """
        import os
        from docx2html import convert
        
        # Get file record
        file_record = await self.get_file(file_id)
        if not file_record:
            return {"success": False, "error": "File not found"}
        
        # Check authorization
        is_owner = file_record.uploaded_by_id == user_id
        if not (is_owner or is_admin):
            return {"success": False, "error": "Access denied"}
        
        try:
            # Resolve file path
            base_dir = os.getenv("FILES_DIR", "data/files")
            full_path = os.path.join(base_dir, file_record.file_path)
            
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
                        "file_type": "html"
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
                
                logger.info(f"Retrieved file content for file_id={file_id}, user_id={user_id}")
                
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
    
    async def delete_file_secure(
        self,
        file_id: int,
        user_id: int,
        is_admin: bool
    ) -> dict:
        """
        Securely delete file with permission checks.
        
        Args:
            file_id: File upload ID
            user_id: Current user ID
            is_admin: Whether user is admin
        
        Returns:
            Dict with success status and message/error
        """
        from app.storage.file_storage import FileStorage
        
        # Get file record
        file_record = await self.get_file(file_id)
        if not file_record:
            return {"success": False, "error": "File not found"}
        
        # Check permissions: owner or admin
        if file_record.uploaded_by_id != user_id and not is_admin:
            return {"success": False, "error": "Permission denied"}
        
        try:
            # Delete physical file from disk
            storage = FileStorage()
            await storage.delete_file(file_record.file_path)
            
            # Mark as deleted in database
            await self.delete(file_id)
            
            logger.info(f"File {file_id} deleted by user {user_id}")
            
            return {
                "success": True,
                "message": "File deleted"
            }
        except Exception as e:
            logger.error(f"Delete file failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
