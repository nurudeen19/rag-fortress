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
        
        SECURITY: Sensitive values remain encrypted until accessed.
        
        Priority for each setting:
        1. Explicit kwargs (highest priority - for testing/overrides)
        2. Cached DB values (loaded at startup, decrypted on access)
        3. Environment variables (Pydantic reads from os.environ)
        4. Field defaults (lowest priority)
        
        Args:
            cached_settings: Dict of {category: {key: {"value": str, "is_sensitive": bool}}}
            **kwargs: Explicit override values (highest priority)
        """
        # Initialize parent first so Pydantic sets up attributes
        super().__init__(**kwargs)
        
        # NOW store encrypted metadata for lazy decryption (after Pydantic init)
        self._encrypted_settings = {}
        self._encrypted_overrides = {}  # Track which attrs have encrypted overrides
        
        # Process cached DB values
        if cached_settings:
            for category, settings_dict in cached_settings.items():
                for key, metadata in settings_dict.items():
                    if isinstance(metadata, dict):
                        value = metadata.get("value")
                        is_sensitive = metadata.get("is_sensitive", False)
                    else:
                        # Backward compatibility: plain value
                        value = metadata
                        is_sensitive = False
                    
                    if value is not None:  # Only use non-null DB values
                        # Convert snake_case key to UPPER_CASE env var format
                        env_var_name = key.upper()
                        
                        # Skip settings that don't exist as Pydantic fields
                        # This filters out test settings while allowing all real settings
                        try:
                            model_fields = self.model_fields
                            if env_var_name not in model_fields:
                                continue  # Skip non-existent fields
                        except AttributeError:
                            pass  # Fallback if model_fields doesn't exist
                        
                        if is_sensitive:
                            # Store encrypted value for lazy decryption
                            self._encrypted_settings[env_var_name] = value
                            # Mark this attribute as having encrypted override
                            self._encrypted_overrides[env_var_name] = True
                        else:
                            # Non-sensitive: DB value overrides ENV/defaults unconditionally
                            setattr(self, env_var_name, value)
    
    def __getattribute__(self, name: str):
        """
        Override attribute access to decrypt sensitive values on-demand.
        
        SECURITY: Decryption happens only when value is accessed, keeping
        encrypted values in cache/memory until needed.
        """
        # Check if this is an encrypted setting that needs decryption
        # Must check BEFORE getting the value to avoid infinite recursion
        try:
            encrypted_overrides = super().__getattribute__('_encrypted_overrides')
            if name in encrypted_overrides:
                # This attribute has an encrypted override - decrypt it
                encrypted_settings = super().__getattribute__('_encrypted_settings')
                encrypted_value = encrypted_settings[name]
                
                # Decrypt on access (happens in-process, not stored anywhere)
                from app.utils.encryption import decrypt_value
                return decrypt_value(encrypted_value)
        except (AttributeError, KeyError):
            # _encrypted_overrides not initialized yet, or key not encrypted
            pass
        
        # Get the attribute normally
        return super().__getattribute__(name)
    
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