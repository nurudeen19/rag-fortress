"""
LangChain-compatible vector store factory.
Returns proper LangChain VectorStore instances that support from_documents().
"""

from typing import Optional
from langchain_core.embeddings import Embeddings

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.core import get_logger


logger = get_logger(__name__)


def get_vector_store_langchain(
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    embeddings: Optional[Embeddings] = None,
    **kwargs
):
    """
    Get a LangChain-compatible vector store instance.
    
    Args:
        provider: Vector store provider (chroma, qdrant, pinecone, etc.)
        collection_name: Collection/index name
        embeddings: LangChain embeddings instance
        **kwargs: Provider-specific arguments
    
    Returns:
        LangChain VectorStore instance with from_documents() support
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
    logger.info(f"Initializing LangChain vector store: {provider}")
    
    # Chroma
    if provider == "chroma":
        try:
            from langchain_chroma import Chroma
        except ImportError:
            raise VectorStoreError(
                "langchain-chroma not installed. Install with: pip install langchain-chroma",
                provider="chroma"
            )
        
        return Chroma(
            collection_name=config["collection_name"],
            embedding_function=embeddings,
            persist_directory=config["persist_directory"]
        )
    
    # Qdrant
    elif provider == "qdrant":
        try:
            from langchain_qdrant import Qdrant
            from qdrant_client import QdrantClient
        except ImportError:
            raise VectorStoreError(
                "langchain-qdrant not installed. Install with: pip install langchain-qdrant qdrant-client",
                provider="qdrant"
            )
        
        client = QdrantClient(
            url=config.get("url"),
            api_key=config.get("api_key")
        )
        
        return Qdrant(
            client=client,
            collection_name=config["collection_name"],
            embeddings=embeddings
        )
    
    # Pinecone
    elif provider == "pinecone":
        try:
            from langchain_pinecone import PineconeVectorStore
        except ImportError:
            raise VectorStoreError(
                "langchain-pinecone not installed. Install with: pip install langchain-pinecone",
                provider="pinecone"
            )
        
        return PineconeVectorStore(
            index_name=config["collection_name"],
            embedding=embeddings
        )
    
    # Weaviate
    elif provider == "weaviate":
        try:
            from langchain_weaviate import WeaviateVectorStore
            import weaviate
        except ImportError:
            raise VectorStoreError(
                "langchain-weaviate not installed. Install with: pip install langchain-weaviate weaviate-client",
                provider="weaviate"
            )
        
        client = weaviate.Client(
            url=config.get("url"),
            auth_client_secret=weaviate.AuthApiKey(api_key=config.get("api_key"))
        )
        
        return WeaviateVectorStore(
            client=client,
            index_name=config["collection_name"],
            embedding=embeddings
        )
    
    # FAISS (local)
    elif provider == "faiss":
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise VectorStoreError(
                "faiss not installed. Install with: pip install faiss-cpu",
                provider="faiss"
            )
        
        # FAISS is created empty, documents added later
        return FAISS.from_documents(
            documents=[],  # Empty initially
            embedding=embeddings
        )
    
    else:
        raise VectorStoreError(
            f"Unsupported vector store provider: {provider}. "
            f"Supported: chroma, qdrant, pinecone, weaviate, faiss",
            provider=provider
        )
