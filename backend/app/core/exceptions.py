"""
Central exception handling for RAG Fortress.

This module provides custom exceptions and exception handlers for consistent
error handling across the application.
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ============================================================================
# Base Exceptions
# ============================================================================

class RAGFortressException(Exception):
    """Base exception for all RAG Fortress errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(RAGFortressException):
    """Raised when there's a configuration error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class InvalidSettingsError(ConfigurationError):
    """Raised when settings validation fails."""
    pass


class MissingEnvironmentVariableError(ConfigurationError):
    """Raised when a required environment variable is missing."""
    
    def __init__(self, variable_name: str):
        super().__init__(
            message=f"Missing required environment variable: {variable_name}",
            details={"variable": variable_name}
        )


# ============================================================================
# LLM Exceptions
# ============================================================================

class LLMError(RAGFortressException):
    """Base exception for LLM-related errors."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class LLMProviderError(LLMError):
    """Raised when LLM provider encounters an error."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    
    def __init__(
        self,
        provider: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=f"Rate limit exceeded for {provider}",
            provider=provider,
            details=details
        )


class LLMAuthenticationError(LLMError):
    """Raised when LLM authentication fails."""
    
    def __init__(self, provider: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Authentication failed for {provider}",
            provider=provider,
            details=details
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    
    def __init__(
        self,
        provider: str,
        timeout: float,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["timeout"] = timeout
        
        super().__init__(
            message=f"Request to {provider} timed out after {timeout}s",
            provider=provider,
            details=details
        )


# ============================================================================
# Document Processing Exceptions
# ============================================================================

class DocumentError(RAGFortressException):
    """Base exception for document-related errors."""
    
    def __init__(
        self,
        message: str,
        document_id: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if document_id:
            details["document_id"] = document_id
        
        super().__init__(
            message=message,
            status_code=status_code,
            details=details
        )


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            document_id=document_id,
            status_code=status.HTTP_404_NOT_FOUND
        )


class DocumentParsingError(DocumentError):
    """Raised when document parsing fails."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when document type is not supported."""
    
    def __init__(self, file_type: str, supported_types: Optional[list] = None):
        details = {"file_type": file_type}
        if supported_types:
            details["supported_types"] = supported_types
        
        super().__init__(
            message=f"Unsupported document type: {file_type}",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details=details
        )


class DocumentTooLargeError(DocumentError):
    """Raised when document exceeds size limit."""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"Document too large: {size} bytes (max: {max_size} bytes)",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"size": size, "max_size": max_size}
        )




# ============================================================================
# Vector Store Exceptions
# ============================================================================

class VectorStoreError(RAGFortressException):
    """Base exception for vector store errors."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        collection: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if provider:
            details["provider"] = provider
        if collection:
            details["collection"] = collection
        
        super().__init__(
            message=message,
            status_code=status_code,
            details=details
        )


class VectorStoreConnectionError(VectorStoreError):
    """Raised when vector store connection fails."""
    pass


class CollectionNotFoundError(VectorStoreError):
    """Raised when collection is not found."""
    
    def __init__(self, collection: str):
        super().__init__(
            message=f"Collection not found: {collection}",
            collection=collection
        )


class EmbeddingError(VectorStoreError):
    """Raised when embedding generation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details
        )


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(RAGFortressException):
    """Base exception for database errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when database record is not found."""
    
    def __init__(self, model: str, record_id: Any):
        super().__init__(
            message=f"{model} not found: {record_id}",
            details={"model": model, "id": record_id}
        )
        self.status_code = status.HTTP_404_NOT_FOUND


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create duplicate record."""
    
    def __init__(self, model: str, field: str, value: Any):
        super().__init__(
            message=f"Duplicate {model}: {field}={value}",
            details={"model": model, "field": field, "value": value}
        )
        self.status_code = status.HTTP_409_CONFLICT


# ============================================================================
# Authentication & Authorization Exceptions
# ============================================================================

class AuthenticationError(RAGFortressException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(RAGFortressException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid."""
    
    def __init__(self):
        super().__init__(message="Invalid or expired token")


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(RAGFortressException):
    """Raised when validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================

class RateLimitExceededError(RAGFortressException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


# ============================================================================
# Exception Handlers
# ============================================================================

async def rag_fortress_exception_handler(
    request: Request,
    exc: RAGFortressException
) -> JSONResponse:
    """Handle RAG Fortress custom exceptions."""
    from app.core import get_logger
    
    logger = get_logger(__name__)
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed logging."""
    from app.core import get_logger
    import json
    
    logger = get_logger(__name__)
    
    # Extract detailed error information
    errors = exc.errors()
    
    # Build comprehensive error details
    error_details = []
    for error in errors:
        error_details.append({
            "location": error.get("loc", []),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
            "input": str(error.get("input", ""))[:500],  # Truncate large inputs
            "context": error.get("ctx", {})
        })
    
    # Get request details
    request_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": dict(request.headers),
    }
    
    # Try to get body if applicable
    try:
        body = await request.body()
        request_details["body"] = body.decode() if body else None
    except:
        request_details["body"] = "Could not read body"
    
    # Log comprehensive error information
    logger.error(
        f"Validation error on {request.url.path}: {len(errors)} error(s)",
        extra={
            "validation_errors": error_details,
            "request_details": request_details,
            "full_traceback": True
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": {
                    "errors": error_details,
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "query": dict(request.query_params)
                    }
                }
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    from app.core import get_logger
    
    logger = get_logger(__name__)
    
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
        )
    else:
        logger.warning(
            f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,  # FastAPI standard format
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "details": {}
            }
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions with detailed logging."""
    from app.core import get_logger
    import traceback
    
    logger = get_logger(__name__)
    
    # Get detailed request information
    request_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query": dict(request.query_params),
    }
    
    # Try to get body if applicable
    try:
        body = await request.body()
        request_details["body"] = body.decode() if body else None
    except:
        request_details["body"] = "Could not read body"
    
    # Get exception details
    exc_details = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "module": exc.__class__.__module__,
        "traceback": traceback.format_exc()
    }
    
    # Log comprehensive error information
    logger.critical(
        f"Unhandled exception on {request.url.path} ({exc.__class__.__name__}): {str(exc)[:200]}",
        extra={
            "exception_details": exc_details,
            "request_details": request_details
        },
        exc_info=True
    )
    
    # In production, don't expose internal error details
    from app.config import settings
    
    if settings.ENVIRONMENT == "production":
        message = "An internal error occurred"
        details = {}
    else:
        message = str(exc)
        details = {
            "type": exc.__class__.__name__,
            "request": request_details,
            "exception": exc_details
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": message,
                "details": details
            }
        }
    )


# ============================================================================
# Exception Handler Registration
# ============================================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from app.core import get_logger
    
    logger = get_logger(__name__)
    
    # Custom exceptions
    app.add_exception_handler(RAGFortressException, rag_fortress_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered")
