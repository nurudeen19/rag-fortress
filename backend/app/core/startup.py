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
from app.core.cache import (
    initialize_cache,
    close_cache,
    get_cache
)
from app.core.events import (
    get_event_bus,
    init_event_handlers,
)
from app.core.email_client import init_email_client
from app.core.embedding_factory import get_embedding_provider
from app.core.llm_factory import (
    get_internal_llm_provider,
    get_llm_provider,
    get_fallback_llm_provider
)
from app.services.llm.classifier_llm import get_classifier_llm
from app.core.vector_store_factory import get_vector_store, get_retriever
from app.core.database import DatabaseManager
from app.core.settings_loader import load_settings_by_category
from app.config import (
    settings as settings_module,
    settings,
    DatabaseSettings,
    Settings
)
from app.config.cache_settings import cache_settings
from app.jobs import get_job_manager
from app.jobs.integration import JobQueueIntegration
from app.jobs.bootstrap import init_jobs
from app.services.vector_store.reranker import get_reranker_service


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
        self.classifier_llm_provider = None
    
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
            await self._initialize_llm()
            await self._initialize_fallback_llm()

            # ========== STEP 7: Internal LLM Provider (optional) ==========
            if settings.llm_settings.USE_INTERNAL_LLM:
                await self._initialize_internal_llm()
            
            # ========== STEP 8: Classifier/Decomposer LLM (optional) ==========
            if settings.llm_settings.ENABLE_LLM_CLASSIFIER or settings.llm_settings.ENABLE_QUERY_DECOMPOSER:
                await self._initialize_classifier_llm()
            
            # ========== STEP 9: Validate decomposer/reranker configuration ==========
            self._validate_decomposer_reranker_config()
            
            # ========== STEP 10: Reranker (OPTIONAL) ==========
            # Reranker initialization/validation moved to setup.py to avoid
            # performing model availability checks on every application startup.
            # The reranker service will still be lazy-loaded on first use.
            
            # ========== STEP 9: Email Client (OPTIONAL) ==========
            await self._initialize_email_client()
            
            # ========== STEP 10: Event Bus (OPTIONAL) ==========
            # Initialize event handlers for background task processing
            init_event_handlers()
            
            # ========== STEP 11: Job Queue (OPTIONAL, at end) ==========
            # Jobs scheduled last to ensure all dependencies are ready
            await self._initialize_job_queue()

            self.initialized = True
            logger.info("✓ Application initialization completed successfully")
        
        except Exception as e:
            logger.error(f"✗ Application initialization failed: {e}", exc_info=True)
            raise
    
    async def _initialize_database(self):
        """Initialize database connection and create tables (without seeding)."""

        try:
            # Create database manager
            db_settings = DatabaseSettings()
            self.database_manager = DatabaseManager(db_settings)
            
            # Create async engine
            await self.database_manager.create_async_engine()
            
            # Create session factory
            self.async_session_factory = self.database_manager.get_session_factory()
            
            # Health check
            is_healthy = await self.database_manager.health_check()
            if not is_healthy:
                raise RuntimeError("Database health check failed")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    async def _load_db_settings(self):
        """Load settings from database grouped by category and cache them."""
        try:
            
            # Load settings from DB grouped by category
            async with self.async_session_factory() as session:
                cached_settings = await load_settings_by_category(session)
            
            # Cache them for fast access
            if cached_settings and self.cache_manager:
                cache = get_cache()
                cache_key = "app_settings:all"
                await cache.set(cache_key, cached_settings, ttl=None)  # No expiry
            
            # Re-initialize global settings with cached values
            settings_module.settings = Settings(cached_settings=cached_settings)
            
        except Exception as e:
            logger.warning(f"⚠ Failed to load DB settings: {e}. Using ENV/defaults only.")
            # Don't block startup - ENV variables still work
    
    async def _initialize_job_queue(self):
        """Initialize job queue and schedule jobs via bootstrap."""
        try:
            if not self.async_session_factory:
                raise RuntimeError("Database must be initialized before job queue")
            
            # Start job manager (APScheduler)
            self.job_manager = get_job_manager()
            self.job_manager.start()
            
            # Setup job integration (bridges persistence + scheduling)
            self.job_integration = JobQueueIntegration(self.async_session_factory)
            
            # Schedule all jobs via centralized bootstrap
            await init_jobs(self.job_manager)
            
        except Exception as e:
            logger.warning(f"⚠ Job queue initialization skipped: {e}")
    
    async def _initialize_email_client(self):
        """Initialize email client for sending emails."""
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
        try:
            # Get embedding provider (creates instance if needed)
            self.embedding_provider = get_embedding_provider()
            
            # Test embedding generation to ensure it's working
            test_text = "Application startup test"
            test_embedding = self.embedding_provider.embed_query(test_text)
            
            if not test_embedding or len(test_embedding) == 0:
                raise RuntimeError("Embedding provider returned invalid result")
        
        except Exception as e:
            logger.error(f"Failed to initialize embedding provider: {e}")
            raise
    
    async def _initialize_vector_store(self):
        """Initialize vector store (optional - catches errors without blocking startup)."""
        try:
            # Get vector store with embeddings
            store = get_vector_store(
                embeddings=self.embedding_provider,
                provider=getattr(settings, "VECTOR_DB_PROVIDER", None)
            )
        
        except Exception as e:
            logger.warning(f"⚠ Vector store initialization skipped: {e}", exc_info=True)

    async def _initialize_llm(self):
        """Initialize LLM provider (optional - catches errors without blocking startup)."""
        try:
            # Get LLM provider (creates instance if needed)
            self.llm_provider = get_llm_provider()
        
        except Exception as e:
            logger.warning(f"⚠ LLM provider initialization skipped: {e}")

    async def _initialize_fallback_llm(self):
        """Initialize and warm up fallback LLM provider."""
        try:
            # Get fallback LLM provider (creates instance if needed)
            self.fallback_llm_provider = get_fallback_llm_provider()
            
            # Test fallback LLM invocation to ensure it's working
            test_prompt = "Hello"
            test_response = self.fallback_llm_provider.invoke(test_prompt)
            
            if not test_response:
                raise RuntimeError("Fallback LLM provider returned invalid result")
        
        except Exception as e:
            logger.error(f"Failed to initialize fallback LLM provider: {e}")
            raise

    async def _initialize_internal_llm(self):
        """Initialize internal LLM provider (optional)."""
        try:
            self.internal_llm_provider = get_internal_llm_provider()

        except Exception as e:
            logger.warning(f"⚠ Internal LLM initialization skipped: {e}")
    
    async def _initialize_classifier_llm(self):
        """Initialize classifier/decomposer LLM provider (optional)."""
        try:
            self.classifier_llm_provider = get_classifier_llm()

        except Exception as e:
            logger.warning(f"⚠ Classifier/decomposer LLM initialization skipped: {e}")
    
    async def _initialize_reranker(self):
        """Check if reranker is enabled and model is accessible.
        
        Validates reranker configuration by testing model availability.
        The model is downloaded once and cached locally for subsequent uses.
        """
        try:
            # Check if reranker is enabled in settings
            if not settings.app_settings.ENABLE_RERANKER:
                return
            
            logger.info("Reranker is enabled, testing model availability...")
            
            # Get reranker service instance
            reranker = get_reranker_service()
            
            # Test with minimal query to verify model works and is accessible
            # This triggers the download once (cached locally after)
            class SimpleDoc:
                def __init__(self, content):
                    self.page_content = content
            
            test_query = "test"
            test_docs = [SimpleDoc("test")]
            
            # Minimal rerank test - triggers actual model load/download
            test_results, test_scores = reranker.rerank(test_query, test_docs, top_k=1)
            
            if test_results and len(test_scores) > 0:
                logger.info(
                    f"Reranker ready (model: {reranker.model_name}, "
                    f"cached locally for subsequent queries)"
                )
            else:
                raise RuntimeError("Reranker model test returned no results")
        
        except ImportError as e:
            logger.error(f"Missing reranker dependency: {e}")
            logger.warning("Install with: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            logger.warning(
                "Reranker unavailable - set ENABLE_RERANKER=false to disable this check"
            )
    
    async def _initialize_retriever(self):
        """Initialize retriever (optional - catches errors without blocking startup)."""
        try:
            # Get retriever (creates instance from vector store)
            self.retriever = get_retriever(embeddings=self.embedding_provider)
        
        except Exception as e:
            logger.warning(f"⚠ Retriever initialization skipped: {e}")

    def _smoke_test_vector_store(self):
        """Lightweight vector store initialization check without ingestion."""
        try:
            store = get_vector_store(
                embeddings=self.embedding_provider,
                provider=getattr(settings, "VECTOR_DB_PROVIDER", None),
                collection_name=None,
            )
        except Exception as e:
            logger.error(f"Vector store smoke test failed: {e}", exc_info=True)
            # Do not block app startup for smoke test failures
    
    def _validate_decomposer_reranker_config(self):
        """Validate decomposer and reranker configuration, warn about consequences."""
        if not settings.llm_settings.ENABLE_QUERY_DECOMPOSER:
            return
        
        if not settings.app_settings.ENABLE_RERANKER:
            logger.warning(
                "⚠ CONFIGURATION WARNING: Query decomposer is enabled but reranker is disabled. "
                "This can lead to:\n"
                "  - Sub-optimal document ordering (not ranked against original query)\n"
                "  - Higher token usage (more potentially irrelevant documents sent to LLM)\n"
                "  - Lower quality responses\n"
                "RECOMMENDATION: Enable reranker by setting ENABLE_RERANKER=true"
            )
    
    async def _initialize_cache(self):
        """
        Initialize cache layer based on environment settings.        
        - If CACHE_ENABLED=true AND CACHE_BACKEND=redis → Initialize Redis
        - Otherwise → Use in-memory cache
        
        Graceful fallback: If any error occurs, always falls back to memory cache.
        """
        try:
            # Determine cache backend based entirely on .env settings
            should_use_redis = (
                settings.CACHE_ENABLED and 
                settings.CACHE_BACKEND.lower() == "redis"
            )
            
            # Prepare Redis configuration only if needed
            redis_url = cache_settings.get_redis_url() if should_use_redis else None
            redis_options = cache_settings.get_redis_options() if should_use_redis else None
            
            # Initialize cache with settings-driven configuration
            # Note: initialize_cache() has built-in Redis → Memory fallback
            self.cache_manager = await initialize_cache(
                redis_url=redis_url,
                use_redis=should_use_redis,
                redis_options=redis_options
            )
        
        except Exception as e:
            logger.warning(f"⚠ Cache initialization failed: {e}. Using fallback memory cache.")
            # Ensure we always have a cache - fallback to memory
            try:
                self.cache_manager = await initialize_cache(
                    redis_url=None,
                    use_redis=False,
                    redis_options=None
                )
            except Exception as fallback_error:
                logger.error(f"✗ Critical: Even memory cache failed: {fallback_error}")
                # This should never happen, but log it clearly if it does
    

    
    async def shutdown(self):
        """
        Cleanup resources on application shutdown.
        
        This is called during FastAPI shutdown event.
        """
        if not self.initialized:
            return
        
        logger.info("Starting application shutdown...")
        
        try:
            # Wait for pending event bus tasks
            logger.info("Waiting for pending event tasks...")
            
            event_bus = get_event_bus()
            await event_bus.wait_for_pending_tasks(timeout=5.0)
            
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
