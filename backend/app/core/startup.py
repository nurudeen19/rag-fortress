"""
Application Startup Controller.
Initializes critical components on server start.

Database seeding is NOT performed here - it's called programmatically via CLI or scripts.
See app/core/seeders.py for seeding operations.
"""

from app.core import get_logger
from app.core.email_client import init_email_client
from app.core.embedding_factory import get_embedding_provider
from app.core.llm_factory import get_llm_provider, get_fallback_llm_provider, test_llm_provider
from app.core.vector_store_factory import get_vector_store, get_retriever
from app.core.database import DatabaseManager
from app.config.settings import settings
from app.config.database_settings import DatabaseSettings


logger = get_logger(__name__)


class StartupController:
    """
    Manages initialization of critical application components.
    
    Ensures all required services are ready before handling requests.
    """
    
    def __init__(self):
        self.initialized = False
        self.database_manager = None
        self.async_session_factory = None
        self.email_client = None
        self.embedding_provider = None
        self.llm_provider = None
        self.fallback_llm_provider = None
        self.retriever = None
    
    async def initialize(self):
        """
        Initialize all critical components.
        
        This is called during FastAPI startup event.
        
        Note: Database seeding is NOT performed here. Use run_seeders() CLI command
        or call DatabaseSeeder.seed_all() programmatically from scripts.
        """
        if self.initialized:
            logger.warning("StartupController already initialized")
            return
        
        logger.info("Starting application initialization...")
        
        try:
            # Initialize database connection and create tables
            await self._initialize_database()
            
            # Email client initialization
            await self._initialize_email_client()
            
            # Initialize embedding provider
            await self._initialize_embeddings()
            
            # Initialize LLM provider
            # await self._initialize_llm()
            
            # Initialize fallback LLM provider
            # await self._initialize_fallback_llm()
            
            # Initialize retriever
            # await self._initialize_retriever()

            # Future initializations will be added here:
            # - Vector store connection pool
            # - Cache warming
            # - Background job queue
            # - etc.
            
            self.initialized = True
            logger.info("✓ Application initialization completed successfully")
        
        except Exception as e:
            logger.error(f"✗ Application initialization failed: {e}", exc_info=True)
            raise
    
    async def _initialize_database(self):
        """Initialize database connection and create tables (without seeding)."""
        logger.info("Initializing database...")
        
        try:
            # Create database manager
            db_settings = DatabaseSettings()
            self.database_manager = DatabaseManager(db_settings)
            
            # Create async engine
            logger.info("Creating database engine...")
            self.database_manager.create_async_engine()
            
            # Create session factory
            self.async_session_factory = self.database_manager.get_session_factory()
            
            # Create tables
            logger.info("Creating database tables...")
            await self.database_manager.create_all_tables()
            
            logger.info("✓ Database initialized successfully")
            logger.info("To seed the database, run: python -m app.scripts.seed_database")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    async def _initialize_email_client(self):
        """Initialize email client for sending emails."""
        logger.info("Initializing email client...")
        
        try:
            # Initialize global email client
            self.email_client = init_email_client()
            
            # Initialize async components
            await self.email_client.initialize()
            
            if self.email_client.is_configured():
                logger.info("✓ Email client initialized and configured")
            else:
                logger.warning(
                    "⚠ Email client initialized but not configured "
                    "(missing SMTP credentials - email features will be disabled)"
                )
        
        except Exception as e:
            logger.error(f"Failed to initialize email client: {e}")
            # Don't raise - email is optional, app should still start
            logger.warning("Email features will be unavailable")
    
    async def _initialize_embeddings(self):
        """Initialize and warm up embedding provider."""
        logger.info("Initializing embedding provider...")
        
        try:
            # Get embedding provider (creates instance if needed)
            self.embedding_provider = get_embedding_provider()
            
            # Test embedding generation to ensure it's working
            test_text = "Application startup test"
            test_embedding = self.embedding_provider.embed_query(test_text)
            
            if test_embedding and len(test_embedding) > 0:
                logger.info(
                    f"✓ Embedding provider initialized "
                    f"(dimension: {len(test_embedding)})"
                )
            else:
                raise RuntimeError("Embedding provider returned invalid result")
        
        except Exception as e:
            logger.error(f"Failed to initialize embedding provider: {e}")
            raise
    
    async def _initialize_llm(self):
        """Initialize and warm up LLM provider."""
        logger.info("Initializing LLM provider...")
        
        try:
            # Get LLM provider (creates instance if needed)
            self.llm_provider = get_llm_provider()
            
            # Test LLM setup
            if test_llm_provider():
                logger.info(f"✓ LLM provider initialized successfully")
            else:
                raise RuntimeError("LLM provider test failed")
        
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise
    
    async def _initialize_fallback_llm(self):
        """Initialize and warm up fallback LLM provider."""
        logger.info("Initializing fallback LLM provider...")
        
        try:
            # Get fallback LLM provider (creates instance if needed)
            self.fallback_llm_provider = get_fallback_llm_provider()
            
            # Test fallback LLM invocation to ensure it's working
            test_prompt = "Hello"
            test_response = self.fallback_llm_provider.invoke(test_prompt)
            
            if test_response:
                logger.info(f"✓ Fallback LLM provider initialized successfully")
            else:
                raise RuntimeError("Fallback LLM provider returned invalid result")
        
        except Exception as e:
            logger.error(f"Failed to initialize fallback LLM provider: {e}")
            raise
    
    async def _initialize_retriever(self):
        """Initialize and warm up retriever."""
        logger.info("Initializing retriever...")
        
        try:
            # Get retriever (creates instance from vector store)
            self.retriever = get_retriever(embeddings=self.embedding_provider)
            
            logger.info("✓ Retriever initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise

    def _smoke_test_vector_store(self):
        """Lightweight vector store initialization check without ingestion."""
        try:
            logger.info("Running vector store smoke test (no ingestion)...")

            store = get_vector_store(
                embeddings=self.embedding_provider,
                provider=getattr(settings, "VECTOR_DB_PROVIDER", None),
                collection_name=None,
            )

            # FAISS returns None until created from documents
            if store is None:
                logger.info("✓ Vector store (FAISS) ready for on-demand creation")
            else:
                logger.info("✓ Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Vector store smoke test failed: {e}", exc_info=True)
            # Do not block app startup for smoke test failures
    
    async def shutdown(self):
        """
        Cleanup resources on application shutdown.
        
        This is called during FastAPI shutdown event.
        """
        if not self.initialized:
            return
        
        logger.info("Starting application shutdown...")
        
        try:
            # Close database connections
            if self.database_manager:
                logger.info("Closing database connections...")
                await self.database_manager.close_connection()
            
            # Shutdown email client
            if self.email_client:
                logger.info("Shutting down email client...")
                await self.email_client.shutdown()
            
            # Future cleanup tasks:
            # - Flush caches
            # - Stop background workers
            # - etc.
            
            logger.info("✓ Application shutdown completed")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        
        finally:
            self.initialized = False
    
    def is_ready(self) -> bool:
        """Check if application is ready to handle requests."""
        return self.initialized


# Global startup controller instance
_startup_controller = StartupController()


def get_startup_controller() -> StartupController:
    """Get the global startup controller instance."""
    return _startup_controller
