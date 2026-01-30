"""
Embedding provider configuration settings.
"""
from typing import Optional
from pydantic import Field, field_validator
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
    
    # ============================================================================
    # REDISVL VECTORIZER SETTINGS (for semantic cache)
    # ============================================================================
    # RedisVL vectorizer can reuse existing embedding config or use separate configuration
    # ============================================================================
    REDISVL_USE_EXISTING_EMBEDDING: bool = Field(True, env="REDISVL_USE_EXISTING_EMBEDDING")
    
    # Separate RedisVL configuration (only used if REDISVL_USE_EXISTING_EMBEDDING=False)
    REDISVL_PROVIDER: Optional[str] = Field(None, env="REDISVL_PROVIDER")  # openai, cohere, huggingface
    REDISVL_API_KEY: Optional[str] = Field(None, env="REDISVL_API_KEY")
    REDISVL_MODEL: Optional[str] = Field(None, env="REDISVL_MODEL")
    REDISVL_INPUT_TYPE: Optional[str] = Field(None, env="REDISVL_INPUT_TYPE")  # For Cohere
    
    @field_validator("EMBEDDING_DIMENSIONS", mode="before")
    @classmethod
    def validate_embedding_dimensions(cls, v):
        """Convert empty strings to None for optional int field."""
        if v == "" or v is None:
            return None
        return int(v) if isinstance(v, str) else v
    

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
    
    def validate_redisvl_config(self):
        """
        Validate RedisVL configuration.
        Raises ValueError if configuration is invalid.
        """
        # If using existing embedding config, no additional validation needed
        if self.REDISVL_USE_EXISTING_EMBEDDING:
            return
        
        # Validate separate RedisVL configuration
        if not self.REDISVL_PROVIDER:
            raise ValueError(
                "REDISVL_PROVIDER is required when REDISVL_USE_EXISTING_EMBEDDING=false. "
                "Supported: openai, cohere, huggingface"
            )
        
        provider = self.REDISVL_PROVIDER.lower()
        supported_providers = {"openai", "cohere", "huggingface"}
        
        if provider not in supported_providers:
            raise ValueError(
                f"Unsupported REDISVL_PROVIDER: {provider}. "
                f"Supported: {', '.join(supported_providers)}"
            )
        
        # Validate required fields for each provider
        if not self.REDISVL_MODEL:
            raise ValueError("REDISVL_MODEL is required for RedisVL configuration")
        
        if provider in {"openai", "cohere"}:
            if not self.REDISVL_API_KEY:
                raise ValueError(
                    f"REDISVL_API_KEY is required for {provider.capitalize()} RedisVL provider"
                )
    
    def get_redisvl_config(self) -> dict:
        """
        Get RedisVL vectorizer configuration.
        
        Returns:
            dict: Configuration for RedisVL vectorizer
        """
        # Use existing embedding config if flag is set
        if self.REDISVL_USE_EXISTING_EMBEDDING:
            return self.get_embedding_config()
        
        # Use separate RedisVL configuration
        provider = self.REDISVL_PROVIDER.lower()
        
        if provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.REDISVL_API_KEY,
                "model": self.REDISVL_MODEL,
            }
        
        elif provider == "cohere":
            return {
                "provider": "cohere",
                "api_key": self.REDISVL_API_KEY,
                "model": self.REDISVL_MODEL,
                "input_type": self.REDISVL_INPUT_TYPE or "search_query",
            }
        
        elif provider == "huggingface":
            return {
                "provider": "huggingface",
                "model": self.REDISVL_MODEL,
            }
        
        else:
            raise ValueError(f"Unsupported RedisVL provider: {provider}. Supported: openai, cohere, huggingface")