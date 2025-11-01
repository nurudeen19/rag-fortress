"""
Main settings module that composes all configuration modules.
"""
from pydantic_settings import BaseSettings

from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embedding_settings import EmbeddingSettings
from .vectordb_settings import VectorDBSettings


class Settings(AppSettings, LLMSettings, EmbeddingSettings, VectorDBSettings):
    """
    Main settings class that inherits from all specialized settings modules.
    
    This provides a unified interface to all application configuration while
    keeping the implementation modular and maintainable.
    """
    
    def validate_all(self):
        """
        Run all validation methods across all settings modules.
        """
        # Validate app-specific settings
        self.validate_rag_config()
        
        # Validate LLM configuration
        self.validate_llm_config()
        self.validate_fallback_config()
        
        # Validate embedding configuration
        self.validate_config()
        
        # Validate vector database configuration
        VectorDBSettings.validate_config(self, self.ENVIRONMENT)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()