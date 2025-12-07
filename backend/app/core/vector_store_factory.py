"""
Vector Store Factory - Creates LangChain vector stores with from_documents().
Provider-agnostic, clean abstraction.
"""

from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.core import get_logger


logger = get_logger(__name__)


# Global retriever instance
_retriever_instance: Optional[BaseRetriever] = None


def get_vector_store(
    embeddings: Embeddings,
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    **kwargs
) -> VectorStore:
    """
    Get or create a LangChain vector store instance.
    
    Args:
        embeddings: Pre-initialized LangChain embeddings (from startup)
        provider: Vector store provider (chroma, qdrant, pinecone, etc.)
        collection_name: Collection/index name
        **kwargs: Provider-specific arguments
    
    Returns:
        LangChain VectorStore instance ready for from_documents()
    
    Example:
        # Get pre-initialized embeddings from startup
        embeddings = get_embedding_provider()

        # Get a configured vector store instance (provider from settings or explicit)
        store = get_vector_store(
            embeddings=embeddings,
            provider="chroma",
            collection_name="my_docs"
        )
        
        # Use LangChain's from_documents pattern
        vector_store = store.from_documents(
            documents=chunks,
            embedding=embeddings,
        )
    """
    provider = (provider or settings.VECTOR_DB_PROVIDER).lower()
    
    # Get config from composed settings
    config = settings.get_vector_db_config()
    if collection_name:
        config["collection_name"] = collection_name
    config.update(kwargs)
    
    logger.info(f"Initializing vector store: {provider}")
    
    # === Chroma ===
    if provider == "chroma":
        try:
            from langchain_chroma import Chroma
        except ImportError:
            raise VectorStoreError(
                "langchain-chroma not installed. Run: pip install langchain-chroma",
                provider="chroma"
            )
        
        # Return existing collection or create new one
        store = Chroma(
            collection_name=config["collection_name"],
            embedding_function=embeddings,
            persist_directory=config["persist_directory"]
        )
        logger.info(f"✓ Chroma initialized: {config['collection_name']}")
        return store
    
    # === Qdrant ===
    elif provider == "qdrant":
        try:
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
        except ImportError:
            raise VectorStoreError(
                "langchain-qdrant not installed. Run: pip install langchain-qdrant qdrant-client",
                provider="qdrant"
            )
        
        client = QdrantClient(
            url=config.get("url"),
            api_key=config.get("api_key")
        )
        
        store = QdrantVectorStore(
            client=client,
            collection_name=config["collection_name"],
            embedding=embeddings
        )
        logger.info(f"✓ Qdrant initialized: {config['collection_name']}")
        return store
    
    # === Pinecone ===
    elif provider == "pinecone":
        try:
            from langchain_pinecone import PineconeVectorStore
        except ImportError:
            raise VectorStoreError(
                "langchain-pinecone not installed. Run: pip install langchain-pinecone",
                provider="pinecone"
            )
        
        store = PineconeVectorStore(
            index_name=config["collection_name"],
            embedding=embeddings
        )
        logger.info(f"✓ Pinecone initialized: {config['collection_name']}")
        return store
    
    # === Weaviate ===
    elif provider == "weaviate":
        try:
            from langchain_weaviate import WeaviateVectorStore
            import weaviate
        except ImportError:
            raise VectorStoreError(
                "langchain-weaviate not installed. Run: pip install langchain-weaviate weaviate-client",
                provider="weaviate"
            )
        
        client = weaviate.Client(
            url=config.get("url"),
            auth_client_secret=weaviate.AuthApiKey(api_key=config.get("api_key"))
        )
        
        store = WeaviateVectorStore(
            client=client,
            index_name=config["collection_name"],
            embedding=embeddings
        )
        logger.info(f"✓ Weaviate initialized: {config['collection_name']}")
        return store
    
    else:
        raise VectorStoreError(
            f"Unsupported vector store: {provider}. "
            f"Supported: chroma, qdrant, pinecone, weaviate",
            provider=provider
        )


def get_retriever(
    embeddings: Optional[Embeddings] = None,
    provider: Optional[str] = None,
    top_k: Optional[int] = None
) -> BaseRetriever:
    """
    Get retriever instance from vector store.
    Returns existing instance if initialized, otherwise creates new one.
    
    Args:
        embeddings: Pre-initialized embeddings (optional, uses existing if available)
        provider: Vector store provider (optional, uses settings default)
        top_k: Number of results to return (optional, uses MIN_TOP_K from settings)
    
    Returns:
        BaseRetriever: LangChain Retriever instance
    """
    global _retriever_instance
    
    # Return existing instance if available
    if _retriever_instance is not None:
        # Update search_kwargs if top_k provided
        if top_k is not None:
            _retriever_instance.search_kwargs = {"k": top_k}
        return _retriever_instance
    
    # Create new instance
    if embeddings is None:
        from app.core.embedding_factory import get_embedding_provider
        embeddings = get_embedding_provider()
    
    vector_store = get_vector_store(
        embeddings=embeddings,
        provider=provider
    )
    
    # Get top_k from settings or parameter
    k = top_k or settings.app_settings.MIN_TOP_K
    
    # Create retriever from vector store
    _retriever_instance = vector_store.as_retriever(
        search_kwargs={"k": k}
    )
    
    logger.info(f"✓ Retriever initialized (top_k={k})")
    return _retriever_instance
