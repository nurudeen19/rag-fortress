"""
General application configuration settings.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """General application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="",
        # Disable JSON parsing for list fields - we'll handle it in validators
        env_parse_enums=None,
        # Allow extra fields from .env that aren't in the model
        extra="ignore",
    )
    
    # Application Info
    APP_NAME: str = Field("RAG Fortress", env="APP_NAME")
    APP_DESCRIPTION: str = Field(
        "Secure document intelligence platform",
        env="APP_DESCRIPTION"
    )
    APP_VERSION: str = Field("0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    
    # Demo Mode - Prevents destructive actions for public demos
    DEMO_MODE: bool = Field(False, env="DEMO_MODE")
    
    # Server Configuration
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    
    # Data Directories
    DATA_DIR: str = Field("./data", env="DATA_DIR")
    KNOWLEDGE_BASE_DIR: str = Field("./data/knowledge_base", env="KNOWLEDGE_BASE_DIR")
    PENDING_DIR: str = Field("./data/knowledge_base/pending", env="PENDING_DIR")
    PROCESSED_DIR: str = Field("./data/knowledge_base/processed", env="PROCESSED_DIR")
    
    # RAG Configuration
    CHUNK_SIZE: int = Field(1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(200, env="CHUNK_OVERLAP")
    MIN_TOP_K: int = Field(3, env="MIN_TOP_K")
    MAX_TOP_K: int = Field(10, env="MAX_TOP_K")
    RETRIEVAL_SCORE_THRESHOLD: float = Field(0.5, env="RETRIEVAL_SCORE_THRESHOLD")
    SIMILARITY_THRESHOLD: float = Field(0.7, env="SIMILARITY_THRESHOLD")
    
    # Reranker Configuration
    ENABLE_RERANKER: bool = Field(True, env="ENABLE_RERANKER")
    RERANKER_MODEL: str = Field("cross-encoder/ms-marco-MiniLM-L-6-v2", env="RERANKER_MODEL")
    RERANKER_TOP_K: int = Field(3, env="RERANKER_TOP_K")
    RERANKER_SCORE_THRESHOLD: float = Field(0.3, env="RERANKER_SCORE_THRESHOLD")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    SETTINGS_ENCRYPTION_KEY: str = Field(None, env="SETTINGS_ENCRYPTION_KEY")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    CORS_CREDENTIALS: bool = Field(True, env="CORS_CREDENTIALS")
    CORS_METHODS: List[str] = Field(
        default_factory=lambda: ["*"],
        env="CORS_METHODS"
    )
    CORS_HEADERS: List[str] = Field(
        default_factory=lambda: ["*"],
        env="CORS_HEADERS"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field("logs/rag_fortress.log", env="LOG_FILE")
    LOG_MAX_BYTES: int = Field(10485760, env="LOG_MAX_BYTES")  # 10MB
    LOG_BACKUP_COUNT: int = Field(5, env="LOG_BACKUP_COUNT")

    # Startup Options
    # If true, perform a very lightweight vector store initialization check
    # during application startup (no document ingestion).
    STARTUP_VECTOR_STORE_SMOKE_TEST: bool = Field(
        False, env="STARTUP_VECTOR_STORE_SMOKE_TEST"
    )

    # Admin Account Configuration
    ADMIN_USERNAME: str = Field("admin", env="ADMIN_USERNAME")
    ADMIN_EMAIL: str = Field("admin@ragfortress.com", env="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field("admin@RAGFortress123", env="ADMIN_PASSWORD")
    ADMIN_FIRSTNAME: str = Field("Admin", env="ADMIN_FIRSTNAME")
    ADMIN_LASTNAME: str = Field("User", env="ADMIN_LASTNAME")
    
    # Rate Limiting Configuration
    # General rate limiting for all endpoints (requests per minute)
    RATE_LIMIT_ENABLED: bool = Field(True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(1000, env="RATE_LIMIT_PER_HOUR")
    
    # Conversation endpoint rate limiting (stricter for RAG pipeline)
    CONVERSATION_RATE_LIMIT_PER_MINUTE: int = Field(10, env="CONVERSATION_RATE_LIMIT_PER_MINUTE")
    CONVERSATION_RATE_LIMIT_PER_HOUR: int = Field(100, env="CONVERSATION_RATE_LIMIT_PER_HOUR")
    
    # Conversation History Configuration
    # Number of previous message turns (user+assistant pairs) to include in context
    # Higher values provide more context but use more tokens
    CONVERSATION_HISTORY_TURNS: int = Field(3, env="CONVERSATION_HISTORY_TURNS")
    
    # Rate limit storage backend (memory or redis)
    RATE_LIMIT_STORAGE: str = Field("memory", env="RATE_LIMIT_STORAGE")
    RATE_LIMIT_REDIS_URL: Optional[str] = Field(None, env="RATE_LIMIT_REDIS_URL")
    
    # Job Configuration
    # Enable/disable individual scheduled jobs
    ENABLE_OVERRIDE_ESCALATION_JOB: bool = Field(True, env="ENABLE_OVERRIDE_ESCALATION_JOB")
    ENABLE_OVERRIDE_EXPIRATION_JOB: bool = Field(True, env="ENABLE_OVERRIDE_EXPIRATION_JOB")
    
    # Production Configuration
    SKIP_AUTO_SETUP: bool = Field(False, env="SKIP_AUTO_SETUP")
    UVICORN_WORKERS: int = Field(1, env="UVICORN_WORKERS")

    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        """Parse list fields from JSON array, comma-separated string, or list."""
        if isinstance(v, str):
            # Handle wildcard shorthand
            if v.strip() == "*":
                return ["*"]
            
            # Try to parse as JSON array first
            if v.strip().startswith("["):
                import json
                try:
                    parsed = json.loads(v)
                    # If wildcard in array, expand to explicit methods for CORS_METHODS
                    if isinstance(parsed, list) and "*" in parsed:
                        return ["*"]
                    return parsed
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, fall back to comma-separated
                    print(f"Warning: Failed to parse JSON array '{v}': {e}. Falling back to CSV parsing.")
                    pass
            
            # Parse as comma-separated string
            items = [item.strip() for item in v.split(",") if item.strip()]
            # Remove any accidental quotes from CSV parsing
            return [item.strip('"\'') for item in items]
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {allowed}, got '{v}'"
            )
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of {allowed}, got '{v}'"
            )
        return v_upper
    
    @field_validator("RATE_LIMIT_STORAGE")
    @classmethod
    def validate_rate_limit_storage(cls, v: str) -> str:
        """Validate rate limit storage backend."""
        allowed = {"memory", "redis"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(
                f"RATE_LIMIT_STORAGE must be one of {allowed}, got '{v}'"
            )
        return v_lower

    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is less than chunk size."""
        # Note: In Pydantic v2, we can't access other fields in field_validator
        # This will be validated in the Settings class after composition
        if v < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")
        return v

    @field_validator("SIMILARITY_THRESHOLD")
    @classmethod
    def validate_similarity_threshold(cls, v: float) -> float:
        """Ensure similarity threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1")
        return v

    def validate_rag_config(self):
        """Validate RAG-specific configuration."""
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError(
                f"CHUNK_OVERLAP ({self.CHUNK_OVERLAP}) must be less than "
                f"CHUNK_SIZE ({self.CHUNK_SIZE})"
            )
        
        if self.MIN_TOP_K < 1:
            raise ValueError("MIN_TOP_K must be at least 1")
        if self.MAX_TOP_K < self.MIN_TOP_K:
            raise ValueError("MAX_TOP_K must be greater than or equal to MIN_TOP_K")
        if not (0.0 <= self.RETRIEVAL_SCORE_THRESHOLD <= 1.0):
            raise ValueError("RETRIEVAL_SCORE_THRESHOLD must be between 0.0 and 1.0")
        
        # Reranker validation
        if self.RERANKER_TOP_K < 1:
            raise ValueError("RERANKER_TOP_K must be at least 1")
        if not (0.0 <= self.RERANKER_SCORE_THRESHOLD <= 1.0):
            raise ValueError("RERANKER_SCORE_THRESHOLD must be between 0.0 and 1.0")
        
        # Intent classifier validation
        if not (0.0 <= self.INTENT_CONFIDENCE_THRESHOLD <= 1.0):
            raise ValueError("INTENT_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        
        # Rate limiting validation
        if self.RATE_LIMIT_PER_MINUTE < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be at least 1")
        if self.RATE_LIMIT_PER_HOUR < 1:
            raise ValueError("RATE_LIMIT_PER_HOUR must be at least 1")
        if self.CONVERSATION_RATE_LIMIT_PER_MINUTE < 1:
            raise ValueError("CONVERSATION_RATE_LIMIT_PER_MINUTE must be at least 1")
        if self.CONVERSATION_RATE_LIMIT_PER_HOUR < 1:
            raise ValueError("CONVERSATION_RATE_LIMIT_PER_HOUR must be at least 1")
        if self.RATE_LIMIT_STORAGE == "redis" and not self.RATE_LIMIT_REDIS_URL:
            raise ValueError("RATE_LIMIT_REDIS_URL must be set when RATE_LIMIT_STORAGE is 'redis'")
