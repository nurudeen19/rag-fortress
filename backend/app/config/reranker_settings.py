"""
Reranker provider configuration settings.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RerankerSettings(BaseSettings):
    """Reranker provider configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Reranker Provider (huggingface, cohere, jina)
    RERANKER_PROVIDER: str = Field("huggingface", env="RERANKER_PROVIDER")
    RERANKER_MODEL: Optional[str] = Field(None, env="RERANKER_MODEL")
    RERANKER_API_KEY: Optional[str] = Field(None, env="RERANKER_API_KEY")
    
    # Reranker Behavior
    RERANKER_SCORE_THRESHOLD: float = Field(0.5, env="RERANKER_SCORE_THRESHOLD")
    
    def get_reranker_config(self) -> dict:
        """
        Get reranker configuration based on selected provider.
        
        Returns:
            dict: Reranker configuration with provider, model, and credentials
        """
        provider = self.RERANKER_PROVIDER.lower()
        
        if provider == "huggingface":
            model = self.RERANKER_MODEL or "cross-encoder/ms-marco-MiniLM-L-6-v2"
            return {
                "provider": "huggingface",
                "model": model
            }
        
        elif provider == "cohere":
            if not self.RERANKER_API_KEY:
                raise ValueError("RERANKER_API_KEY is required for cohere reranker")
            if not self.RERANKER_MODEL:
                raise ValueError(
                    "RERANKER_MODEL is required for cohere reranker. "
                    "Options: rerank-v4.0-pro, rerank-v4.0-fast, rerank-v3.5, rerank-english-v3.0"
                )
            
            return {
                "provider": "cohere",
                "api_key": self.RERANKER_API_KEY,
                "model": self.RERANKER_MODEL
            }
        
        elif provider == "jina":
            if not self.RERANKER_API_KEY:
                raise ValueError("RERANKER_API_KEY is required for jina reranker")
            
            config = {
                "provider": "jina",
                "api_key": self.RERANKER_API_KEY
            }
            
            # Jina has default model, only include if specified
            if self.RERANKER_MODEL:
                config["model"] = self.RERANKER_MODEL
            
            return config
        
        else:
            raise ValueError(
                f"Unsupported reranker provider: {provider}. "
                f"Supported: huggingface, cohere, jina"
            )
    
    @field_validator("RERANKER_SCORE_THRESHOLD")
    @classmethod
    def validate_score_threshold(cls, v: float) -> float:
        """Validate RERANKER_SCORE_THRESHOLD is between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("RERANKER_SCORE_THRESHOLD must be between 0.0 and 1.0")
        return v


# Create settings instance
reranker_settings = RerankerSettings()
