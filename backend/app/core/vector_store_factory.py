"""
Vector Store Factory - Creates LangChain vector stores with singleton pattern.
Returns configured vector store instance based on settings.
Reuses instance if already initialized (from startup).
"""

from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.core import get_logger


logger = get_logger(__name__)


# Global instance (initialized in startup)
_vector_store_instance: Optional[VectorStore] = None
_retriever_instance: Optional[BaseRetriever] = None


def get_vector_store(
    embeddings: Embeddings,
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    **kwargs
) -> VectorStore:
    """
    Get LangChain vector store instance.
    Returns existing instance if initialized, otherwise creates new one.
    
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

        # Get vector store instance (reuses existing if available)
        store = get_vector_store(
            embeddings=embeddings,
            provider="chroma",
            collection_name="my_docs"
        )
    """
    global _vector_store_instance
    
    # Return existing instance if available
    if _vector_store_instance is not None:
        return _vector_store_instance
    
    # Create new instance
    _vector_store_instance = _create_vector_store(embeddings, provider, collection_name, **kwargs)
    return _vector_store_instance


def _create_vector_store(
    embeddings: Embeddings,
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    **kwargs
) -> VectorStore:
    """
    Create LangChain vector store instance based on configuration.
    Internal function - use get_vector_store() instead.
    
    Args:
        embeddings: LangChain embeddings
        provider: Vector store provider (faiss, chroma, qdrant, etc.)
        collection_name: Collection/index name
        **kwargs: Provider-specific arguments
        
    Returns:
        VectorStore instance
    """
    provider = (provider or settings.VECTOR_DB_PROVIDER).lower()
    
    # Get config from composed settings
    config = settings.get_vector_db_config()
    if collection_name:
        config["collection_name"] = collection_name
    config.update(kwargs)
    
    logger.info(f"Initializing vector store: {provider}")
    # === FAISS (Default for Python 3.14+) ===
    if provider == "faiss":
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise VectorStoreError(
                "FAISS not installed. Run: pip install faiss-cpu langchain-community",
                provider="faiss"
            )
        
        import os
        persist_directory = config.get("persist_directory")
        index_path = os.path.join(persist_directory, config["collection_name"])
        
        # Try to load existing index, otherwise create empty store
        if os.path.exists(index_path):
            try:
                store = FAISS.load_local(
                    index_path,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"✓ FAISS loaded from disk: {config['collection_name']}")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index, creating new one: {e}")
                # Create empty FAISS store with a dummy document
                from langchain_core.documents import Document
                store = FAISS.from_documents(
                    [Document(page_content="init", metadata={"init": True})],
                    embeddings
                )
        else:
            # Create new FAISS store with dummy document
            from langchain_core.documents import Document
            store = FAISS.from_documents(
                [Document(page_content="init", metadata={"init": True})],
                embeddings
            )
            logger.info(f"✓ FAISS initialized (new): {config['collection_name']}")
        
        # Store the persist path for later saving
        store._persist_directory = persist_directory
        store._collection_name = config["collection_name"]
        return store
    
    # === Chroma (Currently Python 3.13 and below only - as of December 2025) ===
    elif provider == "chroma":
        try:
            from langchain_chroma import Chroma
        except ImportError:
            raise VectorStoreError(
                "langchain-chroma not installed. "
                "Note: As of December 2025, Chroma is NOT compatible with Python 3.14+ due to dependency conflicts. "
                "Python 3.14 support is being worked on by the Chroma team. "
                "For now, use FAISS for Python 3.14+ or install Chroma with pip for Python 3.11-3.13. "
                "Run: pip install langchain-chroma",
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
            f"Supported: faiss, chroma (legacy), qdrant, pinecone, weaviate, milvus",
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


def save_vector_store(vector_store: VectorStore) -> bool:
    """
    Save vector store to disk (for FAISS).
    
    For providers like FAISS that support local persistence, this function
    saves the current state to disk. For other providers (Chroma, Qdrant, etc.),
    persistence is handled automatically.
    
    Args:
        vector_store: The vector store instance to save
    
    Returns:
        bool: True if saved successfully, False otherwise
    
    Example:
        store = get_vector_store(embeddings, provider="faiss")
        store.add_documents(documents)
        save_vector_store(store)  # Persist to disk
    """
    try:
        # Check if this is a FAISS store with persistence attributes
        if hasattr(vector_store, '_persist_directory') and hasattr(vector_store, '_collection_name'):
            import os
            persist_dir = vector_store._persist_directory
            collection_name = vector_store._collection_name
            
            # Ensure directory exists
            os.makedirs(persist_dir, exist_ok=True)
            
            # Save to disk
            index_path = os.path.join(persist_dir, collection_name)
            vector_store.save_local(index_path)
            
            logger.info(f"✓ FAISS index saved to: {index_path}")
            return True
        else:
            # Other providers handle persistence automatically
            logger.debug(f"Vector store type {type(vector_store).__name__} does not require manual saving")
            return False
    except Exception as e:
        logger.error(f"Failed to save vector store: {e}")
        return False
