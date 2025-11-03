"""
Application Startup Controller.
Initializes critical components on server start.
"""

from app.core import get_logger
from app.core.embedding_factory import get_embedding_provider
from app.config.settings import settings
from app.services.vector_store.factory import get_vector_store


logger = get_logger(__name__)


class StartupController:
    """
    Manages initialization of critical application components.
    
    Ensures all required services are ready before handling requests.
    """
    
    def __init__(self):
        self.initialized = False
        self.embedding_provider = None
    
    async def initialize(self):
        """
        Initialize all critical components.
        
        This is called during FastAPI startup event.
        """
        if self.initialized:
            logger.warning("StartupController already initialized")
            return
        
        logger.info("Starting application initialization...")
        
        try:
            # Initialize embedding provider
            await self._initialize_embeddings()

            # Optional: very light vector store smoke test (no ingestion)
            # This is gated by env STARTUP_VECTOR_STORE_SMOKE_TEST to avoid
            # heavy operations or side effects during startup.
            if getattr(settings, "STARTUP_VECTOR_STORE_SMOKE_TEST", False):
                self._smoke_test_vector_store()
            
            # Future initializations will be added here:
            # - Vector store connection pool
            # - Database connections
            # - Cache warming
            # - Background job queue
            # - etc.
            
            self.initialized = True
            logger.info("✓ Application initialization completed successfully")
        
        except Exception as e:
            logger.error(f"✗ Application initialization failed: {e}", exc_info=True)
            raise
    
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
            # Future cleanup tasks:
            # - Close database connections
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
