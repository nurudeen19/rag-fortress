"""
Vector store implementations for RAG Fortress.

This module provides a unified interface for multiple vector database providers:
- ChromaDB: Development and small datasets
- Qdrant: Production-ready, high performance
- Pinecone: Managed cloud service
- Weaviate: GraphQL interface, hybrid search
- Milvus: Large-scale deployments

All implementations follow the VectorStoreBase interface for consistent behavior.
"""

from app.services.vector_store.base import VectorStoreBase
from app.services.vector_store.chroma_store import ChromaVectorStore
from app.services.vector_store.factory import (
    VectorStoreFactory,
    VectorStoreType,
    get_vector_store
)

__all__ = [
    "VectorStoreBase",
    "ChromaVectorStore",
    "VectorStoreFactory",
    "VectorStoreType",
    "get_vector_store",
]
