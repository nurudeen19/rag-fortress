"""
FastAPI Application Factory and Startup Configuration.
"""

import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from slowapi.errors import RateLimitExceeded

from app.config.settings import settings
from app.core import get_logger
from app.core.startup import get_startup_controller
from app.core.exceptions import register_exception_handlers
from app.middleware import setup_middlewares
from app.utils.rate_limiter import get_limiter, rate_limit_exceeded_handler

# Suppress langchain_core's Pydantic V1 compatibility warning on Python 3.14+
# This is a known issue with langchain_core that will be fixed in future versions
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater",
    category=UserWarning,
)

logger = get_logger(__name__)


async def run_background_setup():
    """
    Run setup (migrations + seeders) and then initialize services in background.
    This allows the server to start immediately and become ready after setup completes.
    """
    startup_controller = get_startup_controller()
    startup_controller.mark_setup_running()
    
    try:
        logger.info("🔧 Running background setup...")
        
        # Import setup functions
        try:
            from setup import (
                run_migrations,
                run_seeders,
                verify_setup,
                cleanup_postgres_enums
            )
        except ImportError as e:
            error_msg = f"Failed to import setup functions: {e}"
            logger.error(f"❌ {error_msg}")
            startup_controller.mark_setup_failed(error_msg)
            return
        
        # Check if setup is already complete
        logger.info("🔍 Checking if setup is already complete...")
        if await verify_setup():
            logger.info("✅ Setup already complete - proceeding with initialization")
        else:
            logger.info("📋 Setup needed - running migrations and seeders...")
            
            # Clean up PostgreSQL ENUM types
            await cleanup_postgres_enums()
            
            # Run migrations
            logger.info("📊 Running database migrations...")
            if not await run_migrations():
                error_msg = "Database migrations failed"
                startup_controller.mark_setup_failed(error_msg)
                return
            
            # Run essential seeders
            essential_seeders = ["admin", "departments"]
            logger.info(f"🌱 Running essential seeders: {', '.join(essential_seeders)}")
            if not await run_seeders(essential_seeders):
                error_msg = "Seeding failed"
                startup_controller.mark_setup_failed(error_msg)
                return
            
            # Verify setup
            logger.info("✅ Verifying setup...")
            if not await verify_setup():
                error_msg = "Setup verification failed"
                startup_controller.mark_setup_failed(error_msg)
                return
            
            logger.info("🎉 Setup completed successfully!")
        
        startup_controller.mark_setup_complete()
        
        # Now initialize all services
        logger.info("🚀 Initializing application services...")
        await startup_controller.initialize()
        startup_controller.mark_ready()
        
    except Exception as e:
        error_msg = f"Background setup failed: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        startup_controller.mark_setup_failed(error_msg)
    finally:
        # Flush logs
        for handler in logger.handlers:
            handler.flush()


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
    
    # Check if we should run setup in background
    if settings.ALLOW_SETUP_ON_START:
        import asyncio
        logger.info("🔧 ALLOW_SETUP_ON_START enabled - starting server immediately")
        logger.info("📡 Setup will run in background, check /health/ready for status")
        # Start setup task in background without blocking server startup
        asyncio.create_task(run_background_setup())
    else:
        # Normal startup - block until initialization completes
        try:
            await startup_controller.initialize()
            startup_controller.mark_ready()
            logger.info("Application is ready to handle requests")
        except Exception as e:
            logger.error(f"Startup failed: {e}", exc_info=True)
            raise
        finally:
            # Flush logs after startup (success or error)
            for handler in logger.handlers:
                handler.flush()
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down RAG Fortress Application")
    logger.info("=" * 60)
    
    await startup_controller.shutdown()
    logger.info("Application shutdown complete")
    
    # Final flush after shutdown
    for handler in logger.handlers:
        handler.flush()


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
    
    # Setup rate limiting
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    logger.info("Rate limiting configured")
    
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
    from app.routes.departments import router as departments_router
    from app.routes.notifications import router as notifications_router
    from app.routes.dashboard import router as dashboard_router
    from app.routes.conversation import router as conversation_router
    from app.routes.activity_log import router as activity_log_router
    from app.routes.admin import router as admin_router
    from app.routes.settings import router as settings_router
    from app.routes.override_requests import router as override_requests_router
    from app.routes.error_reports import router as error_reports_router, admin_router as error_reports_admin_router
    
    app.include_router(email_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(file_upload_router)
    app.include_router(jobs_router)
    app.include_router(departments_router, prefix="/api/v1/admin")
    app.include_router(notifications_router)
    app.include_router(dashboard_router)
    app.include_router(conversation_router)
    app.include_router(activity_log_router)
    app.include_router(admin_router)
    app.include_router(settings_router)
    app.include_router(override_requests_router)
    app.include_router(error_reports_router)
    app.include_router(error_reports_admin_router)

    # Static file serving for error report attachments
    error_report_dir = Path(settings.DATA_DIR) / "error_reports"
    error_report_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/static/error-reports",
        StaticFiles(directory=error_report_dir),
        name="error_report_images",
    )
    
    # Health check endpoints
    @app.get("/health")
    async def health_check():
        """Health check endpoint - liveness probe."""
        return {
            "status": "ok",
            "version": "1.0.0"
        }
    
    @app.get("/health/ready")
    async def readiness_check():
        """Readiness check endpoint - shows if app can handle traffic."""
        startup_controller = get_startup_controller()
        
        if startup_controller.is_ready():
            return {
                "status": "ready",
                "message": "Application is ready to receive traffic",
                "version": "1.0.0"
            }
        elif startup_controller.is_setup_running():
            return {
                "status": "not_ready",
                "message": "Setup is running in background, please try again later",
                "version": "1.0.0"
            }
        elif startup_controller.get_setup_error():
            return {
                "status": "error",
                "message": f"Setup failed: {startup_controller.get_setup_error()}",
                "version": "1.0.0"
            }
        else:
            return {
                "status": "not_ready",
                "message": "Application is starting, please try again later",
                "version": "1.0.0"
            }
    
    return app


# Create application instance
app = create_app()
