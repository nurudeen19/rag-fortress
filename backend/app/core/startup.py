"""
Application Startup Controller.
Initializes critical components on server start in proper order:

1. Database (first - everything depends on it)
2. Job Queue (for processing)
3. Embedding Provider (for vector operations)
4. Vector Store (uses embedding provider)
5. LLM Provider (for AI operations)
6. Email Client (for notifications)

Database seeding is NOT performed here - it's called via setup.py or CLI.
See app/seeders/ for seeding operations.
"""

from app.core import get_logger
from app.core.email_client import init_email_client
from app.core.embedding_factory import get_embedding_provider
from app.core.llm_factory import (
    get_internal_llm_provider,
    get_llm_provider,
    get_fallback_llm_provider,
    test_llm_provider,
)
from app.core.vector_store_factory import get_vector_store, get_retriever
from app.core.database import DatabaseManager
from app.config.settings import settings
from app.config.database_settings import DatabaseSettings
from app.jobs import get_job_manager
from app.jobs.integration import JobQueueIntegration


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
        self.job_manager = None
        self.job_integration = None
        self.email_client = None
        self.embedding_provider = None
        self.llm_provider = None
        self.fallback_llm_provider = None
        self.retriever = None
        self.cache_manager = None
        self.internal_llm_provider = None
    
    async def initialize(self):
        """
        Initialize all critical components in proper order.
        
        Order matters:
        1. Database (required by all other components)
        2. Job Queue (for task processing)
        3. Embedding Provider (for vector operations)
        4. Vector Store (uses embeddings)
        5. LLM Provider (optional AI operations)
        6. Email Client (optional notifications)
        
        This is called during FastAPI startup event.
        
        Note: Database seeding is NOT performed here. Use setup.py CLI command
        for first-time setup or run_seeders.py for additional seeding.
        """
        if self.initialized:
            logger.warning("StartupController already initialized")
            return
        
        logger.info("Starting application initialization...")
        
        try:
            # ========== STEP 1: Database (CRITICAL) ==========
            await self._initialize_database()
            
            # ========== STEP 2: Cache (CRITICAL for settings) ==========
            await self._initialize_cache()
            
            # ========== STEP 3: Load Settings from DB (CRITICAL) ==========
            await self._load_db_settings()
            
            # ========== STEP 4: Embedding Provider (CRITICAL) ==========
            await self._initialize_embeddings()
            
            # ========== STEP 5: Vector Store (CRITICAL) ==========
            await self._initialize_vector_store()
            
            # ========== STEP 6: LLM Provider (CRITICAL) ==========
            # await self._initialize_llm()
            # await self._initialize_fallback_llm()

            # ========== STEP 7: Internal LLM Provider (optional) ==========
            if settings.llm_settings.USE_INTERNAL_LLM:
                await self._initialize_internal_llm()
            
            # ========== STEP 7: Email Client (OPTIONAL) ==========
            await self._initialize_email_client()
            
            # ========== STEP 8: Job Queue (OPTIONAL, at end) ==========
            await self._initialize_job_queue()

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
            await self.database_manager.create_async_engine()
            
            # Create session factory
            self.async_session_factory = self.database_manager.get_session_factory()
            
            # Health check
            is_healthy = await self.database_manager.health_check()
            if not is_healthy:
                raise RuntimeError("Database health check failed")
            
            logger.info("✓ Database initialized successfully")
            logger.info("To seed the database, run: python setup.py")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    async def _load_db_settings(self):
        """Load settings from database grouped by category and cache them."""
        logger.info("Loading settings from database...")
        
        try:
            from app.core.settings_loader import load_settings_by_category
            from app.core.cache import get_cache
            from app.config.settings import Settings
            
            # Load settings from DB grouped by category
            async with self.async_session_factory() as session:
                cached_settings = await load_settings_by_category(session)
            
            # Cache them for fast access
            if cached_settings and self.cache_manager:
                cache = get_cache()
                cache_key = "app_settings:all"
                await cache.set(cache_key, cached_settings, ttl=None)  # No expiry
                logger.info(f"✓ Cached {sum(len(v) for v in cached_settings.values())} settings")
            
            # Re-initialize global settings with cached values
            from app.config import settings as settings_module
            settings_module.settings = Settings(cached_settings=cached_settings)
            logger.info("✓ Settings loaded with database values")
            
        except Exception as e:
            logger.warning(f"⚠ Failed to load DB settings: {e}. Using ENV/defaults only.")
            # Don't block startup - ENV variables still work
    
    async def _initialize_job_queue(self):
        """Initialize job queue (optional - catches errors without blocking startup)."""
        logger.info("Initializing job queue...")
        
        try:
            if not self.async_session_factory:
                raise RuntimeError("Database must be initialized before job queue")
            
            # Start job manager (APScheduler)
            self.job_manager = get_job_manager()
            self.job_manager.start()
            logger.info("✓ Job manager started")
            
            # Setup job integration (bridges persistence + scheduling)
            # Note: Job recovery is deferred - jobs are scheduled when created,
            # pending jobs will retry on next app restart
            self.job_integration = JobQueueIntegration(self.async_session_factory)
            logger.info("✓ Job queue initialized")
            
        except Exception as e:
            logger.warning(f"⚠ Job queue initialization skipped: {e}")
    
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
    
    async def _initialize_vector_store(self):
        """Initialize vector store (optional - catches errors without blocking startup)."""
        logger.info("Initializing vector store...")
        
        try:
            # Get vector store with embeddings
            store = get_vector_store(
                embeddings=self.embedding_provider,
                provider=getattr(settings, "VECTOR_DB_PROVIDER", None)
            )
            
            logger.info(f"✓ Vector store initialized (provider: {settings.VECTOR_DB_PROVIDER})")
        
        except Exception as e:
            logger.warning(f"⚠ Vector store initialization skipped: {e}", exc_info=True)

    async def _initialize_llm(self):
        """Initialize LLM provider (optional - catches errors without blocking startup)."""
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
            logger.warning(f"⚠ LLM provider initialization skipped: {e}")

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

    async def _initialize_internal_llm(self):
        """Initialize internal LLM provider (optional)."""
        logger.info("Initializing internal LLM provider...")

        try:
            self.internal_llm_provider = get_internal_llm_provider()

            if self.internal_llm_provider:
                logger.info("✓ Internal LLM provider initialized successfully")
            else:
                logger.info("Internal LLM provider is disabled or returned no instance")

        except Exception as e:
            logger.warning(f"⚠ Internal LLM initialization skipped: {e}")
    
    async def _initialize_retriever(self):
        """Initialize retriever (optional - catches errors without blocking startup)."""
        logger.info("Initializing retriever...")
        
        try:
            # Get retriever (creates instance from vector store)
            self.retriever = get_retriever(embeddings=self.embedding_provider)
            
            logger.info("✓ Retriever initialized successfully")
        
        except Exception as e:
            logger.warning(f"⚠ Retriever initialization skipped: {e}")

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
    
    async def _initialize_cache(self):
        """Initialize cache layer (optional - graceful fallback)."""
        logger.info("Initializing cache layer...")
        
        try:
            from app.core.cache import initialize_cache
            from app.config.cache_settings import cache_settings
            
            use_redis = settings.CACHE_BACKEND == "redis" and settings.CACHE_ENABLED
            redis_url = cache_settings.get_redis_url() if use_redis else None
            redis_options = cache_settings.get_redis_options() if use_redis else None
            
            self.cache_manager = await initialize_cache(
                redis_url=redis_url,
                use_redis=use_redis,
                redis_options=redis_options
            )
            
            logger.info(f"✓ Cache initialized ({settings.CACHE_BACKEND} backend)")
        
        except Exception as e:
            logger.warning(f"⚠ Cache initialization failed (continuing without cache): {e}")
            # Don't block startup - cache is optional
    
    async def shutdown(self):
        """
        Cleanup resources on application shutdown.
        
        This is called during FastAPI shutdown event.
        """
        if not self.initialized:
            return
        
        logger.info("Starting application shutdown...")
        
        try:
            # Shutdown cache
            if self.cache_manager:
                logger.info("Closing cache connections...")
                from app.core.cache import close_cache
                await close_cache()
            
            # Shutdown job manager
            if self.job_manager:
                logger.info("Shutting down job manager...")
                self.job_manager.shutdown(wait=True)
            
            # Close database connections
            if self.database_manager:
                logger.info("Closing database connections...")
                await self.database_manager.close_connection()
            
            # Shutdown email client
            if self.email_client:
                logger.info("Shutting down email client...")
                await self.email_client.shutdown()
            
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
