"""
Document Ingestion Orchestrator.
Coordinates: Load → Chunk → Embed → Store → Move to Processed
"""

import shutil
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from app.services.document_loader import DocumentLoader
from app.services.chunking import DocumentChunker
from app.core.embedding_factory import get_embedding_provider
from app.services.vector_store.factory import get_vector_store
from app.config.settings import settings
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
    1. Load document from pending directory
    2. Chunk document (type-aware)
    3. Generate embeddings
    4. Store in vector database
    5. Move to processed directory (on success)
    
    Simple folder-based tracking:
    - Documents placed in pending/ are processed
    - Successfully processed documents moved to processed/
    - Failed documents remain in pending/ for retry
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
        # Initialize components
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        
        # Directories
        self.pending_dir = Path(settings.PENDING_DIR)
        self.processed_dir = Path(settings.PROCESSED_DIR)
        
        # Ensure directories exist
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    
    def _move_to_processed(self, file_path: Path) -> None:
        """
        Move document from pending to processed directory.
        
        Args:
            file_path: Full path to file in pending directory
        """
        # Get relative path from pending directory
        relative_path = file_path.relative_to(self.pending_dir)
        
        # Destination path in processed directory
        dest_path = self.processed_dir / relative_path
        
        # Create subdirectories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle name conflicts: append timestamp if file exists
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = dest_path.stem
            suffix = dest_path.suffix
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"
        
        # Move the file
        shutil.move(str(file_path), str(dest_path))
    
    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> IngestionResult:
        """
        Ingest a single document through the full pipeline.
        
        Args:
            file_path: Path to document (relative to pending directory)
            metadata: Additional metadata to attach to chunks
        
        Returns:
            IngestionResult: Result of ingestion
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get full path in pending directory
            full_path = self.pending_dir / file_path
            
            if not full_path.exists():
                return IngestionResult(
                    success=False,
                    document_path=file_path,
                    error_message=f"File not found in pending directory: {file_path}"
                )
            
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
            
            # Step 3: Generate embeddings (batch operation - cost-effective!)
            embedder = get_embedding_provider()
            contents = [chunk.content for chunk in chunks]
            embeddings = await embedder.aembed_documents(contents)
            
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
            
            if not success:
                return IngestionResult(
                    success=False,
                    document_path=file_path,
                    error_message="Failed to store chunks in vector database"
                )
            
            # Step 6: Move to processed directory (only if successful)
            self._move_to_processed(full_path)
            
            return IngestionResult(
                success=True,
                document_path=file_path,
                chunks_count=len(chunks)
            )
            
        except Exception as e:
            return IngestionResult(
                success=False,
                document_path=file_path,
                error_message=str(e)
            )
    
    
    async def ingest_from_pending(
        self,
        recursive: bool = True,
        file_types: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents from the pending directory.
        
        Args:
            recursive: Whether to search subdirectories
            file_types: List of file extensions to ingest (e.g., ['pdf', 'txt']). None = all types.
            metadata: Additional metadata for all documents
        
        Returns:
            List[IngestionResult]: Results for each document
        """
        if not self._initialized:
            await self.initialize()
        
        results = []
        
        # Load all documents from pending directory
        documents = self.loader.load_all(recursive=recursive, file_types=file_types)
        
        if not documents:
            print("No documents found in pending directory")
            return results
        
        print(f"Found {len(documents)} documents in pending directory")
        
        for document in documents:
            try:
                # Get full path in pending directory
                full_path = self.pending_dir / document.source
                
                # Chunk document
                chunks = self.chunker.chunk_document(document)
                
                if not chunks:
                    results.append(IngestionResult(
                        success=False,
                        document_path=document.source,
                        error_message="No chunks generated"
                    ))
                    continue
                
                # Generate embeddings
                embedder = get_embedding_provider()
                contents = [chunk.content for chunk in chunks]
                embeddings = await embedder.aembed_documents(contents)
                
                # Prepare metadata
                metadatas = []
                for chunk in chunks:
                    chunk_metadata = {
                        "source": document.source,
                        "document_type": document.doc_type.value,
                        "chunk_index": chunk.chunk_index,
                        **chunk.metadata,
                        **document.metadata
                    }
                    if metadata:
                        chunk_metadata.update(metadata)
                    metadatas.append(chunk_metadata)
                
                # Store in vector database
                success = await self.vector_store.insert_chunks(
                    contents=contents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                
                if success:
                    # Move to processed directory
                    self._move_to_processed(full_path)
                    results.append(IngestionResult(
                        success=True,
                        document_path=document.source,
                        chunks_count=len(chunks)
                    ))
                else:
                    results.append(IngestionResult(
                        success=False,
                        document_path=document.source,
                        error_message="Failed to store in vector database"
                    ))
                
            except Exception as e:
                results.append(IngestionResult(
                    success=False,
                    document_path=document.source,
                    error_message=str(e)
                ))
        
        return results
    
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # Utility methods
    
    def get_pending_files(self) -> List[Path]:
        """Get list of files in pending directory."""
        files = []
        for path in self.pending_dir.rglob("*"):
            if path.is_file():
                files.append(path.relative_to(self.pending_dir))
        return files
    
    def get_processed_files(self) -> List[Path]:
        """Get list of files in processed directory."""
        files = []
        for path in self.processed_dir.rglob("*"):
            if path.is_file():
                files.append(path.relative_to(self.processed_dir))
        return files
    
    def reprocess_document(self, filename: str) -> bool:
        """
        Move a document from processed back to pending for reprocessing.
        
        Args:
            filename: Filename in processed directory (can include subdirectories)
            
        Returns:
            bool: True if document was moved successfully
        """
        source_path = self.processed_dir / filename
        
        if not source_path.exists():
            return False
        
        # Destination in pending directory
        dest_path = self.pending_dir / filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle name conflicts
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = dest_path.stem
            suffix = dest_path.suffix
            dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"
        
        # Move back to pending
        shutil.move(str(source_path), str(dest_path))
        return True
