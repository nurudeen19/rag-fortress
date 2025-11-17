"""
Synchronous database utilities for background jobs.

Provides sync database access for APScheduler and other sync contexts
where async/await cannot be used.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.config.database_settings import DatabaseSettings
from app.core import get_logger

logger = get_logger(__name__)

# Singleton sync engine for background jobs
_sync_engine = None
_sync_session_factory = None


def get_sync_engine():
    """Get or create synchronous SQLAlchemy engine."""
    global _sync_engine
    if _sync_engine is None:
        settings = DatabaseSettings()
        config = settings.get_database_config()
        provider = config["provider"]
        
        # Use the private URL builder from settings which handles sync drivers
        db_url = settings._get_sync_database_url()
        
        logger.info(
            f"Creating sync database engine: {provider}://"
            f"{config['host']}:{config['port']}/{config['database']}"
        )
        
        engine_kwargs = {
            "echo": config["echo"],
        }
        
        # Add connection pool settings for PostgreSQL and MySQL
        if provider in {"postgresql", "mysql"}:
            engine_kwargs.update({
                "pool_size": config.get("pool_size", 5),
                "max_overflow": config.get("max_overflow", 10),
                "pool_timeout": config.get("pool_timeout", 30),
                "pool_recycle": config.get("pool_recycle", 3600),
            })
        else:
            # SQLite doesn't support connection pooling
            engine_kwargs["poolclass"] = NullPool
        
        # Add SQLite-specific configuration
        if provider == "sqlite":
            engine_kwargs["connect_args"] = {
                "check_same_thread": config.get("check_same_thread", False)
            }
        
        _sync_engine = create_engine(db_url, **engine_kwargs)
    
    return _sync_engine


def get_sync_session() -> Session:
    """Get synchronous database session."""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(bind=engine)
    return _sync_session_factory()


