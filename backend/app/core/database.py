"""
Database utilities for managing connections, sessions, and migrations.

This module provides utilities for database operations including session
management, connection pooling, and migration handling.
"""
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config.database_settings import DatabaseSettings
from app.models import Base
import logging
import warnings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections, sessions, and migrations."""
    
    def __init__(self, settings: DatabaseSettings):
        """Initialize database manager with settings."""
        self.settings = settings
        self.engine = None
        self.async_engine = None
        self.session_factory = None
    
    def create_engine(self):
        """Create synchronous SQLAlchemy engine."""
        config = self.settings.get_database_config()
        
        engine_kwargs = {
            "echo": config.get("echo", False),
        }
        
        # Add pool configuration for PostgreSQL and MySQL
        if config["provider"] in {"postgresql", "mysql"}:
            engine_kwargs.update({
                "pool_size": config.get("pool_size", 5),
                "max_overflow": config.get("max_overflow", 10),
                "pool_timeout": config.get("pool_timeout", 30),
                "pool_recycle": config.get("pool_recycle", 3600),
            })
        
        # Add SQLite-specific configuration
        if config["provider"] == "sqlite":
            engine_kwargs["connect_args"] = config.get("connect_args", {})
        
        # Build sync URL from config
        url = self.settings._get_sync_database_url()
        self.engine = create_engine(url, **engine_kwargs)
        return self.engine
    
    async def create_async_engine(self):
        """Create asynchronous SQLAlchemy engine."""
        config = self.settings.get_database_config()
        
        engine_kwargs = {
            "echo": config.get("echo", False),
        }
        
        # Add pool configuration for PostgreSQL and MySQL
        if config["provider"] in {"postgresql", "mysql"}:
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
        if config["provider"] == "sqlite":
            engine_kwargs["connect_args"] = config.get("connect_args", {})
        
        # Build async URL from config
        url = self.settings._get_async_database_url()
        self.async_engine = create_async_engine(url, **engine_kwargs)
        return self.async_engine
    
    async def get_session(self) -> AsyncSession:
        """Get an async database session."""
        if not self.session_factory:
            await self.create_async_engine()
            self.session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        
        return self.session_factory()
    
    def get_session_factory(self):
        """Get the session factory."""
        if not self.session_factory:
            # Note: This requires async_engine to be created first
            if not self.async_engine:
                raise RuntimeError("Async engine not created. Call create_async_engine() first.")
            self.session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self.session_factory
    
    async def create_all_tables(self):
        """Create all tables in the database."""
        if not self.async_engine:
            await self.create_async_engine()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("All database tables created successfully")
    
    async def drop_all_tables(self):
        """Drop all tables from the database."""
        if not self.async_engine:
            await self.create_async_engine()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
    
    def init_db_sync(self):
        """Initialize database synchronously (for CLI usage)."""
        if not self.engine:
            self.create_engine()
        
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")
    
    async def health_check(self) -> bool:
        """Check database connectivity and health."""
        try:
            if not self.async_engine:
                await self.create_async_engine()
            
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database health check passed")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def table_exists(self, table_name: str) -> bool:
        """
        Check if a specific table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            if not self.async_engine:
                await self.create_async_engine()
            
            # Get the inspector to check table existence
            from sqlalchemy import inspect
            
            async with self.async_engine.connect() as conn:
                inspector = inspect(conn.sync_connection)
                exists = table_name in inspector.get_table_names()
                return exists
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    async def get_missing_tables(self, table_names: list) -> list:
        """
        Check which tables are missing from the database.
        
        Args:
            table_names: List of table names to check
            
        Returns:
            List of missing table names
        """
        missing = []
        for table_name in table_names:
            exists = await self.table_exists(table_name)
            if not exists:
                missing.append(table_name)
        return missing
    
    async def close(self):
        """
        Close database connections.
        
        Suppresses harmless aiomysql cleanup warnings that occur when connections
        are finalized after the event loop has already been closed.
        This is a known issue on Windows with aiomysql/asyncio cleanup timing.
        """
        if self.async_engine:
            # Suppress the harmless "Event loop is closed" warning from aiomysql cleanup
            # This occurs during __del__ after the event loop has already closed
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeError)
                await self.async_engine.dispose()
            logger.info("Database connections closed")
    
    async def close_connection(self):
        """Alias for close() for consistency."""
        await self.close()


# Module-level instance (to be initialized by the application)
db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create the database manager instance."""
    global db_manager
    if db_manager is None:
        settings = DatabaseSettings()
        db_manager = DatabaseManager(settings)
    return db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database sessions."""
    manager = await get_db_manager()
    session = await manager.get_session()
    try:
        yield session
    finally:
        await session.close()


async def _initialize_db_manager():
    """Initialize the database manager asynchronously."""
    global db_manager
    if db_manager is None:
        settings = DatabaseSettings()
        db_manager = DatabaseManager(settings)
        await db_manager.create_async_engine()
    return db_manager


def get_async_session_factory():
    """
    Get the async session factory for direct use.
    
    Note: This is primarily for use in background jobs and CLI tools.
    For FastAPI route handlers, use the get_session() dependency instead.
    
    For CLI usage, call initialize_db_manager_sync() first before using this.
    """
    global db_manager
    
    if db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. "
            "In async contexts, call _initialize_db_manager() first. "
            "In sync contexts, call initialize_db_manager_sync() first."
        )
    
    return db_manager.get_session_factory()


async def get_fresh_async_session_factory():
    """
    Create a fresh async session factory bound to the CURRENT event loop.
    
    CRITICAL: Use this in background jobs that run in isolated event loops
    (via asyncio.run()). The regular get_async_session_factory() returns
    a factory bound to the main event loop, which will fail in isolated loops.
    
    This creates a new engine and session factory for the current loop context.
    """
    settings = DatabaseSettings()
    config = settings.get_database_config()
    
    engine_kwargs = {
        "echo": config.get("echo", False),
    }
    
    # Add pool configuration for PostgreSQL and MySQL
    if config["provider"] in {"postgresql", "mysql"}:
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
    if config["provider"] == "sqlite":
        engine_kwargs["connect_args"] = config.get("connect_args", {})
    
    # Build async URL and create fresh engine in current loop
    url = settings._get_async_database_url()
    fresh_engine = create_async_engine(url, **engine_kwargs)
    
    # Create session factory bound to this engine
    return async_sessionmaker(
        fresh_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def initialize_db_manager_sync():
    """
    Initialize database manager in a sync context (for CLI tools).
    
    This should be called once at the start of CLI commands.
    """
    global db_manager
    
    if db_manager is None:
        settings = DatabaseSettings()
        db_manager = DatabaseManager(settings)
        
        # Create event loop for initialization
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create the async engine
        loop.run_until_complete(db_manager.create_async_engine())
    
    return db_manager
