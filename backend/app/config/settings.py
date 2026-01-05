"""
Main settings module that composes all configuration modules.
"""
import json
from typing import Any, Optional

from pydantic import TypeAdapter, field_validator
from pydantic_settings import SettingsConfigDict

from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embedding_settings import EmbeddingSettings
from .vectordb_settings import VectorDBSettings
from .database_settings import DatabaseSettings
from .email_settings import EmailSettings
from .cache_settings import CacheSettings
from .prompt_settings import PromptSettings
from .reranker_settings import RerankerSettings


# Database connection credentials must never be overridden by user-provided settings
PROTECTED_DATABASE_FIELDS = frozenset(DatabaseSettings.model_fields.keys())
PROTECTED_SETTING_CATEGORIES = frozenset({"database"})


FIELD_ALIASES = {
    # Application settings aliases (DB keys → env/model field names)
    "app_environment": "ENVIRONMENT",
    "cors_allow_origins": "CORS_ORIGINS",
    "debug_mode": "DEBUG",
}


class Settings(AppSettings, LLMSettings, EmbeddingSettings, VectorDBSettings, DatabaseSettings, EmailSettings, CacheSettings, PromptSettings, RerankerSettings):
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
            cached_settings: Dict of {category: {key: {"value": str, "is_sensitive": bool, "is_mutable": bool}}}
            **kwargs: Explicit override values (highest priority)
        """
        # Initialize parent first so Pydantic sets up attributes
        super().__init__(**kwargs)
        
        # NOW store encrypted metadata for lazy decryption (after Pydantic init)
        self._encrypted_settings = {}
    
    # Validators for empty string fields that should be None or typed conversions
    @field_validator("VECTOR_DB_PORT", "VECTOR_DB_GRPC_PORT", "EMBEDDING_DIMENSIONS", 
                    "LLM_TIMEOUT", "LLM_CONTEXT_SIZE", "LLM_N_THREADS", "LLM_N_BATCH",
                    "FALLBACK_LLM_TIMEOUT", "FALLBACK_LLM_MAX_TOKENS",
                    "CLASSIFIER_LLM_TIMEOUT", "DB_PORT", mode="before")
    @classmethod
    def validate_optional_int_fields(cls, v):
        """Convert empty strings to None for optional int fields."""
        if v == "" or v is None:
            return None
        return int(v) if isinstance(v, str) else v
    
    @field_validator("VECTOR_DB_PREFER_GRPC", mode="before")
    @classmethod
    def validate_optional_bool_fields(cls, v):
        """Convert empty strings to None for optional bool fields."""
        if v == "" or v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
        self._encrypted_overrides = {}  # Track which attrs have encrypted overrides
        self._cached_settings = cached_settings or {}
        
        if cached_settings:
            self._apply_cached_settings(cached_settings)
    
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

    @property
    def llm_settings(self) -> LLMSettings:
        """Expose the LLM settings namespace for backwards compatibility."""
        return self

    @property
    def app_settings(self) -> AppSettings:
        """Namespace alias for AppSettings consumers."""
        return self

    @property
    def embedding_settings(self) -> EmbeddingSettings:
        """Namespace alias for EmbeddingSettings consumers."""
        return self

    @property
    def vectordb_settings(self) -> VectorDBSettings:
        """Namespace alias for VectorDBSettings consumers."""
        return self

    @property
    def database_settings(self) -> DatabaseSettings:
        """Namespace alias for DatabaseSettings consumers."""
        return self

    @property
    def email_settings(self) -> EmailSettings:
        """Namespace alias for EmailSettings consumers."""
        return self

    @property
    def cache_settings(self) -> CacheSettings:
        """Namespace alias for CacheSettings consumers."""
        return self

    @property
    def prompt_settings(self) -> PromptSettings:
        """Namespace alias for PromptSettings consumers."""
        return self
    
    @property
    def reranker_settings(self) -> RerankerSettings:
        """Namespace alias for RerankerSettings consumers."""
        return self

    def _apply_cached_settings(self, cached_settings: dict) -> None:
        """Apply cached DB overrides while enforcing priority rules."""
        model_fields = getattr(self, "model_fields", {})
        for category, settings_dict in cached_settings.items():
            for key, metadata in settings_dict.items():
                value, is_sensitive, is_mutable = self._extract_metadata(metadata)
                if value is None:
                    continue
                field_name = self._resolve_field_name(key)
                if field_name not in model_fields:
                    continue
                if self._should_skip_override(field_name, category, is_mutable):
                    continue
                if is_sensitive:
                    self._encrypted_settings[field_name] = value
                    self._encrypted_overrides[field_name] = True
                else:
                    cast_value = self._cast_value(field_name, value)
                    setattr(self, field_name, cast_value)

    @staticmethod
    def _extract_metadata(metadata: Any) -> tuple[Any, bool, bool]:
        """Normalize metadata entry into (value, is_sensitive, is_mutable)."""
        if isinstance(metadata, dict):
            value = metadata.get("value")
            is_sensitive = metadata.get("is_sensitive", False)
            is_mutable = metadata.get("is_mutable", True)
        else:
            value = metadata
            is_sensitive = False
            is_mutable = True
        return value, is_sensitive, is_mutable

    def _resolve_field_name(self, raw_key: str) -> str:
        """Map DB key names to model field names."""
        key_lower = raw_key.lower()
        if key_lower in FIELD_ALIASES:
            return FIELD_ALIASES[key_lower]
        normalized = raw_key.upper().replace("-", "_").replace(".", "_")
        return normalized

    def _should_skip_override(self, field_name: str, category: Optional[str], is_mutable: bool) -> bool:
        """Determine if a cached override should be ignored."""
        if field_name in PROTECTED_DATABASE_FIELDS:
            return True
        if category and category.lower() in PROTECTED_SETTING_CATEGORIES:
            return True
        if not is_mutable:
            return True
        return False

    def _cast_value(self, field_name: str, raw_value: Any) -> Any:
        """Cast string DB values into the target field type."""
        field_info = getattr(self, "model_fields", {}).get(field_name)
        if not field_info:
            return raw_value
        value = raw_value
        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if stripped and stripped[0] in "[{":
                try:
                    value = json.loads(raw_value)
                except json.JSONDecodeError:
                    value = raw_value
        annotation = getattr(field_info, "annotation", Any) or Any
        try:
            adapter = TypeAdapter(annotation)
            return adapter.validate_python(value)
        except Exception:
            return value

# Global settings instance (will be initialized with cached values at startup)
settings = Settings()