"""
Database configuration settings for user data and application metadata.

Supports multiple database backends: PostgreSQL (recommended for production),
MySQL, and SQLite (development/testing).
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration for user data and application metadata."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Database Provider Selection
    DATABASE_PROVIDER: str = Field("sqlite", env="DATABASE_PROVIDER")
    
    # Unified Database Configuration (PostgreSQL & MySQL)
    # These fields are used by both PostgreSQL and MySQL
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: Optional[int] = Field(None, env="DB_PORT")  # Auto-set based on provider if None
    DB_USER: str = Field("rag_fortress", env="DB_USER")
    DB_PASSWORD: Optional[str] = Field(None, env="DB_PASSWORD")
    DB_NAME: str = Field("rag_fortress", env="DB_NAME")
    
    # PostgreSQL-Specific Configuration
    POSTGRES_SSL_MODE: str = Field("prefer", env="POSTGRES_SSL_MODE")  # disable, allow, prefer, require, verify-ca, verify-full
    
    # MySQL-Specific Configuration
    MYSQL_CHARSET: str = Field("utf8mb4", env="MYSQL_CHARSET")
    
    # SQLite Configuration (Development/Testing)
    SQLITE_PATH: str = Field("./rag_fortress.db", env="SQLITE_PATH")
    SQLITE_CHECK_SAME_THREAD: bool = Field(False, env="SQLITE_CHECK_SAME_THREAD")
    
    # Connection Pool Settings (PostgreSQL & MySQL)
    DB_POOL_SIZE: int = Field(5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(30, env="DB_POOL_TIMEOUT")  # seconds
    DB_POOL_RECYCLE: int = Field(3600, env="DB_POOL_RECYCLE")  # seconds
    DB_ECHO: bool = Field(False, env="DB_ECHO")  # Log SQL queries
    
    # Migration Settings
    DB_AUTO_MIGRATE: bool = Field(False, env="DB_AUTO_MIGRATE")
    DB_DROP_ALL: bool = Field(False, env="DB_DROP_ALL")  # Dangerous! Only for development

    @field_validator("DB_PORT", mode="before")
    @classmethod
    def parse_db_port(cls, v):
        """Handle empty string for DB_PORT."""
        if v == "" or v is None:
            return None
        return int(v)

    @field_validator("DATABASE_PROVIDER")
    @classmethod
    def validate_database_provider(cls, v: str) -> str:
        """Validate database provider."""
        allowed = {"postgresql", "postgres", "mysql", "sqlite"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(
                f"DATABASE_PROVIDER must be one of {allowed}, got '{v}'"
            )
        # Normalize postgres/postgresql
        if v_lower in {"postgres", "postgresql"}:
            return "postgresql"
        return v_lower

    @field_validator("POSTGRES_SSL_MODE")
    @classmethod
    def validate_postgres_ssl_mode(cls, v: str) -> str:
        """Validate PostgreSQL SSL mode."""
        allowed = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
        if v.lower() not in allowed:
            raise ValueError(
                f"POSTGRES_SSL_MODE must be one of {allowed}, got '{v}'"
            )
        return v.lower()

    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int) -> int:
        """Validate pool size is positive."""
        if v < 1:
            raise ValueError("DB_POOL_SIZE must be at least 1")
        return v

    @field_validator("DB_MAX_OVERFLOW")
    @classmethod
    def validate_max_overflow(cls, v: int) -> int:
        """Validate max overflow is non-negative."""
        if v < 0:
            raise ValueError("DB_MAX_OVERFLOW must be non-negative")
        return v

    def _get_port(self) -> int:
        """Get the appropriate port based on provider."""
        if self.DB_PORT is not None:
            return self.DB_PORT
        
        provider = self.DATABASE_PROVIDER.lower()
        if provider == "postgresql":
            return 5432
        elif provider == "mysql":
            return 3306
        else:
            return 5432  # Default

    def validate_config(self, environment: str):
        """Validate database configuration based on environment and provider."""
        provider = self.DATABASE_PROVIDER.lower()
        
        # Production validation: Don't allow SQLite in production
        if environment == "production" and provider == "sqlite":
            raise ValueError(
                "SQLite is not recommended for production. "
                "Please use PostgreSQL or MySQL instead."
            )
        
        # Validate required credentials for each provider
        if provider == "postgresql":
            if not self.DB_PASSWORD and environment == "production":
                raise ValueError(
                    "DB_PASSWORD is required for PostgreSQL in production"
                )
        
        elif provider == "mysql":
            if not self.DB_PASSWORD and environment == "production":
                raise ValueError(
                    "DB_PASSWORD is required for MySQL in production"
                )
        
        # Validate dangerous flags
        if self.DB_DROP_ALL and environment == "production":
            raise ValueError(
                "DB_DROP_ALL=True is not allowed in production! "
                "This would delete all data."
            )

    def get_database_url(self) -> str:
        """
        Get SQLAlchemy database URL for the selected provider.
        
        Returns:
            str: SQLAlchemy-compatible database URL
            
        Examples:
            PostgreSQL: postgresql://user:pass@localhost:5432/dbname
            MySQL: mysql+pymysql://user:pass@localhost:3306/dbname
            SQLite: sqlite:///./rag_fortress.db
        """
        provider = self.DATABASE_PROVIDER.lower()
        
        if provider == "postgresql":
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            port = self._get_port()
            url = (
                f"postgresql://{self.DB_USER}{password}"
                f"@{self.DB_HOST}:{port}/{self.DB_NAME}"
            )
            
            # Add SSL mode if not default
            if self.POSTGRES_SSL_MODE != "prefer":
                url += f"?sslmode={self.POSTGRES_SSL_MODE}"
            
            return url
        
        elif provider == "mysql":
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            port = self._get_port()
            url = (
                f"mysql+pymysql://{self.DB_USER}{password}"
                f"@{self.DB_HOST}:{port}/{self.DB_NAME}"
            )
            
            # Add charset
            url += f"?charset={self.MYSQL_CHARSET}"
            
            return url
        
        elif provider == "sqlite":
            # SQLite uses file path
            return f"sqlite:///{self.SQLITE_PATH}"
        
        else:
            raise ValueError(f"Unsupported database provider: {provider}")

    def get_database_config(self) -> dict:
        """
        Get complete database configuration including connection pool settings.
        
        Returns:
            dict: Database configuration for SQLAlchemy engine
        """
        provider = self.DATABASE_PROVIDER.lower()
        
        config = {
            "provider": provider,
            "url": self.get_database_url(),
            "echo": self.DB_ECHO,
        }
        
        # Add connection pool settings for PostgreSQL and MySQL
        if provider in {"postgresql", "mysql"}:
            config.update({
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_recycle": self.DB_POOL_RECYCLE,
            })
        
        # Add SQLite-specific settings
        if provider == "sqlite":
            config["connect_args"] = {
                "check_same_thread": self.SQLITE_CHECK_SAME_THREAD
            }
        
        return config

    def get_async_database_url(self) -> str:
        """
        Get async SQLAlchemy database URL for the selected provider.
        
        Returns:
            str: Async SQLAlchemy-compatible database URL
            
        Examples:
            PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/dbname
            MySQL: mysql+aiomysql://user:pass@localhost:3306/dbname
            SQLite: sqlite+aiosqlite:///./rag_fortress.db
        """
        provider = self.DATABASE_PROVIDER.lower()
        
        if provider == "postgresql":
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            port = self._get_port()
            url = (
                f"postgresql+asyncpg://{self.DB_USER}{password}"
                f"@{self.DB_HOST}:{port}/{self.DB_NAME}"
            )
            
            if self.POSTGRES_SSL_MODE != "prefer":
                url += f"?sslmode={self.POSTGRES_SSL_MODE}"
            
            return url
        
        elif provider == "mysql":
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            port = self._get_port()
            url = (
                f"mysql+aiomysql://{self.DB_USER}{password}"
                f"@{self.DB_HOST}:{port}/{self.DB_NAME}"
            )
            
            url += f"?charset={self.MYSQL_CHARSET}"
            
            return url
        
        elif provider == "sqlite":
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        
        else:
            raise ValueError(f"Unsupported database provider: {provider}")
