"""
CORS (Cross-Origin Resource Sharing) middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    # Ensure OPTIONS method is always included for CORS preflight
    cors_methods = settings.CORS_METHODS
    if "*" not in cors_methods and "OPTIONS" not in cors_methods:
        cors_methods = list(cors_methods) + ["OPTIONS"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=cors_methods,
        allow_headers=settings.CORS_HEADERS,
        expose_headers=["*"],  # Allow frontend to read response headers
        max_age=3600,  # Cache preflight for 1 hour
    )
    
    logger.info(f"CORS configured:")
    logger.info(f"  - Origins: {settings.CORS_ORIGINS}")
    logger.info(f"  - Methods: {cors_methods}")
    logger.info(f"  - Headers: {settings.CORS_HEADERS}")
    logger.info(f"  - Credentials: {settings.CORS_CREDENTIALS}")
