"""
Middleware configuration module.
"""

from fastapi import FastAPI

from .cors import setup_cors
from .logging import setup_request_logging
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
    
    # Enable request logging in non-production environments for debugging
    try:
        enable_logging = (settings.ENVIRONMENT != "production")
    except Exception:
        enable_logging = True
    
    setup_request_logging(app, enabled=enable_logging)
    
    # Add more middleware configurations here as needed:
    # - Authentication middleware
    # - Rate limiting
    # - Compression
    # - Security headers
    # - etc.
    
    logger.info("Middlewares configured successfully")
