"""
Cache configuration settings for RAG Fortress.
"""

from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    """
    Cache-specific settings.
    
    Supports both Redis (production) and in-memory (development) backends.
    Automatically falls back to in-memory if Redis is unavailable.
    
    Priority: DB (cached, set via Settings class) → ENV → Field default
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Cache Behavior
    CACHE_ENABLED: bool = Field(True, env="CACHE_ENABLED")
    CACHE_BACKEND: str = Field("memory", env="CACHE_BACKEND")  # "redis" or "memory"
    CACHE_KEY_PREFIX: str = Field("rag_fortress", env="CACHE_KEY_PREFIX")
    
    # Redis Configuration
    CACHE_REDIS_URL: Optional[str] = Field(None, env="CACHE_REDIS_URL")
    CACHE_REDIS_HOST: str = Field("localhost", env="CACHE_REDIS_HOST")
    CACHE_REDIS_PORT: int = Field(6379, env="CACHE_REDIS_PORT")
    CACHE_REDIS_DB: int = Field(0, env="CACHE_REDIS_DB")
    CACHE_REDIS_PASSWORD: Optional[str] = Field(None, env="CACHE_REDIS_PASSWORD")
    CACHE_REDIS_SSL: bool = Field(False, env="CACHE_REDIS_SSL")
    
    # Advanced Redis Settings
    CACHE_REDIS_SOCKET_TIMEOUT: int = Field(5, env="CACHE_REDIS_SOCKET_TIMEOUT")
    CACHE_REDIS_SOCKET_KEEPALIVE: bool = Field(True, env="CACHE_REDIS_SOCKET_KEEPALIVE")
    CACHE_REDIS_MAX_CONNECTIONS: int = Field(50, env="CACHE_REDIS_MAX_CONNECTIONS")
    CACHE_REDIS_RETRY_ON_TIMEOUT: bool = Field(True, env="CACHE_REDIS_RETRY_ON_TIMEOUT")
    CACHE_REDIS_HEALTH_CHECK_INTERVAL: int = Field(30, env="CACHE_REDIS_HEALTH_CHECK_INTERVAL")
    
    # TTL Settings (Time To Live in seconds)
    CACHE_TTL_DEFAULT: int = Field(300, env="CACHE_TTL_DEFAULT")  # 5 minutes
    CACHE_TTL_STATS: int = Field(60, env="CACHE_TTL_STATS")  # 1 minute
    CACHE_TTL_CONFIG: int = Field(3600, env="CACHE_TTL_CONFIG")  # 1 hour
    CACHE_TTL_USER_DATA: int = Field(300, env="CACHE_TTL_USER_DATA")  # 5 minutes
    CACHE_TTL_SESSION: int = Field(1800, env="CACHE_TTL_SESSION")  # 30 minutes
    CACHE_TTL_HISTORY: int = Field(3600, env="CACHE_TTL_HISTORY")  # 1 hour (sensitive data)
    
    # Conversation History Caching
    ENABLE_CACHE_HISTORY_ENCRYPTION: bool = Field(False, env="ENABLE_CACHE_HISTORY_ENCRYPTION")  # Encrypt history in cache
    
    # ==============================================================================
    # SEMANTIC CACHE - Two-Tier System (Response + Context)
    # Each tier works independently - enable the ones you need
    # ==============================================================================
    
    # Global semantic cache settings
    SEMANTIC_CACHE_INDEX_NAME: str = Field("semantic_cache", env="SEMANTIC_CACHE_INDEX_NAME")
    SEMANTIC_CACHE_VECTOR_DIM: int = Field(384, env="SEMANTIC_CACHE_VECTOR_DIM")  # Typical for many embedding models
    
    # Response-level cache (caches final LLM responses)
    ENABLE_RESPONSE_CACHE: bool = Field(False, env="ENABLE_RESPONSE_CACHE")
    RESPONSE_CACHE_TTL_MINUTES: int = Field(60, env="RESPONSE_CACHE_TTL_MINUTES")  # 60 minutes (1 hour)
    RESPONSE_CACHE_MAX_ENTRIES: int = Field(1, env="RESPONSE_CACHE_MAX_ENTRIES")  # Max variations per cluster (1=single, >1=variations)
    RESPONSE_CACHE_DISTANCE_THRESHOLD: float = Field(0.1, env="RESPONSE_CACHE_DISTANCE_THRESHOLD")  # More lenient
    RESPONSE_CACHE_ENCRYPT: bool = Field(False, env="RESPONSE_CACHE_ENCRYPT")
    
    # Context-level cache (caches retrieved documents before LLM)
    ENABLE_CONTEXT_CACHE: bool = Field(False, env="ENABLE_CONTEXT_CACHE")
    CONTEXT_CACHE_TTL_MINUTES: int = Field(120, env="CONTEXT_CACHE_TTL_MINUTES")  # 120 minutes (2 hours)
    CONTEXT_CACHE_MAX_ENTRIES: int = Field(1, env="CONTEXT_CACHE_MAX_ENTRIES")  # Max variations per cluster (1=single, >1=variations)
    CONTEXT_CACHE_DISTANCE_THRESHOLD: float = Field(0.05, env="CONTEXT_CACHE_DISTANCE_THRESHOLD")  # Stricter
    CONTEXT_CACHE_ENCRYPT: bool = Field(False, env="CONTEXT_CACHE_ENCRYPT")
    
    def get_redis_url(self) -> str:
        """
        Build Redis URL from components if not explicitly set.
        
        Returns:
            Redis connection URL in format: redis[s]://[:password@]host:port/db
        """
        if self.CACHE_REDIS_URL:
            return self.CACHE_REDIS_URL
        
        auth = f":{self.CACHE_REDIS_PASSWORD}@" if self.CACHE_REDIS_PASSWORD else ""
        protocol = "rediss" if self.CACHE_REDIS_SSL else "redis"
        return f"{protocol}://{auth}{self.CACHE_REDIS_HOST}:{self.CACHE_REDIS_PORT}/{self.CACHE_REDIS_DB}"
    
    def get_redis_options(self) -> dict:
        """
        Get Redis connection options for advanced configuration.
        
        Returns:
            Dict of Redis client options
        """
        return {
            "socket_connect_timeout": self.CACHE_REDIS_SOCKET_TIMEOUT,
            "socket_keepalive": self.CACHE_REDIS_SOCKET_KEEPALIVE,
            "max_connections": self.CACHE_REDIS_MAX_CONNECTIONS,
            "retry_on_timeout": self.CACHE_REDIS_RETRY_ON_TIMEOUT,
            "health_check_interval": self.CACHE_REDIS_HEALTH_CHECK_INTERVAL,
        }
    
    def get_semantic_cache_config(self) -> Dict[str, Any]:
        """Get semantic cache configuration as dict."""
        return {
            # Global
            "index_name": self.SEMANTIC_CACHE_INDEX_NAME,
            "vector_dim": self.SEMANTIC_CACHE_VECTOR_DIM,
            
            # Response cache
            "response": {
                "enabled": self.ENABLE_RESPONSE_CACHE,
                "ttl_seconds": self.RESPONSE_CACHE_TTL_MINUTES * 60,
                "max_entries": self.RESPONSE_CACHE_MAX_ENTRIES,
                "distance_threshold": self.RESPONSE_CACHE_DISTANCE_THRESHOLD,
                "encrypt": self.RESPONSE_CACHE_ENCRYPT,
            },
            
            # Context cache
            "context": {
                "enabled": self.ENABLE_CONTEXT_CACHE,
                "ttl_seconds": self.CONTEXT_CACHE_TTL_MINUTES * 60,
                "max_entries": self.CONTEXT_CACHE_MAX_ENTRIES,
                "distance_threshold": self.CONTEXT_CACHE_DISTANCE_THRESHOLD,
                "encrypt": self.CONTEXT_CACHE_ENCRYPT,
            }
        }


# Global cache settings instance
cache_settings = CacheSettings()
