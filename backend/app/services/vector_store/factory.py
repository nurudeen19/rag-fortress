"""
Vector store factory.
Supports both custom and LangChain-native vector stores.
"""

from typing import Optional

from app.services.vector_store.base import VectorStoreBase
from app.services.vector_store.chroma_store import ChromaVectorStore
from app.config.settings import settings
from app.core.exceptions import VectorStoreError


# Export LangChain factory
from app.services.vector_store.langchain_factory import get_vector_store_langchain


def get_vector_store(
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    **kwargs
) -> VectorStoreBase:
    """
    Get a vector store instance.
    
    Args:
        provider: Vector store provider (default: from settings)
        collection_name: Collection name (default: from settings)
        **kwargs: Provider-specific arguments
    
    Returns:
        VectorStoreBase: Vector store instance
    """
    if provider is None:
        provider = settings.VECTOR_DB_PROVIDER
    
    # Get vector DB configuration
    config = settings.VectorDBSettings.get_vector_db_config()
    
    # Override collection name if provided
    if collection_name is not None:
        config["collection_name"] = collection_name
    
    # Override with any kwargs
    config.update(kwargs)
    
    provider = provider.lower()
    
    if provider == "chroma":
        return ChromaVectorStore(
            collection_name=config["collection_name"],
            persist_directory=config["persist_directory"]
        )
    
    else:
        raise VectorStoreError(
            f"Unsupported provider: {provider}",
            provider=provider
        )
