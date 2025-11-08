"""
Main settings module that composes all configuration modules.
"""
from pydantic_settings import SettingsConfigDict

from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embedding_settings import EmbeddingSettings
from .vectordb_settings import VectorDBSettings
from .database_settings import DatabaseSettings


class Settings(AppSettings, LLMSettings, EmbeddingSettings, VectorDBSettings, DatabaseSettings):
    """
    Main settings class that inherits from all specialized settings modules.
    
    This provides a unified interface to all application configuration while
    keeping the implementation modular and maintainable.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    def validate_all(self):
        """
        Run all validation methods across all settings modules.
        """
        # Validate app-specific settings
        self.validate_rag_config()
        self.validate_email_config()
        
        # Validate LLM configuration
        self.validate_llm_config()
        self.validate_fallback_config()
        
        # Validate embedding configuration
        EmbeddingSettings.validate_config(self)
        
        # Validate vector database configuration
        VectorDBSettings.validate_config(self, self.ENVIRONMENT)
        
        # Validate database configuration
        DatabaseSettings.validate_config(self, self.ENVIRONMENT)

settings = Settings()