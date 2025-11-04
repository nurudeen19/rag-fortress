"""
Document Storage Service - Orchestrates load → chunk → store pipeline.
Simple, clean, leverages LangChain patterns.
"""

from typing import List, Optional
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.services.vector_store.loader import DocumentLoader
from app.services.vector_store.chunker import DocumentChunker
from app.core.vector_store_factory import get_vector_store
from app.core.embedding_factory import get_embedding_provider
from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class IngestionResult:
    """Result of document ingestion."""
    def __init__(self, success: bool, document_path: str, chunks_count: int = 0, error: str = None):
        self.success = success
        self.document_path = document_path
        self.chunks_count = chunks_count
        self.error = error


class DocumentStorageService:
    """
    Simplified document storage using LangChain patterns.
    
    Flow:
    1. Load documents (DocumentLoader)
    2. Chunk documents (DocumentChunker)  
    3. Store with embeddings (VectorStore.from_documents or add_documents)
    4. Move to processed/
    
    Clean, simple, leverages LangChain's built-in capabilities.
    """
    
    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_store_provider: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize storage service.
        
        Args:
            embeddings: Pre-initialized embeddings (from startup). If None, will get from factory.
            vector_store_provider: Override provider
            collection_name: Override collection name
        """
        # Use pre-initialized embeddings from startup
        self.embeddings = embeddings or get_embedding_provider()
        
        # Components
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        
        # Directories
        self.pending_dir = Path(settings.PENDING_DIR)
        self.processed_dir = Path(settings.PROCESSED_DIR)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Vector store config
        self.provider = vector_store_provider or settings.VECTOR_DB_PROVIDER
        self.collection_name = collection_name
        
        # Get or create vector store (reuses existing if available)
        self.vector_store = get_vector_store(
            embeddings=self.embeddings,
            provider=self.provider,
            collection_name=self.collection_name
        )
        
        logger.info("DocumentStorageService initialized")
    
    def _move_to_processed(self, file_path: Path) -> None:
        """Move file from pending/ to processed/."""
        try:
            relative_path = file_path.relative_to(self.pending_dir)
            target_path = self.processed_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.rename(target_path)
            logger.debug(f"Moved to processed: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to move {file_path}: {e}")
            raise
    
    def ingest_from_pending(
        self,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents from pending directory.
        
        Simple 3-step process:
        1. Load documents
        2. Chunk documents
        3. Store in vector DB (LangChain handles embedding + storage)
        
        Args:
            recursive: Search subdirectories
            file_types: Filter by file extensions
            
        Returns:
            List of ingestion results
        """
        results = []
        
        # Step 1: Load documents
        logger.info("=" * 60)
        logger.info("Starting document ingestion")
        logger.info("=" * 60)
        
        documents = self.loader.load_from_pending(
            recursive=recursive,
            file_types=file_types
        )
        
        if not documents:
            logger.info("No documents to process")
            return results
        
        # Group documents by source file for processing
        docs_by_file = {}
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            if source not in docs_by_file:
                docs_by_file[source] = []
            docs_by_file[source].append(doc)
        
        logger.info(f"Processing {len(docs_by_file)} files")
        
        # Process each file
        for source_path, docs in docs_by_file.items():
            try:
                file_path = Path(source_path)
                logger.info(f"\nProcessing: {file_path.name}")
                
                # Step 2: Chunk documents
                chunks = self.chunker.chunk_documents(docs)
                
                if not chunks:
                    logger.warning(f"No chunks generated for {file_path.name}")
                    results.append(IngestionResult(
                        success=False,
                        document_path=source_path,
                        error="No chunks generated"
                    ))
                    continue
                
                # Step 3: Store in vector DB
                # LangChain handles:
                # - Embedding generation for each chunk
                # - Batch processing
                # - Vector storage with metadata
                logger.info(f"Storing {len(chunks)} chunks in vector DB...")
                self.vector_store.add_documents(chunks)
                
                logger.info(f"✓ Successfully stored {file_path.name}")
                
                # Move to processed
                self._move_to_processed(file_path)
                
                results.append(IngestionResult(
                    success=True,
                    document_path=source_path,
                    chunks_count=len(chunks)
                ))
            
            except Exception as e:
                logger.error(f"✗ Failed to process {source_path}: {e}", exc_info=True)
                results.append(IngestionResult(
                    success=False,
                    document_path=source_path,
                    error=str(e)
                ))
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total_chunks = sum(r.chunks_count for r in results if r.success)
        
        logger.info("=" * 60)
        logger.info(f"Ingestion complete:")
        logger.info(f"  Files: {successful}/{len(results)}")
        logger.info(f"  Chunks: {total_chunks}")
        logger.info("=" * 60)
        
        return results
