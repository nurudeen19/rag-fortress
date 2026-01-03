"""
Document ingestion flow orchestration.

Manages the document ingestion pipeline by coordinating with existing services:
- DocumentStorageService: Handles load → chunk → embed → store pipeline
- Manages file status transitions: APPROVED → PROCESSING → PROCESSED/FAILED
"""

from typing import Dict
import asyncio

from app.models.file_upload import FileUpload, FileStatus
from app.services.vector_store.storage import DocumentStorageService
from app.core import get_logger
from app.core.database import get_fresh_async_session_factory
from app.config.settings import settings

logger = get_logger(__name__)


class DocumentIngestionService:
    """Orchestrates document ingestion using existing DocumentStorageService."""
    
    def __init__(self):
        """Initialize ingestion service (session managed per operation)."""
        pass
    
    async def ingest_single_file(self, file_id: int) -> Dict:
        """
        Ingest a single approved file through the complete pipeline.
        
        Pipeline:
        1. Verify file is APPROVED
        2. Load specific file via DocumentLoader with file_id
        3. Chunk content via DocumentChunker
        4. Generate embeddings and store in vector DB
        5. Mark as PROCESSED (or FAILED on error)
        
        Args:
            file_id: ID of file to ingest
            
        Returns:
            Dict with ingestion result containing status and metadata
        """
        try:
            # Get fresh session factory bound to CURRENT event loop
            # CRITICAL: This creates a new engine for isolated event loops (background jobs)
            session_factory = await get_fresh_async_session_factory()
            
            # Create session without context manager to control lifecycle
            session = session_factory()
            
            try:
                # Get file record
                file_record = await session.get(FileUpload, file_id)
                if not file_record:
                    logger.error(f"File {file_id} not found")
                    return {"status": "error", "error": "File not found"}
                
                # Verify file is approved
                if file_record.status != FileStatus.APPROVED:
                    logger.warning(f"File {file_id} status is {file_record.status.value}, expected APPROVED")
                    return {
                        "status": "error",
                        "error": f"File status is {file_record.status.value}, not APPROVED"
                    }
                
                try:
                    # Create storage service with fresh session
                    storage_service = DocumentStorageService(session)
                    
                    # Use DocumentStorageService to process this single file only
                    # Pass file_ids parameter to load and process only this file
                    result = await storage_service.ingest_pending_files(
                        batch_size=settings.CHUNK_INGESTION_BATCH_SIZE,
                        file_ids=[file_id]
                    )
                    
                    logger.info(f"File {file_id} ingestion completed: {result}")
                    
                    # Return success - storage service already updated file status
                    return {
                        "status": "success",
                        "file_id": file_id,
                        "chunks_created": result.get("chunks_generated", 0),
                        "message": result.get("message", "File ingestion completed")
                    }
                
                except Exception as pipeline_err:
                    logger.error(f"Pipeline error processing file {file_id}: {pipeline_err}", exc_info=True)
                    
                    # Mark as failed
                    try:
                        file_record.status = FileStatus.FAILED
                        file_record.error_message = str(pipeline_err)
                        await session.commit()
                        logger.info(f"File {file_id} marked as FAILED")
                    except Exception as update_err:
                        logger.error(f"Failed to mark file as FAILED: {update_err}")
                    
                    return {
                        "status": "error",
                        "file_id": file_id,
                        "error": str(pipeline_err)
                    }
            finally:
                # Close session in same event loop
                try:
                    await session.close()
                except Exception as close_err:
                    logger.warning(f"Error closing session: {close_err}")
        
        except Exception as e:
            logger.error(f"Unexpected error ingesting file {file_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "file_id": file_id,
                "error": str(e)
            }
    
    async def ingest_batch(self, batch_size: int = None) -> Dict:
        """
        Ingest all pending approved files in a batch.
        
        Uses DocumentStorageService.ingest_pending_files() which:
        1. Loads all APPROVED files
        2. Chunks them
        3. Stores in vector DB
        4. Updates file statuses
        
        Args:
            batch_size: Chunks per batch to vector store (default: from settings.CHUNK_INGESTION_BATCH_SIZE)
            
        Returns:
            Dict with batch ingestion results
        """
        try:
            # Use configurable batch size from settings if not explicitly provided
            if batch_size is None:
                batch_size = settings.CHUNK_INGESTION_BATCH_SIZE
            
            logger.info(f"Starting batch ingestion with batch_size={batch_size}")
            
            # Get fresh session factory bound to CURRENT event loop
            # CRITICAL: This creates a new engine for isolated event loops (background jobs)
            session_factory = await get_fresh_async_session_factory()
            
            # Create session without context manager to control lifecycle
            session = session_factory()
            
            try:
                # Create storage service with fresh session
                storage_service = DocumentStorageService(session)
                
                # Use DocumentStorageService to process all approved files
                result = await storage_service.ingest_pending_files(batch_size=batch_size)
                
                logger.info(f"Batch ingestion complete: {result}")
                return {
                    "status": "success",
                    "files_processed": result.get("successfully_stored", 0),
                    "total_files": result.get("total_files", 0),
                    "chunks_created": result.get("chunks_generated", 0),
                    "errors": result.get("errors", []),
                    "message": f"Processed {result.get('successfully_stored', 0)} files"
                }
            finally:
                # Close session in same event loop
                try:
                    await session.close()
                except Exception as close_err:
                    logger.warning(f"Error closing session: {close_err}")
        
        except Exception as e:
            logger.error(f"Error in batch ingestion: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
