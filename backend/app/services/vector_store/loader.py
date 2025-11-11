"""
Document Loader - Loads documents from FileUpload model with metadata enrichment.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import csv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.core import get_logger
from app.models.file_upload import FileUpload, FileStatus, SecurityLevel
from app.models.department import Department


logger = get_logger(__name__)


class DocumentLoader:
    """Loads documents from FileUpload model with enriched metadata."""
    
    def __init__(self, session: AsyncSession):
        """Initialize loader with database session."""
        self.session = session
    
    async def load_pending_files(self) -> List[Dict[str, Any]]:
        """
        Load pending approved files from database with enriched metadata.
        
        Returns:
            List of documents with content and metadata
        """
        logger.info("Loading pending approved files from database")
        
        # Query pending approved files
        stmt = select(FileUpload).where(
            (FileUpload.status == FileStatus.APPROVED) &
            (FileUpload.is_processed == False)
        ).order_by(FileUpload.created_at)
        
        result = await self.session.execute(stmt)
        file_uploads = result.scalars().all()
        
        logger.info(f"Found {len(file_uploads)} pending files")
        
        documents = []
        for file_upload in file_uploads:
            try:
                # Load and enrich document
                doc = await self._load_and_enrich(file_upload)
                documents.append(doc)
                logger.info(f"✓ Loaded: {file_upload.file_name}")
            except Exception as e:
                logger.error(f"✗ Failed to load {file_upload.file_name}: {e}")
        
        logger.info(f"Successfully loaded {len(documents)} documents")
        return documents
    
    async def _load_and_enrich(self, file_upload: FileUpload) -> Dict[str, Any]:
        """Load file and enrich with metadata from model."""
        file_path = Path(file_upload.file_path)
        
        # Load file content
        content = self._load_file_content(file_path, file_upload.file_type)
        
        # Get department name if applicable
        dept_name = None
        if file_upload.department_id:
            stmt = select(Department).where(Department.id == file_upload.department_id)
            result = await self.session.execute(stmt)
            dept = result.scalar_one_or_none()
            dept_name = dept.name if dept else None
        
        # Build enriched metadata
        meta = {
            "upload_token": file_upload.upload_token,
            "file_id": file_upload.id,
            "security_level": file_upload.security_level.name,  # e.g., "GENERAL", "CONFIDENTIAL"
            "is_department_only": file_upload.is_department_only,
            "department": dept_name,
            "file_type": file_upload.file_type,
            "department_id": file_upload.department_id or None,
            "file_purpose": file_upload.file_purpose,
            "file_size_bytes": file_upload.file_size,
        }
        
        return {
            "file_id": file_upload.id,
            "file_name": file_upload.file_name,
            "file_type": file_upload.file_type,
            "content": content,
            "meta": meta,
        }
    
    def _load_file_content(self, file_path: Path, file_type: str) -> Any:
        """Load file content based on type."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_type_lower = file_type.lower()
        
        # Text-based files
        if file_type_lower in ['txt', 'md', 'markdown']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # JSON files
        elif file_type_lower == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # CSV files
        elif file_type_lower == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        # PDF files
        elif file_type_lower == 'pdf':
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
                return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load PDF: {e}")
                raise
        
        # Word documents
        elif file_type_lower in ['doc', 'docx']:
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(file_path))
                docs = loader.load()
                return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load DOCX: {e}")
                raise
        
        # Excel files
        elif file_type_lower in ['xlsx', 'xls']:
            try:
                from langchain_community.document_loaders import UnstructuredExcelLoader
                loader = UnstructuredExcelLoader(str(file_path))
                docs = loader.load()
                return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load Excel: {e}")
                raise
        
        else:
            raise ValueError(f"Unsupported file type: {file_type_lower}")

