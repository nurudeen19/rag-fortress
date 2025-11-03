"""
Clean vector store service with LangChain patterns.

Architecture:
    loader.py   → Load documents from pending/
    chunker.py  → Chunk using LangChain splitters
    factory.py  → Get/create vector store with embeddings
    storage.py  → Orchestrate: load → chunk → store

Usage:
    from app.services.vector_store_v2.storage import DocumentStorageService
    
    # Embeddings already initialized in startup
    storage = DocumentStorageService()
    
    # Simple ingestion
    results = storage.ingest_from_pending()
"""

from app.services.vector_store_v2.storage import DocumentStorageService, IngestionResult
from app.services.vector_store_v2.factory import get_vector_store
from app.services.vector_store_v2.loader import DocumentLoader
from app.services.vector_store_v2.chunker import DocumentChunker


__all__ = [
    "DocumentStorageService",
    "IngestionResult",
    "get_vector_store",
    "DocumentLoader",
    "DocumentChunker",
]
