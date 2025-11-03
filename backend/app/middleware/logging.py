"""
Request logging middleware.
Logs incoming requests and responses for monitoring and debugging.
"""

import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import get_logger


logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses.
    
    Logs:
    - Request method, path, and client IP
    - Response status code
    - Request processing time
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details."""
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(f"→ {method} {path} from {client_ip}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"← {method} {path} - Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"✗ {method} {path} - Error: {str(e)} - "
                f"Time: {process_time:.3f}s",
                exc_info=True
            )
            raise


def setup_request_logging(app: FastAPI, enabled: bool = True) -> None:
    """
    Configure request logging middleware.
    
    Args:
        app: FastAPI application instance
        enabled: Whether to enable request logging (default: True in dev, False in prod)
    """
    if enabled:
        app.add_middleware(RequestLoggingMiddleware)
        logger.info("Request logging middleware enabled")
    else:
        logger.info("Request logging middleware disabled")
