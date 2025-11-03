"""
Middleware configuration module.
"""

from fastapi import FastAPI

from .cors import setup_cors
# from .logging import setup_request_logging
from app.core import get_logger
from app.config.settings import settings


logger = get_logger(__name__)


def setup_middlewares(app: FastAPI) -> None:
    """
    Configure all application middlewares.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Setting up middlewares...")
    
    # Configure CORS
    setup_cors(app)
    
    # Optional: Request logging (uncomment to enable)
    # Useful for debugging but can be verbose in production
    # setup_request_logging(app, enabled=(settings.ENVIRONMENT == "development"))
    
    # Add more middleware configurations here as needed:
    # - Authentication middleware
    # - Rate limiting
    # - Compression
    # - Security headers
    # - etc.
    
    logger.info("Middlewares configured successfully")
