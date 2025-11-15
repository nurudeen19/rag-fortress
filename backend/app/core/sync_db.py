"""
Synchronous database utilities for background jobs.

Provides sync database access for APScheduler and other sync contexts
where async/await cannot be used.
"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)

# Singleton sync engine for background jobs
_sync_engine = None
_sync_session_factory = None


def get_sync_engine():
    """Get or create synchronous SQLAlchemy engine."""
    global _sync_engine
    if _sync_engine is None:
        db_url = settings.database_settings.get_database_url()
        logger.info(f"Creating sync database engine: {db_url.split('://')[0]}")
        _sync_engine = create_engine(
            db_url,
            echo=settings.database_settings.DB_ECHO,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )
    return _sync_engine


def get_sync_session() -> Session:
    """Get synchronous database session."""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(bind=engine)
    return _sync_session_factory()
