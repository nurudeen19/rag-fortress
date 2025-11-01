from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import Field

class Settings(BaseSettings):
    # App
    APP_NAME: str = Field("RAG Fortress", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(True, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")

    # LLM Provider selection
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    
    # Fallback LLM configuration (optional, defaults to HuggingFace small model)
    FALLBACK_LLM_PROVIDER: Optional[str] = Field(None, env="FALLBACK_LLM_PROVIDER")
    FALLBACK_LLM_API_KEY: Optional[str] = Field(None, env="FALLBACK_LLM_API_KEY")
    FALLBACK_LLM_MODEL: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL")
    FALLBACK_LLM_TEMPERATURE: Optional[float] = Field(None, env="FALLBACK_LLM_TEMPERATURE")
    FALLBACK_LLM_MAX_TOKENS: Optional[int] = Field(None, env="FALLBACK_LLM_MAX_TOKENS")

    # OpenAI Provider
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(0.7, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(2000, env="OPENAI_MAX_TOKENS")

    # Google Provider
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    GOOGLE_MODEL: str = Field("gemini-pro", env="GOOGLE_MODEL")
    GOOGLE_TEMPERATURE: float = Field(0.7, env="GOOGLE_TEMPERATURE")
    GOOGLE_MAX_TOKENS: int = Field(2000, env="GOOGLE_MAX_TOKENS")

    # HuggingFace Provider
    HF_API_TOKEN: Optional[str] = Field(None, env="HF_API_TOKEN")
    HF_MODEL: str = Field("meta-llama/Llama-2-7b-chat-hf", env="HF_MODEL")
    HF_TEMPERATURE: float = Field(0.7, env="HF_TEMPERATURE")
    HF_MAX_TOKENS: int = Field(2000, env="HF_MAX_TOKENS")

    # Fallback HuggingFace Provider (small model for backup)
    FALLBACK_HF_API_TOKEN: Optional[str] = Field(None, env="FALLBACK_HF_API_TOKEN")
    FALLBACK_HF_MODEL: str = Field("google/flan-t5-small", env="FALLBACK_HF_MODEL")
    FALLBACK_HF_TEMPERATURE: float = Field(0.7, env="FALLBACK_HF_TEMPERATURE")
    FALLBACK_HF_MAX_TOKENS: int = Field(512, env="FALLBACK_HF_MAX_TOKENS")

    # Embedding Provider selection (defaults to huggingface sentence-transformers)
    EMBEDDING_PROVIDER: str = Field("huggingface", env="EMBEDDING_PROVIDER")
    
    # OpenAI Embeddings
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    OPENAI_EMBEDDING_DIMENSIONS: Optional[int] = Field(None, env="OPENAI_EMBEDDING_DIMENSIONS")
    
    # Google Embeddings (Gemini API)
    GOOGLE_EMBEDDING_MODEL: str = Field("gemini-embedding-001", env="GOOGLE_EMBEDDING_MODEL")
    GOOGLE_EMBEDDING_DIMENSIONS: Optional[int] = Field(None, env="GOOGLE_EMBEDDING_DIMENSIONS")  # 768, 1536, or 3072
    GOOGLE_EMBEDDING_TASK_TYPE: str = Field("RETRIEVAL_DOCUMENT", env="GOOGLE_EMBEDDING_TASK_TYPE")  # RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.
    
    # HuggingFace Embeddings (Sentence Transformers)
    HF_EMBEDDING_MODEL: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="HF_EMBEDDING_MODEL")
    HF_EMBEDDING_DEVICE: str = Field("cpu", env="HF_EMBEDDING_DEVICE")  # cpu or cuda
    
    # Cohere Embeddings
    COHERE_API_KEY: Optional[str] = Field(None, env="COHERE_API_KEY")
    COHERE_EMBEDDING_MODEL: str = Field("embed-english-v3.0", env="COHERE_EMBEDDING_MODEL")
    COHERE_INPUT_TYPE: str = Field("search_document", env="COHERE_INPUT_TYPE")  # search_document, search_query, classification, clustering
    
    # Voyage AI Embeddings
    VOYAGE_API_KEY: Optional[str] = Field(None, env="VOYAGE_API_KEY")
    VOYAGE_EMBEDDING_MODEL: str = Field("voyage-2", env="VOYAGE_EMBEDDING_MODEL")
    
    # Vector Database selection
    VECTOR_DB_PROVIDER: str = Field("chroma", env="VECTOR_DB_PROVIDER")
    
    # Qdrant Configuration
    QDRANT_HOST: str = Field("localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(6333, env="QDRANT_PORT")
    QDRANT_GRPC_PORT: int = Field(6334, env="QDRANT_GRPC_PORT")
    QDRANT_API_KEY: Optional[str] = Field(None, env="QDRANT_API_KEY")  # For Qdrant Cloud
    QDRANT_URL: Optional[str] = Field(None, env="QDRANT_URL")  # For Qdrant Cloud
    QDRANT_COLLECTION_NAME: str = Field("rag_documents", env="QDRANT_COLLECTION_NAME")
    QDRANT_PREFER_GRPC: bool = Field(False, env="QDRANT_PREFER_GRPC")
    
    # Chroma Configuration
    CHROMA_HOST: str = Field("localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(8000, env="CHROMA_PORT")
    CHROMA_PERSIST_DIRECTORY: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    CHROMA_COLLECTION_NAME: str = Field("rag_documents", env="CHROMA_COLLECTION_NAME")
    
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

    # Database
    DATABASE_URL: str = Field("sqlite:///./rag_fortress.db", env="DATABASE_URL")

    # RAG
    CHUNK_SIZE: int = Field(1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(200, env="CHUNK_OVERLAP")
    TOP_K_RESULTS: int = Field(5, env="TOP_K_RESULTS")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(["http://localhost:3000", "http://localhost:8000"], env="ALLOWED_ORIGINS")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/app.log", env="LOG_FILE")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **values):
        super().__init__(**values)
        allowed_envs = {"development", "production", "staging"}
        if self.ENVIRONMENT not in allowed_envs:
            raise ValueError(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}. Allowed: {allowed_envs}")
        # Enforce debug level
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            self.LOG_LEVEL = "WARNING"
        elif self.ENVIRONMENT == "development":
            self.DEBUG = True
            self.LOG_LEVEL = "DEBUG"
        
        # Validate fallback provider is different from primary
        if self.FALLBACK_LLM_PROVIDER:
            self._validate_fallback_config()
        
        # Validate vector database configuration
        self._validate_vector_db_config()
        
        # Validate embedding provider configuration
        self._validate_embedding_config()

    def get_llm_config(self):
        """Get LLM configuration for the selected provider"""
        provider = self.LLM_PROVIDER.lower()
        
        if provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
            }
        elif provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required when using Google provider")
            return {
                "provider": "google",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_MODEL,
                "temperature": self.GOOGLE_TEMPERATURE,
                "max_tokens": self.GOOGLE_MAX_TOKENS,
            }
        elif provider == "huggingface":
            if not self.HF_API_TOKEN:
                raise ValueError("HF_API_TOKEN is required when using HuggingFace provider")
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}. Supported: openai, google, huggingface")

    def get_fallback_llm_config(self):
        """
        Get fallback LLM configuration.
        
        Priority:
        1. If FALLBACK_LLM_PROVIDER and custom fields are provided, use those
        2. If FALLBACK_LLM_PROVIDER is set but no custom fields, use that provider's config
        3. If no fallback configured, defaults to small HuggingFace model
        """
        fallback_provider = self.FALLBACK_LLM_PROVIDER
        
        # Default to HuggingFace small model if no fallback configured
        if not fallback_provider:
            return {
                "provider": "huggingface",
                "api_key": self.FALLBACK_HF_API_TOKEN or self.HF_API_TOKEN,
                "model": self.FALLBACK_HF_MODEL,
                "temperature": self.FALLBACK_HF_TEMPERATURE,
                "max_tokens": self.FALLBACK_HF_MAX_TOKENS,
            }
        
        fallback_provider = fallback_provider.lower()
        
        # If custom fallback fields are provided, use them
        if self.FALLBACK_LLM_MODEL:
            api_key = self.FALLBACK_LLM_API_KEY
            
            # Try to get API key from provider-specific config if not explicitly set
            if not api_key:
                if fallback_provider == "openai":
                    api_key = self.OPENAI_API_KEY
                elif fallback_provider == "google":
                    api_key = self.GOOGLE_API_KEY
                elif fallback_provider == "huggingface":
                    api_key = self.HF_API_TOKEN
            
            if not api_key:
                raise ValueError(f"FALLBACK_LLM_API_KEY or {fallback_provider.upper()}_API_KEY is required")
            
            return {
                "provider": fallback_provider,
                "api_key": api_key,
                "model": self.FALLBACK_LLM_MODEL,
                "temperature": self.FALLBACK_LLM_TEMPERATURE or 0.7,
                "max_tokens": self.FALLBACK_LLM_MAX_TOKENS or 1000,
            }
        
        # Otherwise, use provider's default config
        if fallback_provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for fallback OpenAI provider")
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
            }
        elif fallback_provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for fallback Google provider")
            return {
                "provider": "google",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_MODEL,
                "temperature": self.GOOGLE_TEMPERATURE,
                "max_tokens": self.GOOGLE_MAX_TOKENS,
            }
        elif fallback_provider == "huggingface":
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unsupported fallback provider: {fallback_provider}. Supported: openai, google, huggingface")
    
    def _validate_fallback_config(self):
        """Validate that fallback provider/model is different from primary"""
        if not self.FALLBACK_LLM_PROVIDER:
            return
        
        primary_provider = self.LLM_PROVIDER.lower()
        fallback_provider = self.FALLBACK_LLM_PROVIDER.lower()
        
        # Get primary config
        primary_config = self.get_llm_config()
        
        # Get fallback config  
        fallback_config = self.get_fallback_llm_config()
        
        # Check if same provider and model
        if (primary_config["provider"] == fallback_config["provider"] and 
            primary_config["model"] == fallback_config["model"]):
            raise ValueError(
                f"Fallback LLM cannot be the same as primary LLM. "
                f"Primary: {primary_config['provider']}/{primary_config['model']}, "
                f"Fallback: {fallback_config['provider']}/{fallback_config['model']}"
            )
    
    def _validate_vector_db_config(self):
        """Validate vector database configuration based on environment"""
        vector_db = self.VECTOR_DB_PROVIDER.lower()
        
        # Validate provider is supported
        supported_dbs = {"chroma", "qdrant", "pinecone", "weaviate", "milvus"}
        if vector_db not in supported_dbs:
            raise ValueError(
                f"Unsupported VECTOR_DB_PROVIDER: {vector_db}. "
                f"Supported: {', '.join(supported_dbs)}"
            )
        
        # Production validation: Don't allow Chroma in production
        if self.ENVIRONMENT == "production" and vector_db == "chroma":
            raise ValueError(
                "Chroma is not recommended for production. "
                "Please use Qdrant, Pinecone, Weaviate, or Milvus instead."
            )
        
        # Validate required fields for each provider
        if vector_db == "qdrant":
            # If using Qdrant Cloud, URL and API key are required
            if self.QDRANT_URL:
                if not self.QDRANT_API_KEY:
                    raise ValueError("QDRANT_API_KEY is required when using Qdrant Cloud (QDRANT_URL is set)")
        
        elif vector_db == "pinecone":
            if not self.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY is required for Pinecone provider")
            if not self.PINECONE_ENVIRONMENT:
                raise ValueError("PINECONE_ENVIRONMENT is required for Pinecone provider")
        
        elif vector_db == "weaviate":
            # Weaviate can work with just URL in local mode
            pass
        
        elif vector_db == "milvus":
            # Milvus can work with defaults
            pass
    
    def _validate_embedding_config(self):
        """Validate embedding provider configuration"""
        embedding_provider = self.EMBEDDING_PROVIDER.lower()
        
        # Validate provider is supported
        supported_providers = {"openai", "google", "huggingface", "cohere", "voyage"}
        if embedding_provider not in supported_providers:
            raise ValueError(
                f"Unsupported EMBEDDING_PROVIDER: {embedding_provider}. "
                f"Supported: {', '.join(supported_providers)}"
            )
        
        # Validate required API keys for each provider
        if embedding_provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
        
        elif embedding_provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Google embeddings")
        
        elif embedding_provider == "cohere":
            if not self.COHERE_API_KEY:
                raise ValueError("COHERE_API_KEY is required for Cohere embeddings")
        
        elif embedding_provider == "voyage":
            if not self.VOYAGE_API_KEY:
                raise ValueError("VOYAGE_API_KEY is required for Voyage AI embeddings")
        
        # HuggingFace doesn't require API key for local models
    
    def get_embedding_config(self):
        """Get embedding configuration for the selected provider"""
        provider = self.EMBEDDING_PROVIDER.lower()
        
        if provider == "openai":
            config = {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_EMBEDDING_MODEL,
            }
            if self.OPENAI_EMBEDDING_DIMENSIONS:
                config["dimensions"] = self.OPENAI_EMBEDDING_DIMENSIONS
            return config
        
        elif provider == "google":
            config = {
                "provider": "google",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_EMBEDDING_MODEL,
                "task_type": self.GOOGLE_EMBEDDING_TASK_TYPE,
            }
            if self.GOOGLE_EMBEDDING_DIMENSIONS:
                config["dimensions"] = self.GOOGLE_EMBEDDING_DIMENSIONS
            return config
        
        elif provider == "huggingface":
            return {
                "provider": "huggingface",
                "model": self.HF_EMBEDDING_MODEL,
                "device": self.HF_EMBEDDING_DEVICE,
                "api_token": self.HF_API_TOKEN,  # Optional for public models
            }
        
        elif provider == "cohere":
            return {
                "provider": "cohere",
                "api_key": self.COHERE_API_KEY,
                "model": self.COHERE_EMBEDDING_MODEL,
                "input_type": self.COHERE_INPUT_TYPE,
            }
        
        elif provider == "voyage":
            return {
                "provider": "voyage",
                "api_key": self.VOYAGE_API_KEY,
                "model": self.VOYAGE_EMBEDDING_MODEL,
            }
        
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def get_vector_db_config(self):
        """Get vector database configuration for the selected provider"""
        provider = self.VECTOR_DB_PROVIDER.lower()
        
        if provider == "qdrant":
            config = {
                "provider": "qdrant",
                "collection_name": self.QDRANT_COLLECTION_NAME,
            }
            
            # Qdrant Cloud configuration
            if self.QDRANT_URL:
                config["url"] = self.QDRANT_URL
                config["api_key"] = self.QDRANT_API_KEY
            else:
                # Local Qdrant configuration
                config["host"] = self.QDRANT_HOST
                config["port"] = self.QDRANT_PORT
                config["grpc_port"] = self.QDRANT_GRPC_PORT
                config["prefer_grpc"] = self.QDRANT_PREFER_GRPC
            
            return config
        
        elif provider == "chroma":
            return {
                "provider": "chroma",
                "host": self.CHROMA_HOST,
                "port": self.CHROMA_PORT,
                "persist_directory": self.CHROMA_PERSIST_DIRECTORY,
                "collection_name": self.CHROMA_COLLECTION_NAME,
            }
        
        elif provider == "pinecone":
            return {
                "provider": "pinecone",
                "api_key": self.PINECONE_API_KEY,
                "environment": self.PINECONE_ENVIRONMENT,
                "index_name": self.PINECONE_INDEX_NAME,
            }
        
        elif provider == "weaviate":
            config = {
                "provider": "weaviate",
                "url": self.WEAVIATE_URL,
                "class_name": self.WEAVIATE_CLASS_NAME,
            }
            if self.WEAVIATE_API_KEY:
                config["api_key"] = self.WEAVIATE_API_KEY
            return config
        
        elif provider == "milvus":
            config = {
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

settings = Settings()