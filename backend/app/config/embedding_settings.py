"""
Embedding provider configuration settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class EmbeddingSettings(BaseSettings):
    """Embedding provider configuration."""
    
    # Provider selection (defaults to huggingface sentence-transformers)
    EMBEDDING_PROVIDER: str = Field("huggingface", env="EMBEDDING_PROVIDER")
    
    # OpenAI Embeddings
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    OPENAI_EMBEDDING_DIMENSIONS: Optional[int] = Field(None, env="OPENAI_EMBEDDING_DIMENSIONS")
    
    # Google Embeddings (Gemini API)
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    GOOGLE_EMBEDDING_MODEL: str = Field("gemini-embedding-001", env="GOOGLE_EMBEDDING_MODEL")
    GOOGLE_EMBEDDING_DIMENSIONS: Optional[int] = Field(None, env="GOOGLE_EMBEDDING_DIMENSIONS")
    GOOGLE_EMBEDDING_TASK_TYPE: str = Field("RETRIEVAL_DOCUMENT", env="GOOGLE_EMBEDDING_TASK_TYPE")
    
    # HuggingFace Embeddings (Sentence Transformers)
    HF_API_TOKEN: Optional[str] = Field(None, env="HF_API_TOKEN")
    HF_EMBEDDING_MODEL: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="HF_EMBEDDING_MODEL")
    HF_EMBEDDING_DEVICE: str = Field("cpu", env="HF_EMBEDDING_DEVICE")
    
    # Cohere Embeddings
    COHERE_API_KEY: Optional[str] = Field(None, env="COHERE_API_KEY")
    COHERE_EMBEDDING_MODEL: str = Field("embed-english-v3.0", env="COHERE_EMBEDDING_MODEL")
    COHERE_INPUT_TYPE: str = Field("search_document", env="COHERE_INPUT_TYPE")
    
    # Voyage AI Embeddings
    VOYAGE_API_KEY: Optional[str] = Field(None, env="VOYAGE_API_KEY")
    VOYAGE_EMBEDDING_MODEL: str = Field("voyage-2", env="VOYAGE_EMBEDDING_MODEL")

    def validate_config(self):
        """Validate embedding provider configuration."""
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

    def get_embedding_config(self) -> dict:
        """Get embedding configuration for the selected provider."""
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
                "api_token": self.HF_API_TOKEN,
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
