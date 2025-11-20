"""
Document ingestion flow orchestration.

Manages the document ingestion pipeline by coordinating with existing services:
- DocumentStorageService: Handles load → chunk → embed → store pipeline
- Manages file status transitions: APPROVED → PROCESSING → PROCESSED/FAILED
"""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.file_upload import FileUpload, FileStatus
from app.services.vector_store.storage import DocumentStorageService
from app.core import get_logger

logger = get_logger(__name__)


class DocumentIngestionService:
    """Orchestrates document ingestion using existing DocumentStorageService."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize ingestion service.
        
        Args:
            session: AsyncSession for database access
        """
        self.session = session
        self.storage_service = DocumentStorageService(session)
    
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
            logger.info(f"Starting ingestion for file_id={file_id}")
            
            # Get file record
            file_record = await self.session.get(FileUpload, file_id)
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
            
            logger.info(f"File {file_id} ({file_record.file_name}) is approved, starting ingestion")
            
            try:
                # Load ONLY this specific file (not all pending files)
                from app.services.vector_store.loader import DocumentLoader
                from app.services.vector_store.chunker import DocumentChunker
                
                loader = DocumentLoader(self.session)
                chunker = DocumentChunker()
                
                # Load only this file by passing file_id
                files = await loader.load_pending_files(file_ids=[file_id])
                
                if not files:
                    raise Exception(f"Failed to load file {file_id}")
                
                logger.info(f"Loaded file {file_id}, chunking content")
                
                # Chunk the file
                chunks = chunker.chunk_loaded_files(files)
                if not chunks:
                    raise Exception(f"Failed to chunk file {file_id}")
                
                logger.info(f"Generated {len(chunks)} chunks for file {file_id}")
                
                # Store chunks in vector DB
                result = await self.storage_service._store_and_track(chunks, batch_size=100)
                file_ids, errors = result
                
                # Mark file as processed
                file_record.status = FileStatus.PROCESSED
                file_record.is_processed = True
                await self.session.commit()
                logger.info(f"File {file_id} marked as PROCESSED")
                
                # Return success
                return {
                    "status": "success",
                    "file_id": file_id,
                    "chunks_created": len(chunks),
                    "message": f"File ingestion completed"
                }
            
            except Exception as pipeline_err:
                logger.error(f"Pipeline error processing file {file_id}: {pipeline_err}", exc_info=True)
                
                # Mark as failed
                try:
                    file_record.status = FileStatus.FAILED
                    file_record.error_message = str(pipeline_err)
                    await self.session.commit()
                    logger.info(f"File {file_id} marked as FAILED")
                except Exception as update_err:
                    logger.error(f"Failed to mark file as FAILED: {update_err}")
                
                return {
                    "status": "error",
                    "file_id": file_id,
                    "error": str(pipeline_err)
                }
        
        except Exception as e:
            logger.error(f"Unexpected error ingesting file {file_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "file_id": file_id,
                "error": str(e)
            }
    
    async def ingest_batch(self, batch_size: int = 100) -> Dict:
        """
        Ingest all pending approved files in a batch.
        
        Uses DocumentStorageService.ingest_pending_files() which:
        1. Loads all APPROVED files
        2. Chunks them
        3. Stores in vector DB
        4. Updates file statuses
        
        Args:
            batch_size: Chunks per batch to vector store (default: 100)
            
        Returns:
            Dict with batch ingestion results
        """
        try:
            logger.info(f"Starting batch ingestion")
            
            # Use DocumentStorageService to process all approved files
            result = await self.storage_service.ingest_pending_files(batch_size=batch_size)
            
            logger.info(f"Batch ingestion complete: {result}")
            return {
                "status": "success",
                "files_processed": result.get("successfully_stored", 0),
                "total_files": result.get("total_files", 0),
                "chunks_created": result.get("chunks_generated", 0),
                "errors": result.get("errors", []),
                "message": f"Processed {result.get('successfully_stored', 0)} files"
            }
        
        except Exception as e:
            logger.error(f"Error in batch ingestion: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
