#!/usr/bin/env python3
"""
Production server runner with automatic setup.

This script automatically sets up the RAG Fortress application on first run
and then starts the production server. It runs essential seeders (admin and
departments) to ensure the application is ready for production use.

Environment Variables (handled by Pydantic settings):
    SKIP_AUTO_SETUP=true       # Skip automatic setup and start server immediately (default: false)
    UVICORN_WORKERS=N          # Number of worker processes (default: 4)
    
All standard application environment variables from .env file are supported via Pydantic settings.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app.config.settings import settings
from app.core.logging import setup_logging

# Setup logging for production
setup_logging()
logger = logging.getLogger(__name__)


async def run_production_setup():
    """
    Automatically set up the project for production deployment.
    Only runs admin and departments seeders for minimal production setup.
    
    Returns:
        bool: True if setup succeeded or was already complete, False if failed
    """
    try:
        # Check if setup should be skipped
        if settings.SKIP_AUTO_SETUP:
            logger.info("⏭️  Auto-setup skipped (SKIP_AUTO_SETUP=true)")
            return True
        
        logger.info("🚀 Starting production setup...")
        
        # Import setup functions with error handling
        try:
            from setup import (
                run_migrations, 
                run_seeders, 
                verify_setup,
                cleanup_postgres_enums
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import setup functions: {e}")
            logger.error("💡 Ensure all dependencies are installed: pip install -r requirements.txt")
            return False
        
        # First check if setup is already complete
        logger.info("🔍 Checking if setup is already complete...")
        if await verify_setup():
            logger.info("✅ Setup already complete - skipping automatic setup")
            return True
        
        logger.info("📋 Setup needed - running automatic production setup...")
        
        # Clean up PostgreSQL ENUM types before migrations (prevents conflicts)
        await cleanup_postgres_enums()
        
        # Run database migrations
        logger.info("📊 Running database migrations...")
        if not await run_migrations():
            logger.error("❌ Database migrations failed")
            return False
        
        # Run only essential seeders for production
        essential_seeders = ["admin", "departments"]
        logger.info(f"🌱 Running essential seeders: {', '.join(essential_seeders)}")
        if not await run_seeders(essential_seeders):
            logger.error("❌ Seeding failed")
            return False
        
        # Verify setup completed successfully
        logger.info("✅ Verifying setup...")
        if not await verify_setup():
            logger.error("❌ Setup verification failed")
            return False
        
        logger.info("🎉 Production setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Production setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main production server entry point."""
    
    logger.info("=== RAG Fortress Production Server ===")
    
    # Use Pydantic settings for configuration
    workers = settings.UVICORN_WORKERS
    skip_setup = settings.SKIP_AUTO_SETUP
    
    if skip_setup:
        logger.info("⏭️  Skipping automatic setup (SKIP_AUTO_SETUP=true)")
    else:
        logger.info("🔧 Running automatic production setup...")
        setup_success = asyncio.run(run_production_setup())
        
        if not setup_success:
            logger.error("❌ Production setup failed - aborting server start")
            logger.info("💡 To skip setup and start anyway, set SKIP_AUTO_SETUP=true")
            sys.exit(1)
    
    # Setup completed or skipped, start the server
    logger.info(f"🚀 Starting production server with {workers} workers...")
    
    try:
        # Production server configuration
        uvicorn_config = {
            "app": "app.main:app",
            "host": settings.HOST or "0.0.0.0",
            "port": os.environ["PORT"],
            "workers": workers,
            "log_level": settings.LOG_LEVEL.lower(),
            "access_log": True,
            "lifespan": "on",  # Enable lifespan events
        }
        
        # Add production optimizations if available
        try:
            import uvloop
            uvicorn_config["loop"] = "uvloop"
        except ImportError:
            logger.debug("uvloop not available - using default asyncio loop")
        
        try:
            import httptools
            uvicorn_config["http"] = "httptools"
        except ImportError:
            logger.debug("httptools not available - using default HTTP parser")
        
        # Start the server
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
