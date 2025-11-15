"""
FastAPI Application Factory and Startup Configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config.settings import settings
from app.core import get_logger
from app.core.startup import get_startup_controller
from app.core.exceptions import register_exception_handlers
from app.middleware import setup_middlewares


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting RAG Fortress Application")
    logger.info("=" * 60)
    
    startup_controller = get_startup_controller()
    
    try:
        await startup_controller.initialize()
        logger.info("Application is ready to handle requests")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down RAG Fortress Application")
    logger.info("=" * 60)
    
    await startup_controller.shutdown()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="RAG Fortress API",
        description="Advanced RAG system with comprehensive document processing",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup all middlewares
    setup_middlewares(app)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routers
    from app.routes.email import router as email_router
    from app.routes.auth import router as auth_router
    from app.routes.users import router as users_router
    from app.routes.file_upload import router as file_upload_router
    from app.routes.jobs import router as jobs_router
    
    app.include_router(email_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(file_upload_router)
    app.include_router(jobs_router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        startup_controller = get_startup_controller()
        return {
            "status": "healthy" if startup_controller.is_ready() else "starting",
            "version": "1.0.0"
        }
    
    return app


# Create application instance
app = create_app()
