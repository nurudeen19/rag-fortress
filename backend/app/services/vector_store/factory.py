"""
Vector Store Factory - Creates LangChain vector stores with from_documents().
Provider-agnostic, clean abstraction.
"""

from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from app.config.settings import settings
from app.core.exceptions import VectorStoreError
from app.core import get_logger


logger = get_logger(__name__)


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
        
        # Create vector store
        vector_store = get_vector_store(
            embeddings=embeddings,
            provider="chroma",
            collection_name="my_docs"
        )
        
        # Use LangChain's from_documents pattern
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name="my_docs"
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
            from langchain_qdrant import Qdrant
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
        
        store = Qdrant(
            client=client,
            collection_name=config["collection_name"],
            embeddings=embeddings
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
    
    # === FAISS (local) ===
    elif provider == "faiss":
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise VectorStoreError(
                "faiss not installed. Run: pip install faiss-cpu",
                provider="faiss"
            )
        
        # FAISS needs to be created with documents
        # Return a placeholder that can be used with from_documents()
        logger.info("✓ FAISS ready (will be created with from_documents)")
        return None  # Signal to use from_documents() directly
    
    else:
        raise VectorStoreError(
            f"Unsupported vector store: {provider}. "
            f"Supported: chroma, qdrant, pinecone, weaviate, faiss",
            provider=provider
        )
