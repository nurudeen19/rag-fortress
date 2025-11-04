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

        # Step 2: Chunk all files at once using the new chunker flow
        chunks: List[Dict[str, Any]] = self.chunker.chunk_loaded_files(files)

        if not chunks:
            logger.warning("No chunks generated from input files")
            # Move files to processed even if no chunks to avoid reprocessing
            for f in files:
                try:
                    self._move_to_processed(Path(f["file_path"]))
                except Exception:
                    pass
            return results

        # Step 3: Store in vector DB
        logger.info(f"Storing {len(chunks)} chunks in vector DB...")
    stored_count = self.store_data(chunks)

        # Step 4: Move all processed files
        for f in files:
            try:
                self._move_to_processed(Path(f["file_path"]))
            except Exception as e:
                logger.error(f"Failed moving processed file {f.get('file_name')}: {e}")

        # Build per-file results based on chunk metadata source (file name)
        source_counts: Dict[str, int] = {}
        for c in chunks:
            src_name = (c.get("metadata") or {}).get("source")
            if src_name:
                source_counts[src_name] = source_counts.get(src_name, 0) + 1

        for f in files:
            name = f.get("file_name")
            count = source_counts.get(name, 0)
            results.append(IngestionResult(
                success=count > 0,
                document_path=str(f.get("file_path")),
                chunks_count=count,
                error=None if count > 0 else "No chunks generated",
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

    def store_data(self, chunks: List[Dict[str, Any]]) -> int:
        """Store chunk dicts into the already-initialized vector store instance.

        Simple flow:
        - Convert chunk dicts to LangChain Documents
        - Call vector_store.add_documents(docs)
        The vector store instance is already configured with the embedding function via the factory.
        """
        if not chunks:
            return 0

        # Convert to Documents
        docs: List[Document] = []
        for c in chunks:
            text = c.get("content")
            if not isinstance(text, str) or not text.strip():
                continue
            meta = c.get("metadata") or {}
            docs.append(Document(page_content=text, metadata=meta))

        if not docs:
            return 0

        # Store via provider instance
        try:
            self.vector_store.add_documents(docs)
            return len(docs)
        except Exception as e:
            logger.error(f"Failed storing data in vector store: {e}")
            return 0
