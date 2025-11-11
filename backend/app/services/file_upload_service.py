"""
FileUploadService - Manages file upload lifecycle.
Simple, focused service for file tracking and status management.
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import select
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
    
    async def create_from_form(self, data: FileUploadCreate, file_path: str) -> FileUpload:
        """
        Create file upload from form submission (recommended for frontend).
        
        Args:
            data: FileUploadCreate schema with all required fields
            file_path: Full path where file is stored
        
        Returns:
            FileUpload record
        """
        try:
            # Calculate file hash
            file_hash = await self._calculate_hash(file_path)
            
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
            # Calculate file hash
            file_hash = await self._calculate_hash(file_path)
            
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
    
    async def delete(self, file_id: int, delete_file: bool = True) -> FileUpload:
        """Delete file record and optionally physical file."""
        file_upload = await self.get_file(file_id)
        if not file_upload:
            raise ValueError(f"File not found: {file_id}")
        
        file_upload.status = FileStatus.DELETED
        await self.session.flush()
        
        if delete_file:
            try:
                path = Path(file_upload.file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"Deleted physical file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete physical file: {e}")
        
        logger.info(f"Deleted: {file_upload.file_name}")
        return file_upload
    
    @staticmethod
    async def _calculate_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
