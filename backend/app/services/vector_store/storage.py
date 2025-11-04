"""
Document Storage Service - Orchestrates load → chunk → store pipeline.
Simple, clean, new flow based on loader → chunker (dicts) → store.
"""

from typing import List, Optional, Dict, Any
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
    Simplified document storage.

    Flow:
    1) Get/initialize dependencies (embeddings, vector store)
    2) Load documents (loader → list[dict])
    3) Chunk (chunker → list[{content, metadata}])
    4) Store (provider.add_texts or create FAISS via from_texts)
    5) Post-process: move files to processed/
    6) Log summary
    """
    
    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_store_provider: Optional[str] = None,
        collection_name: Optional[str] = None,
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
    # collection name is optional and not required here (factory/settings handle it)
    self.collection_name = collection_name

        # Get or create vector store (reuses existing if available)
        # Do not force collection name here; factory/settings handle it.
        self.vector_store = get_vector_store(
            embeddings=self.embeddings,
            provider=self.provider,
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
        file_types: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> List[IngestionResult]:
        """
        Ingest all documents from pending directory.
        
        Simple flow:
        1. Load documents (loader handles all file types)
        2. Chunk documents (chunker returns LangChain Documents)
        3. Store in vector DB with batching
        4. Move only successfully stored files
        
        Args:
            recursive: Search subdirectories
            file_types: Filter by file extensions
            batch_size: Number of chunks to store per batch (default: 100)
            
        Returns:
            List of ingestion results
        """
        results = []
        
        # Step 1: Load documents (loader returns list of dicts)
        logger.info("=" * 60)
        logger.info("Starting document ingestion")
        logger.info("=" * 60)
        
        files = self.loader.load_from_pending(
            recursive=recursive,
            file_types=file_types,
        )

        if not files:
            logger.info("No documents to process")
            return results

        logger.info(f"Processing {len(files)} files")

        # Step 2: Chunk all files at once (returns LangChain Documents)
        chunks: List[Document] = self.chunker.chunk_loaded_files(files)

        if not chunks:
            logger.warning("No chunks generated from input files")
            return results

        # Step 3: Store in vector DB with batching and error recovery
        logger.info(f"Storing {len(chunks)} chunks in vector DB...")
        successfully_stored_sources, stored_count = self.store_data(chunks, batch_size=batch_size)

        # Step 4: Move only successfully stored files
        moved_count = 0
        for f in files:
            file_name = f.get("file_name")
            if file_name in successfully_stored_sources:
                try:
                    self._move_to_processed(Path(f["file_path"]))
                    moved_count += 1
                except Exception as e:
                    logger.error(f"Failed moving {file_name}: {e}")

        # Build per-file results
        source_counts: Dict[str, int] = {}
        for chunk in chunks:
            src_name = chunk.metadata.get("source")
            if src_name:
                source_counts[src_name] = source_counts.get(src_name, 0) + 1

        for f in files:
            name = f.get("file_name")
            count = source_counts.get(name, 0)
            was_stored = name in successfully_stored_sources
            
            results.append(IngestionResult(
                success=was_stored and count > 0,
                document_path=str(f.get("file_path")),
                chunks_count=count if was_stored else 0,
                error=None if was_stored else "Storage failed",
            ))
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total_chunks = sum(r.chunks_count for r in results if r.success)
        
        logger.info("=" * 60)
        logger.info(f"Ingestion complete:")
        logger.info(f"  Files processed: {successful}/{len(results)}")
        logger.info(f"  Files moved: {moved_count}")
        logger.info(f"  Chunks stored: {total_chunks}")
        logger.info("=" * 60)
        
        return results

    def store_data(self, chunks: List[Document], batch_size: int = 100) -> tuple[set, int]:
        """Store LangChain Documents with batching for scalability.

        Args:
            chunks: List of LangChain Document objects
            batch_size: Number of chunks per batch (default: 100)

        Returns:
            Tuple of (set of successfully stored source names, total count stored)
        """
        if not chunks:
            return set(), 0

        successfully_stored_sources = set()
        total_stored = 0

        # Track which sources we're processing in this batch
        batch_sources = set()
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Track sources in this batch
            batch_sources = {doc.metadata.get("source") for doc in batch if doc.metadata.get("source")}
            
            try:
                # Use add_documents for batch storage
                self.vector_store.add_documents(batch)
                total_stored += len(batch)
                successfully_stored_sources.update(batch_sources)
                logger.info(f"✓ Stored batch {batch_num}: {len(batch)} chunks")
            except Exception as e:
                logger.error(f"✗ Failed storing batch {batch_num}: {e}")
                # Don't add these sources to successfully_stored

        return successfully_stored_sources, total_stored
