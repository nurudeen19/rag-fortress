"""
Document Storage Service - Orchestrates load → chunk → store pipeline.
Manages ingestion from FileUpload model through vector store.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.services.vector_store.loader import DocumentLoader
from app.services.vector_store.chunker import DocumentChunker
from app.core.vector_store_factory import get_vector_store
from app.core.embedding_factory import get_embedding_provider
from app.models.file_upload import FileUpload, FileStatus
from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentStorageService:
    """
    Orchestrates load → chunk → store pipeline.
    
    Flow:
    1. Load approved files from FileUpload model
    2. Chunk documents using DocumentChunker
    3. Store chunks in vector DB with batching
    4. Update file statuses (PROCESSED or FAILED)
    """
    
    def __init__(self, session: AsyncSession, embeddings: Embeddings = None):
        """
        Initialize storage service.
        
        Args:
            session: AsyncSession for database operations
            embeddings: Pre-initialized embeddings (optional)
        """
        self.session = session
        self.embeddings = embeddings or get_embedding_provider()
        self.loader = DocumentLoader(session)
        self.chunker = DocumentChunker()
        self.vector_store = get_vector_store(
            embeddings=self.embeddings,
            provider=settings.VECTOR_DB_PROVIDER,
        )
        logger.info("DocumentStorageService initialized")
    
    async def ingest_pending_files(self, batch_size: int = 100, file_ids: List[int] = None) -> Dict[str, Any]:
        """
        Load, chunk, and store pending approved files or specific files.
        
        Args:
            batch_size: Chunks per batch to vector store (default: 100)
            file_ids: Optional list of specific file IDs to ingest.
                     If provided, only those files are processed.
                     If None, all approved unprocessed files are ingested.
        
        Returns:
            Dict with counts: total_files, successfully_stored, chunks_generated, errors
        """
        logger.info(f"Starting ingestion pipeline (file_ids={file_ids})")
        
        # Step 1: Load files from database
        # Pass file_ids to loader - if provided, only those are loaded
        files = await self.loader.load_pending_files(file_ids=file_ids)
        if not files:
            logger.info("No pending files to process")
            return {"total_files": 0, "successfully_stored": 0, "chunks_generated": 0, "errors": []}
        
        logger.info(f"Loaded {len(files)} files")
        
        # Step 2: Chunk files
        chunks = self.chunker.chunk_loaded_files(files)
        if not chunks:
            logger.warning("No chunks generated from files")
            return {"total_files": len(files), "successfully_stored": 0, "chunks_generated": 0, "errors": []}
        
        logger.info(f"Generated {len(chunks)} chunks")
        
        # Step 3: Store chunks in vector DB
        file_ids_result, errors = await self._store_and_track(chunks, batch_size)
        
        # Step 4: Update file statuses
        await self._update_file_statuses(files, file_ids_result, errors)
        
        successfully_stored = len([fid for fid in file_ids_result if fid not in errors])
        logger.info(f"Ingestion complete: {successfully_stored}/{len(files)} files processed")
        
        return {
            "total_files": len(files),
            "successfully_stored": successfully_stored,
            "chunks_generated": len(chunks),
            "errors": errors,
        }
    
    async def _store_and_track(self, chunks: List[Document], batch_size: int) -> Tuple[set, Dict]:
        """
        Store chunks in vector DB with batching and track results.
        
        Returns:
            Tuple of (set of successful file_ids, dict of error file_ids)
        """
        successful_file_ids = set()
        error_file_ids = {}
        
        # Group chunks by file_id
        chunks_by_file: Dict[int, List[Document]] = {}
        for chunk in chunks:
            file_id = chunk.metadata.get("file_id")
            if file_id not in chunks_by_file:
                chunks_by_file[file_id] = []
            chunks_by_file[file_id].append(chunk)
        
        # Store in batches and track success/failure per file
        all_file_chunks = []
        for file_id, file_chunks in chunks_by_file.items():
            all_file_chunks.extend(file_chunks)
        
        for i in range(0, len(all_file_chunks), batch_size):
            batch = all_file_chunks[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                self.vector_store.add_documents(batch)
                
                # Mark files in this batch as successful
                for chunk in batch:
                    file_id = chunk.metadata.get("file_id")
                    if file_id:
                        successful_file_ids.add(file_id)
                
                logger.info(f"✓ Stored batch {batch_num}: {len(batch)} chunks")
            except Exception as e:
                logger.error(f"✗ Failed storing batch {batch_num}: {e}")
                
                # Mark files in failed batch with error
                for chunk in batch:
                    file_id = chunk.metadata.get("file_id")
                    if file_id:
                        error_file_ids[file_id] = str(e)
        
        return successful_file_ids, error_file_ids
    
    async def _update_file_statuses(
        self, 
        files: List[Dict[str, Any]], 
        successful_file_ids: set, 
        error_file_ids: Dict[int, str]
    ) -> None:
        """Update FileUpload statuses in database after storage."""
        for file_data in files:
            file_id = file_data.get("file_id")
            
            try:
                # Fetch file from DB
                stmt = select(FileUpload).where(FileUpload.id == file_id)
                result = await self.session.execute(stmt)
                file_upload = result.scalar_one_or_none()
                
                if not file_upload:
                    logger.warning(f"File {file_id} not found in database")
                    continue
                
                # Update status
                if file_id in successful_file_ids:
                    file_upload.status = FileStatus.PROCESSED
                    file_upload.is_processed = True
                    file_upload.processing_completed_at = datetime.now(timezone.utc)
                    logger.info(f"✓ Marked {file_data.get('file_name')} as PROCESSED")
                
                elif file_id in error_file_ids:
                    file_upload.status = FileStatus.FAILED
                    file_upload.processing_error = error_file_ids[file_id]
                    logger.error(f"✗ Marked {file_data.get('file_name')} as FAILED: {error_file_ids[file_id]}")
                
                await self.session.commit()
            
            except Exception as e:
                logger.error(f"Failed updating status for file {file_id}: {e}")
                await self.session.rollback()
