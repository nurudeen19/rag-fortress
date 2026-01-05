"""
Embedding provider configuration settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    """Embedding provider configuration."""
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # ============================================================================
    # EMBEDDING PROVIDER SELECTION
    # ============================================================================
    # Supported: openai, google, huggingface, cohere
    EMBEDDING_PROVIDER: str = Field("huggingface", env="EMBEDDING_PROVIDER")
    
    # ============================================================================
    # CONSOLIDATED EMBEDDING SETTINGS
    # ============================================================================
    # Generic fields for all providers
    EMBEDDING_API_KEY: Optional[str] = Field(None, env="EMBEDDING_API_KEY")
    EMBEDDING_MODEL: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Optional provider-specific fields (fill only when applicable)
    EMBEDDING_DIMENSIONS: Optional[int] = Field(None, env="EMBEDDING_DIMENSIONS")
    EMBEDDING_DEVICE: Optional[str] = Field(None, env="EMBEDDING_DEVICE")  # For HuggingFace
    EMBEDDING_TASK_TYPE: Optional[str] = Field(None, env="EMBEDDING_TASK_TYPE")  # For Google
    EMBEDDING_INPUT_TYPE: Optional[str] = Field(None, env="EMBEDDING_INPUT_TYPE")  # For Cohere
    

    def validate_config(self):
        """Validate embedding provider configuration."""
        embedding_provider = self.EMBEDDING_PROVIDER.lower()
        
        # Validate provider is supported
        supported_providers = {"openai", "google", "huggingface", "cohere"}
        if embedding_provider not in supported_providers:
            raise ValueError(
                f"Unsupported EMBEDDING_PROVIDER: {embedding_provider}. "
                f"Supported: {', '.join(supported_providers)}"
            )
        
        # Validate required API keys for each provider
        if embedding_provider == "openai":
            if not self.EMBEDDING_API_KEY:
                raise ValueError("EMBEDDING_API_KEY is required for OpenAI embeddings (set EMBEDDING_API_KEY)")
        
        elif embedding_provider == "google":
            if not self.EMBEDDING_API_KEY:
                raise ValueError("EMBEDDING_API_KEY is required for Google embeddings (set EMBEDDING_API_KEY)")
        
        elif embedding_provider == "cohere":
            if not self.EMBEDDING_API_KEY:
                raise ValueError("EMBEDDING_API_KEY is required for Cohere embeddings (set EMBEDDING_API_KEY)")
        
        # HuggingFace doesn't require API key for local models

    def get_embedding_config(self) -> dict:
        """Get embedding configuration for the selected provider."""
        provider = self.EMBEDDING_PROVIDER.lower()
        
        if provider == "openai":
            config = {
                "provider": "openai",
                "api_key": self.EMBEDDING_API_KEY,
                "model": self.EMBEDDING_MODEL,
            }
            if self.EMBEDDING_DIMENSIONS:
                config["dimensions"] = self.EMBEDDING_DIMENSIONS
            return config
        
        elif provider == "google":
            config = {
                "provider": "google",
                "api_key": self.EMBEDDING_API_KEY,
                "model": self.EMBEDDING_MODEL,
                "task_type": self.EMBEDDING_TASK_TYPE or "RETRIEVAL_DOCUMENT",
            }
            if self.EMBEDDING_DIMENSIONS:
                config["dimensions"] = self.EMBEDDING_DIMENSIONS
            return config
        
        elif provider == "huggingface":
            return {
                "provider": "huggingface",
                "model": self.EMBEDDING_MODEL,
                "device": self.EMBEDDING_DEVICE or "cpu",
                "api_token": self.EMBEDDING_API_KEY,
            }
        
        elif provider == "cohere":
            return {
                "provider": "cohere",
                "api_key": self.EMBEDDING_API_KEY,
                "model": self.EMBEDDING_MODEL,
                "input_type": self.EMBEDDING_INPUT_TYPE or "search_document",
            }
                
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
