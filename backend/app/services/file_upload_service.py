"""
FileUploadService - Manages file upload lifecycle and integration with ingestion.

Handles:
1. File upload tracking and storage
2. Approval workflow management
3. Processing lifecycle (pending → processing → processed/failed)
4. Error handling and retry logic
5. Data retention and cleanup
6. Security level enforcement
"""
import uuid
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload, FileStatus, SecurityLevel
from app.core import get_logger


logger = get_logger(__name__)


class FileUploadService:
    """Service for managing file uploads through the ingestion pipeline."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize service with database session."""
        self.db = db_session
    
    # ============================================================================
    # File Registration & Tracking
    # ============================================================================
    
    async def create_file_upload(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        file_size: int,
        uploaded_by_id: int,
        file_purpose: Optional[str] = None,
        field_selection: Optional[List[str]] = None,
        extraction_config: Optional[Dict[str, Any]] = None,
        security_level: SecurityLevel = SecurityLevel.INTERNAL,
        retention_days: Optional[int] = None,
    ) -> FileUpload:
        """
        Create a new file upload record.
        
        Args:
            file_path: Full path to the uploaded file
            file_name: Original file name
            file_type: File extension (pdf, txt, csv, etc.)
            file_size: File size in bytes
            uploaded_by_id: User ID of uploader
            file_purpose: Optional description of why file is being uploaded
            field_selection: Optional list of fields to extract from file
            extraction_config: Optional JSON config for extraction rules
            security_level: Classification level (public, internal, confidential, restricted)
            retention_days: Optional days to retain file (None = indefinite)
            
        Returns:
            FileUpload record
        """
        try:
            # Calculate file hash for deduplication
            file_hash = await self._calculate_file_hash(file_path)
            
            # Check for duplicate file (same hash, same security level)
            existing = await self.get_file_by_hash(file_hash, security_level)
            if existing:
                logger.warning(
                    f"Duplicate file detected: {file_name} "
                    f"(matches {existing.file_name}, hash={file_hash})"
                )
            
            # Generate unique upload token
            upload_token = str(uuid.uuid4())
            
            # Calculate retention date
            retention_until = None
            if retention_days:
                retention_until = datetime.now(timezone.utc) + timedelta(days=retention_days)
            
            # Convert field_selection list to JSON if provided
            field_selection_json = json.dumps(field_selection) if field_selection else None
            extraction_config_json = json.dumps(extraction_config) if extraction_config else None
            
            file_upload = FileUpload(
                upload_token=upload_token,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_path=file_path,
                file_hash=file_hash,
                uploaded_by_id=uploaded_by_id,
                file_purpose=file_purpose,
                field_selection=field_selection_json,
                extraction_config=extraction_config_json,
                security_level=security_level,
                retention_until=retention_until,
            )
            
            self.db.add(file_upload)
            await self.db.flush()
            
            logger.info(
                f"Created file upload: {file_name} "
                f"(token={upload_token}, size={file_size}, security={security_level.value})"
            )
            
            return file_upload
        
        except Exception as e:
            logger.error(f"Failed to create file upload for {file_name}: {e}")
            raise
    
    # ============================================================================
    # Approval Workflow
    # ============================================================================
    
    async def approve_file(
        self,
        file_upload_id: int,
        approved_by_id: int,
        reason: str = ""
    ) -> FileUpload:
        """
        Approve a file for processing.
        
        Args:
            file_upload_id: FileUpload record ID
            approved_by_id: User ID of approver
            reason: Optional approval reason/notes
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        if not file_upload.is_awaiting_approval():
            raise ValueError(f"File is not awaiting approval (status={file_upload.status.value})")
        
        file_upload.mark_approved(approved_by_id, reason)
        await self.db.flush()
        
        logger.info(
            f"Approved file: {file_upload.file_name} "
            f"(approved_by={approved_by_id}, reason={reason})"
        )
        
        return file_upload
    
    async def reject_file(
        self,
        file_upload_id: int,
        rejected_by_id: int,
        reason: str = ""
    ) -> FileUpload:
        """
        Reject a file from processing.
        
        Args:
            file_upload_id: FileUpload record ID
            rejected_by_id: User ID of rejector
            reason: Optional rejection reason
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        if not file_upload.is_awaiting_approval():
            raise ValueError(f"File is not awaiting approval (status={file_upload.status.value})")
        
        file_upload.mark_rejected(rejected_by_id, reason)
        await self.db.flush()
        
        logger.info(f"Rejected file: {file_upload.file_name} (reason={reason})")
        
        return file_upload
    
    # ============================================================================
    # Processing Lifecycle
    # ============================================================================
    
    async def start_processing(self, file_upload_id: int) -> FileUpload:
        """
        Mark file as currently being processed.
        
        Args:
            file_upload_id: FileUpload record ID
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        if not file_upload.is_approved():
            raise ValueError(f"File must be approved before processing (status={file_upload.status.value})")
        
        file_upload.mark_processing()
        await self.db.flush()
        
        logger.info(f"Started processing: {file_upload.file_name}")
        
        return file_upload
    
    async def mark_processing_complete(
        self,
        file_upload_id: int,
        chunks_created: int,
        processing_time_ms: int
    ) -> FileUpload:
        """
        Mark file as successfully processed.
        
        Args:
            file_upload_id: FileUpload record ID
            chunks_created: Number of chunks created from file
            processing_time_ms: Time taken to process (milliseconds)
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        file_upload.mark_processed(chunks_created, processing_time_ms)
        await self.db.flush()
        
        logger.info(
            f"Completed processing: {file_upload.file_name} "
            f"(chunks={chunks_created}, time={processing_time_ms}ms)"
        )
        
        return file_upload
    
    async def mark_processing_failed(
        self,
        file_upload_id: int,
        error: str
    ) -> FileUpload:
        """
        Mark file processing as failed.
        
        If retry count < max_retries, status reverts to PENDING for retry.
        If retry count >= max_retries, status becomes FAILED.
        
        Args:
            file_upload_id: FileUpload record ID
            error: Error message
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        file_upload.mark_failed(error)
        await self.db.flush()
        
        if file_upload.can_retry():
            logger.warning(
                f"Processing failed (will retry): {file_upload.file_name} "
                f"(retry {file_upload.retry_count}/{file_upload.max_retries}): {error}"
            )
        else:
            logger.error(
                f"Processing failed permanently: {file_upload.file_name} "
                f"(max retries exceeded): {error}"
            )
        
        return file_upload
    
    # ============================================================================
    # Queries & Retrieval
    # ============================================================================
    
    async def get_file_upload(self, file_upload_id: int) -> Optional[FileUpload]:
        """Get a file upload record by ID."""
        result = await self.db.execute(
            select(FileUpload).where(FileUpload.id == file_upload_id)
        )
        return result.scalar_one_or_none()
    
    async def get_file_by_token(self, upload_token: str) -> Optional[FileUpload]:
        """Get a file upload record by upload token."""
        result = await self.db.execute(
            select(FileUpload).where(FileUpload.upload_token == upload_token)
        )
        return result.scalar_one_or_none()
    
    async def get_file_by_hash(
        self,
        file_hash: str,
        security_level: SecurityLevel
    ) -> Optional[FileUpload]:
        """Get a file by hash and security level (for duplicate detection)."""
        result = await self.db.execute(
            select(FileUpload).where(
                and_(
                    FileUpload.file_hash == file_hash,
                    FileUpload.security_level == security_level,
                    FileUpload.status != FileStatus.DELETED,
                )
            ).order_by(FileUpload.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_pending_approvals(self, limit: int = 50) -> List[FileUpload]:
        """Get files awaiting approval."""
        result = await self.db.execute(
            select(FileUpload)
            .where(FileUpload.status == FileStatus.PENDING)
            .order_by(FileUpload.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_approved_pending_processing(self, limit: int = 50) -> List[FileUpload]:
        """Get approved files ready for processing."""
        result = await self.db.execute(
            select(FileUpload)
            .where(FileUpload.status == FileStatus.APPROVED)
            .order_by(FileUpload.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_failed_retryable(self, limit: int = 50) -> List[FileUpload]:
        """Get failed files that can be retried."""
        result = await self.db.execute(
            select(FileUpload)
            .where(
                and_(
                    FileUpload.status.in_([FileStatus.PENDING, FileStatus.FAILED]),
                    FileUpload.retry_count < FileUpload.max_retries,
                )
            )
            .order_by(FileUpload.updated_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_user(
        self,
        user_id: int,
        status: Optional[FileStatus] = None,
        limit: int = 100
    ) -> List[FileUpload]:
        """Get file uploads by user."""
        query = select(FileUpload).where(FileUpload.uploaded_by_id == user_id)
        
        if status:
            query = query.where(FileUpload.status == status)
        
        result = await self.db.execute(
            query.order_by(FileUpload.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
    
    # ============================================================================
    # Data Retention & Cleanup
    # ============================================================================
    
    async def get_expired_files(self, limit: int = 100) -> List[FileUpload]:
        """Get files that have exceeded retention period."""
        result = await self.db.execute(
            select(FileUpload)
            .where(
                and_(
                    FileUpload.retention_until.isnot(None),
                    FileUpload.retention_until < datetime.now(timezone.utc),
                    FileUpload.status != FileStatus.DELETED,
                )
            )
            .order_by(FileUpload.retention_until.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def archive_file(self, file_upload_id: int) -> FileUpload:
        """Mark file as archived (for long-term storage)."""
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        file_upload.is_archived = True
        file_upload.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        logger.info(f"Archived file: {file_upload.file_name}")
        return file_upload
    
    async def delete_file(
        self,
        file_upload_id: int,
        delete_physical_file: bool = True
    ) -> FileUpload:
        """
        Mark file as deleted and optionally remove physical file.
        
        Args:
            file_upload_id: FileUpload record ID
            delete_physical_file: Whether to also delete the physical file from disk
            
        Returns:
            Updated FileUpload record
        """
        file_upload = await self.get_file_upload(file_upload_id)
        if not file_upload:
            raise ValueError(f"FileUpload not found: {file_upload_id}")
        
        file_upload.status = FileStatus.DELETED
        file_upload.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        # Delete physical file if requested
        if delete_physical_file:
            try:
                path = Path(file_upload.file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"Deleted physical file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete physical file {file_upload.file_path}: {e}")
        
        logger.info(f"Marked file as deleted: {file_upload.file_name}")
        return file_upload
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    @staticmethod
    async def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get file upload statistics."""
        # Query all statuses
        result = await self.db.execute(
            select(
                FileUpload.status,
                func.count(FileUpload.id).label('count')
            ).group_by(FileUpload.status)
        )
        
        status_counts = {row.status.value: row.count for row in result.all()}
        
        # Total statistics
        total_result = await self.db.execute(select(func.count(FileUpload.id)))
        total = total_result.scalar()
        
        return {
            "total_files": total,
            "by_status": status_counts,
            "pending_approvals": status_counts.get(FileStatus.PENDING.value, 0),
            "processed": status_counts.get(FileStatus.PROCESSED.value, 0),
            "failed": status_counts.get(FileStatus.FAILED.value, 0),
        }
