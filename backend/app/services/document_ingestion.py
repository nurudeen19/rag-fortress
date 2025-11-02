"""
Document Ingestion Orchestrator.
Coordinates: Load → Chunk → Embed → Store
"""

from typing import Dict, Any, List
from pathlib import Path

from app.services.document_loader import DocumentLoader
from app.services.chunking import DocumentChunker
from app.services.embedding import get_embedding_provider
from app.services.vector_store.factory import get_vector_store
from app.config.settings import get_settings
from app.core.exceptions import DocumentError


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
    Orchestrates the document ingestion pipeline.
    
    Pipeline:
    1. Load document
    2. Chunk document (type-aware)
    3. Generate embeddings
    4. Store in vector database
    """
    
    def __init__(
        self,
        vector_store_provider: str = None,
        embedding_provider: str = None,
        collection_name: str = None
    ):
        """
        Initialize ingestion service.
        
        Args:
            vector_store_provider: Override vector store provider
            embedding_provider: Override embedding provider
            collection_name: Override collection name
        """
        self.settings = get_settings()
        
        # Initialize components
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        
        # Get embedding provider
        provider_name = embedding_provider or self.settings.embedding.provider
        self.embedding_provider = get_embedding_provider(provider_name)
        
        # Get vector store
        self.vector_store = get_vector_store(
            provider=vector_store_provider,
            collection_name=collection_name
        )
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize vector store connection."""
        await self.vector_store.initialize()
        self._initialized = True
    
    async def close(self) -> None:
        """Close vector store connection."""
        await self.vector_store.close()
        self._initialized = False
    
    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> IngestionResult:
        """
        Ingest a single document through the full pipeline.
        
        Args:
            file_path: Path to document
            metadata: Additional metadata to attach to chunks
        
        Returns:
            IngestionResult: Result of ingestion
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Step 1: Load document
            document = self.loader.load(file_path)
            
            # Step 2: Chunk document (type-aware)
            chunks = self.chunker.chunk_document(document)
            
            if not chunks:
                return IngestionResult(
                    success=False,
                    document_path=file_path,
                    error_message="No chunks generated from document"
                )
            
            # Step 3: Generate embeddings
            contents = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_provider.embed_batch(contents)
            
            # Step 4: Prepare metadata
            metadatas = []
            for chunk in chunks:
                chunk_metadata = {
                    "source": document.source,
                    "document_type": document.doc_type.value,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                # Add user-provided metadata
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
            
            # Step 5: Store in vector database
            success = await self.vector_store.insert_chunks(
                contents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            return IngestionResult(
                success=success,
                document_path=file_path,
                chunks_count=len(chunks)
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                document_path=file_path,
                error_message=str(e)
            )
    
    async def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        metadata: Dict[str, Any] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents in a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            metadata: Additional metadata for all documents
        
        Returns:
            List[IngestionResult]: Results for each document
        """
        if not self._initialized:
            await self.initialize()
        
        results = []
        directory = Path(directory_path)
        
        # Supported extensions
        extensions = ['.txt', '.pdf', '.docx', '.md', '.json', '.csv', '.xlsx', '.pptx']
        
        # Find all documents
        if recursive:
            files = [f for ext in extensions for f in directory.rglob(f'*{ext}')]
        else:
            files = [f for ext in extensions for f in directory.glob(f'*{ext}')]
        
        # Ingest each document
        for file_path in files:
            result = await self.ingest_document(str(file_path), metadata)
            results.append(result)
        
        return results
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
