"""
Simplified Document Ingestion Service.
Follows LangChain patterns: Load → Chunk → Pass to VectorStore.from_documents()
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain_core.documents import Document

from app.services.document_loader import DocumentLoader
from app.services.chunking import DocumentChunker
from app.core.embedding_factory import get_embedding_provider
from app.services.vector_store.factory import get_vector_store_langchain
from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class IngestionResult:
    """Result of document ingestion."""
    def __init__(
        self,
        success: bool,
        document_path: str,
        chunks_count: int = 0,
        error_message: str = None
    ):
        self.success = success
        self.document_path = document_path
        self.chunks_count = chunks_count
        self.error_message = error_message
    
    def __repr__(self):
        if self.success:
            return f"IngestionResult(✓ {self.document_path}: {self.chunks_count} chunks)"
        return f"IngestionResult(✗ {self.document_path}: {self.error_message})"


class DocumentIngestionService:
    """
    Simplified document ingestion using LangChain patterns.
    
    Flow:
    1. Load documents from pending directory (DocumentLoader)
    2. Chunk documents (DocumentChunker)
    3. Pass to VectorStore.from_documents() - LangChain handles the rest
    4. Move to processed directory
    
    The vector store provider handles:
    - Embedding generation
    - Vector storage
    - Collection management
    """
    
    def __init__(
        self,
        vector_store_provider: str = None,
        collection_name: str = None
    ):
        """
        Initialize ingestion service.
        
        Args:
            vector_store_provider: Override vector store provider
            collection_name: Override collection name
        """
        # Components
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        
        # Directories
        self.pending_dir = Path(settings.PENDING_DIR)
        self.processed_dir = Path(settings.PROCESSED_DIR)
        
        # Ensure directories exist
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Store config for lazy initialization
        self.vector_store_provider = vector_store_provider or settings.VECTOR_DB_PROVIDER
        self.collection_name = collection_name
        
        self._initialized = False
        self.vector_store = None
        self.embeddings = None
    
    async def initialize(self) -> None:
        """Initialize embedding provider and vector store."""
        if self._initialized:
            return
        
        logger.info("Initializing ingestion service...")
        
        # Get embedding provider
        self.embeddings = get_embedding_provider()
        logger.info("✓ Embedding provider ready")
        
        # Get LangChain-compatible vector store
        self.vector_store = get_vector_store_langchain(
            provider=self.vector_store_provider,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        logger.info(f"✓ Vector store ready: {self.vector_store_provider}")
        
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        logger.info("Ingestion service cleaned up")
    
    def _move_to_processed(self, file_path: Path) -> None:
        """
        Move file from pending to processed directory.
        Preserves subdirectory structure.
        """
        try:
            # Calculate relative path from pending directory
            relative_path = file_path.relative_to(self.pending_dir)
            
            # Create target path in processed directory
            target_path = self.processed_dir / relative_path
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            file_path.rename(target_path)
            logger.info(f"Moved to processed: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Failed to move file {file_path}: {e}")
            raise
    
    async def ingest_from_pending(
        self,
        recursive: bool = True,
        file_types: List[str] = None,
        fields_to_keep: Optional[List[str]] = None,
        json_flatten: bool = True
    ) -> List[IngestionResult]:
        """
        Ingest all documents from pending directory using LangChain pattern.
        
        Args:
            recursive: Search subdirectories
            file_types: File extensions to process
            fields_to_keep: Fields to keep for structured data (JSON, CSV, XLSX)
            json_flatten: Flatten nested JSON
            
        Returns:
            List of ingestion results
        """
        if not self._initialized:
            await self.initialize()
        
        results = []
        
        # Step 1: Load documents from pending directory
        logger.info("Loading documents from pending directory...")
        loaded_docs = self.loader.load_all(
            recursive=recursive,
            file_types=file_types
        )
        
        if not loaded_docs:
            logger.info("No documents found in pending directory")
            return results
        
        logger.info(f"Found {len(loaded_docs)} documents to process")
        
        # Process each document
        for doc in loaded_docs:
            try:
                doc_path = Path(doc.metadata.get("source", "unknown"))
                logger.info(f"Processing: {doc_path.name}")
                
                # Step 2: Chunk the document
                chunks = self.chunker.chunk_document(
                    doc,
                    fields_to_keep=fields_to_keep,
                    json_flatten=json_flatten
                )
                
                if not chunks:
                    logger.warning(f"No chunks generated for {doc_path.name}")
                    results.append(IngestionResult(
                        success=False,
                        document_path=str(doc_path),
                        error_message="No chunks generated"
                    ))
                    continue
                
                logger.info(f"Generated {len(chunks)} chunks")
                
                # Convert chunks to LangChain Documents
                langchain_docs = [
                    Document(
                        page_content=chunk.content,
                        metadata=chunk.metadata
                    )
                    for chunk in chunks
                ]
                
                # Step 3: Let LangChain handle embedding + storage
                # This is where the magic happens - LangChain does:
                # - Generate embeddings for each chunk
                # - Store in vector database
                # - Handle metadata
                logger.info("Storing in vector database...")
                self.vector_store.add_documents(langchain_docs)
                
                logger.info(f"✓ Successfully ingested {doc_path.name}")
                
                # Step 4: Move to processed
                self._move_to_processed(doc_path)
                
                results.append(IngestionResult(
                    success=True,
                    document_path=str(doc_path),
                    chunks_count=len(chunks)
                ))
            
            except Exception as e:
                logger.error(f"Failed to process {doc_path.name}: {e}", exc_info=True)
                results.append(IngestionResult(
                    success=False,
                    document_path=str(doc_path),
                    error_message=str(e)
                ))
        
        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Ingestion complete: {successful}/{len(results)} documents processed")
        
        return results
