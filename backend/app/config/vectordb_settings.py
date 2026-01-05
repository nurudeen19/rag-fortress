"""
Vector database configuration settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # Provider selection
    # Default: faiss (Python 3.14+ compatible, local storage)
    # Chroma: Currently Python 3.11-3.13 only (as of Dec 2025, Python 3.14 support in progress)
    VECTOR_DB_PROVIDER: str = Field("faiss", env="VECTOR_DB_PROVIDER")
    
    # Common Vector Store Configuration (used by FAISS, Chroma, etc.)
    VECTOR_STORE_COLLECTION_NAME: str = Field("rag_documents", env="VECTOR_STORE_COLLECTION_NAME")
    VECTOR_STORE_PERSIST_DIRECTORY: str = Field("./data/vector_store", env="VECTOR_STORE_PERSIST_DIRECTORY")
    
    # Qdrant Configuration
    QDRANT_HOST: str = Field("localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(6333, env="QDRANT_PORT")
    QDRANT_GRPC_PORT: int = Field(6334, env="QDRANT_GRPC_PORT")
    QDRANT_API_KEY: Optional[str] = Field(None, env="QDRANT_API_KEY")
    QDRANT_URL: Optional[str] = Field(None, env="QDRANT_URL")
    QDRANT_COLLECTION_NAME: str = Field("rag_documents", env="QDRANT_COLLECTION_NAME")
    QDRANT_PREFER_GRPC: bool = Field(False, env="QDRANT_PREFER_GRPC")
    
    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str] = Field(None, env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = Field("rag-documents", env="PINECONE_INDEX_NAME")
    
    # Weaviate Configuration
    WEAVIATE_URL: str = Field("http://localhost:8080", env="WEAVIATE_URL")
    WEAVIATE_API_KEY: Optional[str] = Field(None, env="WEAVIATE_API_KEY")
    WEAVIATE_CLASS_NAME: str = Field("Document", env="WEAVIATE_CLASS_NAME")
    
    # Milvus Configuration
    MILVUS_HOST: str = Field("localhost", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(19530, env="MILVUS_PORT")
    MILVUS_COLLECTION_NAME: str = Field("rag_documents", env="MILVUS_COLLECTION_NAME")
    MILVUS_USER: Optional[str] = Field(None, env="MILVUS_USER")
    MILVUS_PASSWORD: Optional[str] = Field(None, env="MILVUS_PASSWORD")
    
    # Ingestion Configuration
    # Batch size for chunk ingestion to vector store (higher = faster but more memory)
    # Recommended: 1000+ for production environments
    CHUNK_INGESTION_BATCH_SIZE: int = Field(1000, env="CHUNK_INGESTION_BATCH_SIZE")
    
    # Hybrid Search Configuration
    # Enable hybrid search (combines dense and sparse vectors using RRF)
    # Only supported by: Qdrant, Weaviate, Milvus
    # Requires provider to support hybrid search natively
    ENABLE_HYBRID_SEARCH: bool = Field(False, env="ENABLE_HYBRID_SEARCH")

    def validate_config(self, environment: str):
        """Validate vector database configuration based on environment."""
        vector_db = self.VECTOR_DB_PROVIDER.lower()
        
        # Validate provider is supported
        supported_dbs = {"faiss", "chroma", "qdrant", "pinecone", "weaviate", "milvus"}
        if vector_db not in supported_dbs:
            raise ValueError(
                f"Unsupported VECTOR_DB_PROVIDER: {vector_db}. "
                f"Supported: {', '.join(supported_dbs)}"
            )
        
        # Production validation: Don't allow Chroma or FAISS in production
        if environment == "production" and vector_db in ["chroma", "faiss"]:
            raise ValueError(
                f"{vector_db.upper()} is not recommended for production. "
                "Please use Qdrant, Pinecone, Weaviate, or Milvus instead."
            )
        
        # Hybrid search validation: Check provider compatibility
        if self.ENABLE_HYBRID_SEARCH:
            # Providers that natively support hybrid search with RRF (Reciprocal Rank Fusion)
            hybrid_supported_providers = {"qdrant", "weaviate", "milvus"}
            
            if vector_db not in hybrid_supported_providers:
                raise ValueError(
                    f"Hybrid search is not supported for {vector_db.upper()}. "
                    f"ENABLE_HYBRID_SEARCH requires one of: {', '.join(sorted(hybrid_supported_providers))}. "
                    f"Current provider: {vector_db}"
                )
        
        # Validate required fields for each provider
        if vector_db == "qdrant":
            if self.QDRANT_URL and not self.QDRANT_API_KEY:
                raise ValueError("QDRANT_API_KEY is required when using Qdrant Cloud (QDRANT_URL is set)")
        
        elif vector_db == "pinecone":
            if not self.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY is required for Pinecone provider")
            if not self.PINECONE_ENVIRONMENT:
                raise ValueError("PINECONE_ENVIRONMENT is required for Pinecone provider")

    def get_vector_db_config(self) -> dict:
        """
        Get vector database configuration for the selected provider.
        
        Returns:
            dict with provider-specific config including hybrid_search_enabled flag
        """
        provider = self.VECTOR_DB_PROVIDER.lower()
        
        # Base config included for all providers
        base_config = {
            "hybrid_search": self.ENABLE_HYBRID_SEARCH,
        }
        
        if provider == "faiss":
            return {
                **base_config,
                "provider": "faiss",
                "persist_directory": self.VECTOR_STORE_PERSIST_DIRECTORY,
                "collection_name": self.VECTOR_STORE_COLLECTION_NAME,
            }
        
        elif provider == "qdrant":
            config = {
                **base_config,
                "provider": "qdrant",
                "collection_name": self.QDRANT_COLLECTION_NAME,
            }
            
            if self.QDRANT_URL:
                config["url"] = self.QDRANT_URL
                config["api_key"] = self.QDRANT_API_KEY
            else:
                config["host"] = self.QDRANT_HOST
                config["port"] = self.QDRANT_PORT
                config["grpc_port"] = self.QDRANT_GRPC_PORT
                config["prefer_grpc"] = self.QDRANT_PREFER_GRPC
            
            return config
        
        elif provider == "chroma":
            return {
                **base_config,
                "provider": "chroma",
                "persist_directory": self.VECTOR_STORE_PERSIST_DIRECTORY,
                "collection_name": self.VECTOR_STORE_COLLECTION_NAME,
            }
        
        elif provider == "pinecone":
            return {
                **base_config,
                "provider": "pinecone",
                "api_key": self.PINECONE_API_KEY,
                "environment": self.PINECONE_ENVIRONMENT,
                "index_name": self.PINECONE_INDEX_NAME,
            }
        
        elif provider == "weaviate":
            config = {
                **base_config,
                "provider": "weaviate",
                "url": self.WEAVIATE_URL,
                "class_name": self.WEAVIATE_CLASS_NAME,
            }
            if self.WEAVIATE_API_KEY:
                config["api_key"] = self.WEAVIATE_API_KEY
            return config
        
        elif provider == "milvus":
            config = {
                **base_config,
                "provider": "milvus",
                "host": self.MILVUS_HOST,
                "port": self.MILVUS_PORT,
                "collection_name": self.MILVUS_COLLECTION_NAME,
            }
            if self.MILVUS_USER:
                config["user"] = self.MILVUS_USER
            if self.MILVUS_PASSWORD:
                config["password"] = self.MILVUS_PASSWORD
            return config
        
        else:
            raise ValueError(f"Unsupported vector database provider: {provider}")
