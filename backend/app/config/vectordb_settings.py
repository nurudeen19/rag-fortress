"""
Vector database configuration settings.
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # ============================================================================
    # VECTOR DATABASE PROVIDER SELECTION
    # ============================================================================
    # Supported: faiss, chroma, qdrant, pinecone, weaviate, milvus
    VECTOR_DB_PROVIDER: str = Field("faiss", env="VECTOR_DB_PROVIDER")
    
    # ============================================================================
    # GENERIC VECTOR STORE SETTINGS (all providers)
    # ============================================================================
    VECTOR_STORE_COLLECTION_NAME: str = Field("rag_documents", env="VECTOR_STORE_COLLECTION_NAME")
    VECTOR_STORE_PERSIST_DIRECTORY: str = Field("./data/vector_store", env="VECTOR_STORE_PERSIST_DIRECTORY")
    
    # ============================================================================
    # CONSOLIDATED PROVIDER-SPECIFIC SETTINGS
    # ============================================================================
    # Generic fields for connecting to remote vector databases
    VECTOR_DB_URL: Optional[str] = Field(None, env="VECTOR_DB_URL")
    VECTOR_DB_HOST: Optional[str] = Field(None, env="VECTOR_DB_HOST")
    VECTOR_DB_PORT: Optional[int] = Field(None, env="VECTOR_DB_PORT")
    VECTOR_DB_API_KEY: Optional[str] = Field(None, env="VECTOR_DB_API_KEY")
    VECTOR_DB_USERNAME: Optional[str] = Field(None, env="VECTOR_DB_USERNAME")
    VECTOR_DB_PASSWORD: Optional[str] = Field(None, env="VECTOR_DB_PASSWORD")
    VECTOR_DB_PREFER_GRPC: Optional[bool] = Field(None, env="VECTOR_DB_PREFER_GRPC")
    VECTOR_DB_INDEX_NAME: Optional[str] = Field(None, env="VECTOR_DB_INDEX_NAME")
    VECTOR_DB_CLASS_NAME: Optional[str] = Field(None, env="VECTOR_DB_CLASS_NAME")
    VECTOR_DB_ENVIRONMENT: Optional[str] = Field(None, env="VECTOR_DB_ENVIRONMENT")
    
    # Additional GRPC port for Qdrant
    VECTOR_DB_GRPC_PORT: Optional[int] = Field(None, env="VECTOR_DB_GRPC_PORT")
    
    # ============================================================================
    # HYBRID SEARCH CONFIGURATION
    # ============================================================================
    # Enable hybrid search (combines dense and sparse vectors using RRF)
    # Only supported by: Qdrant, Weaviate, Milvus
    ENABLE_HYBRID_SEARCH: bool = Field(False, env="ENABLE_HYBRID_SEARCH")
    
    # ============================================================================
    # INGESTION CONFIGURATION
    # ============================================================================
    # Batch size for chunk ingestion to vector store (higher = faster but more memory)
    # Recommended: 1000+ for production environments
    CHUNK_INGESTION_BATCH_SIZE: int = Field(1000, env="CHUNK_INGESTION_BATCH_SIZE")

    @field_validator("VECTOR_DB_PORT", "VECTOR_DB_GRPC_PORT", mode="before")
    @classmethod
    def validate_optional_int_fields(cls, v):
        """Convert empty strings to None for optional int fields."""
        if v == "" or v is None:
            return None
        return int(v) if isinstance(v, str) else v

    @field_validator("VECTOR_DB_PREFER_GRPC", mode="before")
    @classmethod
    def validate_optional_bool_fields(cls, v):
        """Convert empty strings to None for optional bool fields."""
        if v == "" or v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

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
            if self.VECTOR_DB_URL and not self.VECTOR_DB_API_KEY:
                raise ValueError("VECTOR_DB_API_KEY is required when using Qdrant Cloud (VECTOR_DB_URL is set)")
        
        elif vector_db == "pinecone":
            if not self.VECTOR_DB_API_KEY:
                raise ValueError("VECTOR_DB_API_KEY is required for Pinecone provider")
            if not self.VECTOR_DB_ENVIRONMENT:
                raise ValueError("VECTOR_DB_ENVIRONMENT is required for Pinecone provider")

    def get_vector_db_config(self) -> dict:
        """
        Get vector database configuration for the selected provider.
        Uses consolidated generic fields when available, falls back to defaults.
        
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
                "collection_name": self.VECTOR_STORE_COLLECTION_NAME,
            }
            
            if self.VECTOR_DB_URL:
                config["url"] = self.VECTOR_DB_URL
                config["api_key"] = self.VECTOR_DB_API_KEY
            else:
                config["host"] = self.VECTOR_DB_HOST or "localhost"
                config["port"] = self.VECTOR_DB_PORT or 6333
                config["grpc_port"] = self.VECTOR_DB_GRPC_PORT or 6334
                config["prefer_grpc"] = self.VECTOR_DB_PREFER_GRPC if self.VECTOR_DB_PREFER_GRPC is not None else False
            
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
                "api_key": self.VECTOR_DB_API_KEY,
                "environment": self.VECTOR_DB_ENVIRONMENT,
                "index_name": self.VECTOR_DB_INDEX_NAME or "rag-documents",
            }
        
        elif provider == "weaviate":
            config = {
                **base_config,
                "provider": "weaviate",
                "url": self.VECTOR_DB_URL or "http://localhost:8080",
                "class_name": self.VECTOR_DB_CLASS_NAME or "Document",
            }
            if self.VECTOR_DB_API_KEY:
                config["api_key"] = self.VECTOR_DB_API_KEY
            return config
        
        elif provider == "milvus":
            config = {
                **base_config,
                "provider": "milvus",
                "host": self.VECTOR_DB_HOST or "localhost",
                "port": self.VECTOR_DB_PORT or 19530,
                "collection_name": self.VECTOR_STORE_COLLECTION_NAME,
            }
            if self.VECTOR_DB_USERNAME:
                config["user"] = self.VECTOR_DB_USERNAME
            if self.VECTOR_DB_PASSWORD:
                config["password"] = self.VECTOR_DB_PASSWORD
            return config
        
        else:
            raise ValueError(f"Unsupported vector database provider: {provider}")

