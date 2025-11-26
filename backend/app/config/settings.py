"""
Main settings module that composes all configuration modules.
"""
from pydantic_settings import SettingsConfigDict

from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embedding_settings import EmbeddingSettings
from .vectordb_settings import VectorDBSettings
from .database_settings import DatabaseSettings
from .email_settings import EmailSettings
from .cache_settings import CacheSettings


class Settings(AppSettings, LLMSettings, EmbeddingSettings, VectorDBSettings, DatabaseSettings, EmailSettings, CacheSettings):
    """
    Main settings class that inherits from all specialized settings modules.
    
    This provides a unified interface to all application configuration while
    keeping the implementation modular and maintainable.
    
    Supports loading from database cache with priority: DB → ENV → defaults
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    def __init__(self, cached_settings: dict = None, **kwargs):
        """
        Initialize settings with optional cached values from database.
        
        Args:
            cached_settings: Dict of {category: {key: value}} from database
            **kwargs: Additional override values
        """
        # Store cached settings for child classes to use
        self._cached_settings = cached_settings or {}
        
        # Initialize parent classes (Pydantic will handle Field defaults)
        super().__init__(**kwargs)
    
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
        EmbeddingSettings.validate_config(self)
        
        # Validate vector database configuration
        VectorDBSettings.validate_config(self, self.ENVIRONMENT)
        
        # Validate database configuration
        DatabaseSettings.validate_config(self, self.ENVIRONMENT)
        
        # Validate email configuration
        EmailSettings.validate_config(self)
    
    def get_cached_value(self, category: str, key: str) -> any:
        """
        Get a cached value from database settings.
        
        Args:
            category: Setting category (llm, cache, email, etc.)
            key: Setting key
        
        Returns:
            Cached value or None
        """
        return self._cached_settings.get(category, {}).get(key)

# Global settings instance (will be initialized with cached values at startup)
settings = Settings()