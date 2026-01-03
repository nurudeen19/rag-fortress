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
    RERANKER_MODEL: str = Field("cross-encoder/ms-marco-MiniLM-L-6-v2", env="RERANKER_MODEL")
    RERANKER_API_KEY: Optional[str] = Field(None, env="RERANKER_API_KEY")
    
    # Reranker Behavior
    RERANKER_TOP_K: int = Field(5, env="RERANKER_TOP_K")
    RERANKER_SCORE_THRESHOLD: float = Field(0.5, env="RERANKER_SCORE_THRESHOLD")
    
    def get_reranker_config(self) -> dict:
        """
        Get reranker configuration based on selected provider.
        
        Returns:
            dict: Reranker configuration with provider, model, and credentials
        """
        provider = self.RERANKER_PROVIDER.lower()
        
        if provider == "huggingface":
            return {
                "provider": "huggingface",
                "model": self.RERANKER_MODEL
            }
        
        elif provider in ("cohere", "jina"):
            if not self.RERANKER_API_KEY:
                raise ValueError(f"RERANKER_API_KEY is required for {provider} reranker")
            
            return {
                "provider": provider,
                "api_key": self.RERANKER_API_KEY,
                "model": self.RERANKER_MODEL
            }
        
        else:
            raise ValueError(
                f"Unsupported reranker provider: {provider}. "
                f"Supported: huggingface, cohere, jina"
            )
    
    @field_validator("RERANKER_TOP_K")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Validate RERANKER_TOP_K is at least 1."""
        if v < 1:
            raise ValueError("RERANKER_TOP_K must be at least 1")
        return v
    
    @field_validator("RERANKER_SCORE_THRESHOLD")
    @classmethod
    def validate_score_threshold(cls, v: float) -> float:
        """Validate RERANKER_SCORE_THRESHOLD is between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("RERANKER_SCORE_THRESHOLD must be between 0.0 and 1.0")
        return v


# Create settings instance
reranker_settings = RerankerSettings()
