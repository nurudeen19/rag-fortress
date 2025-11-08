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
    APP_VERSION: str = Field("0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    
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
    TOP_K_RESULTS: int = Field(5, env="TOP_K_RESULTS")
    SIMILARITY_THRESHOLD: float = Field(0.7, env="SIMILARITY_THRESHOLD")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
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

    # Email Configuration (SMTP)
    SMTP_SERVER: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field("noreply@ragfortress.com", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field("RAG Fortress", env="SMTP_FROM_NAME")
    SMTP_USE_TLS: bool = Field(True, env="SMTP_USE_TLS")
    SMTP_USE_SSL: bool = Field(False, env="SMTP_USE_SSL")
    
    # Email Settings
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = Field(24 * 60, env="EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES")  # 24 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(60, env="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")  # 1 hour
    INVITE_TOKEN_EXPIRE_DAYS: int = Field(7, env="INVITE_TOKEN_EXPIRE_DAYS")  # 7 days
    
    # Frontend URLs for email links
    FRONTEND_URL: str = Field("http://localhost:5173", env="FRONTEND_URL")
    EMAIL_VERIFICATION_URL: str = Field("http://localhost:5173/verify-email", env="EMAIL_VERIFICATION_URL")
    PASSWORD_RESET_URL: str = Field("http://localhost:5173/reset-password", env="PASSWORD_RESET_URL")
    INVITE_URL: str = Field("http://localhost:5173/accept-invite", env="INVITE_URL")

    # Startup Options
    # If true, perform a very lightweight vector store initialization check
    # during application startup (no document ingestion).
    STARTUP_VECTOR_STORE_SMOKE_TEST: bool = Field(
        False, env="STARTUP_VECTOR_STORE_SMOKE_TEST"
    )

    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        """Parse list fields from comma-separated string or list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
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
        
        if self.TOP_K_RESULTS < 1:
            raise ValueError("TOP_K_RESULTS must be at least 1")

    def validate_email_config(self):
        """Validate email configuration."""
        # Only validate if SMTP is configured
        if self.SMTP_USERNAME and self.SMTP_PASSWORD:
            if self.SMTP_PORT < 1 or self.SMTP_PORT > 65535:
                raise ValueError(f"SMTP_PORT must be between 1 and 65535, got {self.SMTP_PORT}")
            
            if not self.SMTP_FROM_EMAIL:
                raise ValueError("SMTP_FROM_EMAIL is required when SMTP is configured")
            
            if self.SMTP_USE_TLS and self.SMTP_USE_SSL:
                raise ValueError("Cannot use both SMTP_USE_TLS and SMTP_USE_SSL")
        else:
            # Log warning but don't fail - email is optional
            pass
