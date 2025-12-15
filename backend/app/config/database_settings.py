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
    
    # Complete Database URL (takes precedence over individual settings)
    # Supports: postgresql://user:pass@host:port/db, mysql://user:pass@host:port/db, sqlite:///path
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
    
    # Database Provider Selection (used only if DATABASE_URL is not provided)
    DATABASE_PROVIDER: str = Field("postgresql", env="DATABASE_PROVIDER")
    
    # Unified Database Configuration (PostgreSQL & MySQL)
    # These fields are used by both PostgreSQL and MySQL (only if DATABASE_URL is not provided)
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

    def _get_sync_database_url(self) -> str:
        """
        Get synchronous database URL (internal use only).
        
        If DATABASE_URL is provided, it will be used directly.
        Otherwise, builds the URL from individual configuration fields.
        
        Prefer using get_database_config() for explicit host/port/credentials.
        This is primarily used internally for engine creation.
        
        Returns:
            str: SQLAlchemy-compatible database URL with sync drivers
            
        Examples:
            PostgreSQL: postgresql://user:pass@localhost:5432/dbname
            MySQL: mysql+pymysql://user:pass@localhost:3306/dbname
            SQLite: sqlite:///./rag_fortress.db
        """
        if self.DATABASE_URL:
            # Normalize the URL driver for sync operations if needed
            url = self.DATABASE_URL
            # Convert async drivers to sync if present
            url = url.replace("postgresql+asyncpg://", "postgresql://")
            url = url.replace("mysql+aiomysql://", "mysql+pymysql://")
            url = url.replace("sqlite+aiosqlite://", "sqlite:///")
            return url
        
        config = self.get_database_config()
        provider = config["provider"]
        
        if provider == "postgresql":
            password = f":{config['password']}" if config['password'] else ""
            url = (
                f"postgresql://{config['user']}{password}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            if config.get("ssl_mode") and config["ssl_mode"] != "prefer":
                url += f"?sslmode={config['ssl_mode']}"
            return url
        
        elif provider == "mysql":
            password = f":{config['password']}" if config['password'] else ""
            url = (
                f"mysql+pymysql://{config['user']}{password}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            if config.get("charset"):
                url += f"?charset={config['charset']}"
            return url
        
        elif provider == "sqlite":
            return f"sqlite:///{config['path']}"
        
        else:
            raise ValueError(f"Unsupported database provider: {provider}")

    def get_database_config(self) -> dict:
        """
        Get complete database configuration using host-based connection details.
        
        Returns:
            dict: Database configuration with host, port, user, password, and pool settings
        """
        provider = self.DATABASE_PROVIDER.lower()
        
        config = {
            "provider": provider,
            "host": self.DB_HOST,
            "port": self._get_port(),
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "database": self.DB_NAME,
            "echo": self.DB_ECHO,
        }
        
        # Add provider-specific settings
        if provider == "postgresql":
            config["ssl_mode"] = self.POSTGRES_SSL_MODE
            config.update({
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_recycle": self.DB_POOL_RECYCLE,
            })
        elif provider == "mysql":
            config["charset"] = self.MYSQL_CHARSET
            config.update({
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_recycle": self.DB_POOL_RECYCLE,
            })
        elif provider == "sqlite":
            config["path"] = self.SQLITE_PATH
            config["check_same_thread"] = self.SQLITE_CHECK_SAME_THREAD
        
        return config

    def _get_async_database_url(self) -> str:
        """
        Get async database URL (internal use only).
        
        If DATABASE_URL is provided, it will be used directly (or converted to async driver).
        Otherwise, builds the URL from individual configuration fields.
        
        Prefer using get_database_config() for explicit host/port/credentials.
        This is primarily used internally for async engine creation.
        
        Returns:
            str: Async SQLAlchemy-compatible database URL
            
        Examples:
            PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/dbname
            MySQL: mysql+aiomysql://user:pass@localhost:3306/dbname
            SQLite: sqlite+aiosqlite:///./rag_fortress.db
        """
        # If DATABASE_URL is provided, use it and convert to async driver if needed
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Convert sync drivers to async if needed
            if "postgresql://" in url and "postgresql+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            elif "mysql+pymysql://" in url:
                url = url.replace("mysql+pymysql://", "mysql+aiomysql://")
            elif "mysql://" in url and "mysql+aiomysql" not in url:
                url = url.replace("mysql://", "mysql+aiomysql://")
            elif "sqlite:///" in url and "sqlite+aiosqlite" not in url:
                url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
            
            # asyncpg doesn't support sslmode parameter, convert to ssl
            # This is PostgreSQL-specific: MySQL uses different SSL config via connect_args
            # Critical for Neon, Supabase, and other cloud PostgreSQL providers
            if "postgresql+asyncpg" in url and "sslmode=" in url:
                # Convert sslmode to ssl parameter for asyncpg
                url = url.replace("sslmode=disable", "ssl=false")
                url = url.replace("sslmode=allow", "ssl=prefer")
                url = url.replace("sslmode=prefer", "ssl=prefer")
                url = url.replace("sslmode=require", "ssl=require")
                url = url.replace("sslmode=verify-ca", "ssl=verify-ca")
                url = url.replace("sslmode=verify-full", "ssl=verify-full")
            
            return url
        
        config = self.get_database_config()
        provider = config["provider"]
        
        if provider == "postgresql":
            password = f":{config['password']}" if config['password'] else ""
            url = (
                f"postgresql+asyncpg://{config['user']}{password}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            # asyncpg uses 'ssl' parameter instead of 'sslmode'
            if config.get("ssl_mode") and config["ssl_mode"] != "prefer":
                ssl_mode = config["ssl_mode"]
                # Map sslmode values to asyncpg ssl parameter
                ssl_mapping = {
                    "disable": "false",
                    "allow": "prefer",
                    "prefer": "prefer",
                    "require": "require",
                    "verify-ca": "verify-ca",
                    "verify-full": "verify-full"
                }
                ssl_value = ssl_mapping.get(ssl_mode, "prefer")
                url += f"?ssl={ssl_value}"
            return url
        
        elif provider == "mysql":
            password = f":{config['password']}" if config['password'] else ""
            url = (
                f"mysql+aiomysql://{config['user']}{password}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            if config.get("charset"):
                url += f"?charset={config['charset']}"
            return url
        
        elif provider == "sqlite":
            return f"sqlite+aiosqlite:///{config['path']}"
        
        else:
            raise ValueError(f"Unsupported database provider: {provider}")
