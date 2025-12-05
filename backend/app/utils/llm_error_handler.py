"""
LLM Error Handler - Intelligent error categorization and fallback strategy.

Categorizes LLM errors to determine if fallback should be attempted:
- Authorization errors (API key, permissions) → Don't retry with fallback
- Transient errors (timeout, rate limit, connection) → Retry with fallback
- Configuration errors (missing model, bad settings) → Don't retry
- Unknown errors → Attempt fallback as last resort
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """LLM error categories for fallback decision-making."""
    
    AUTHORIZATION = "authorization"      # API key invalid, auth failed
    RATE_LIMIT = "rate_limit"            # Rate limited, quota exceeded
    TIMEOUT = "timeout"                  # Request timeout
    CONNECTION = "connection"            # Network/connection error
    CONFIGURATION = "configuration"      # Model not found, bad config
    SERVICE_UNAVAILABLE = "unavailable"  # Service down, 503 errors
    UNKNOWN = "unknown"                  # Unclassified error


class ErrorShouldRetry(Enum):
    """Whether to retry this error with fallback LLM."""
    
    YES = "yes"              # Retry with fallback
    NO = "no"                # Don't retry, return error
    LAST_RESORT = "last_resort"  # Only retry if this is our only option


class LLMErrorHandler:
    """Analyzes LLM errors and determines if fallback retry should be attempted."""
    
    # Error patterns for categorization
    AUTHORIZATION_PATTERNS = [
        "unauthorized",
        "invalid_api_key",
        "api_key",
        "authentication failed",
        "auth",
        "forbidden",
        "permission",
        "403",
        "401",
    ]
    
    RATE_LIMIT_PATTERNS = [
        "rate_limit",
        "quota_exceeded",
        "quota exceeded",
        "too many requests",
        "too_many_requests",
        "429",
        "rate limit",
    ]
    
    TIMEOUT_PATTERNS = [
        "timeout",
        "timed out",
        "request timeout",
        "read timeout",
        "connection timeout",
        "deadline exceeded",
    ]
    
    CONNECTION_PATTERNS = [
        "connection",
        "connection refused",
        "connection reset",
        "network",
        "unreachable",
        "cannot connect",
        "connection aborted",
        "socket",
    ]
    
    CONFIGURATION_PATTERNS = [
        "model not found",
        "unknown model",
        "invalid model",
        "no such model",
        "not found",
        "404",
    ]
    
    SERVICE_UNAVAILABLE_PATTERNS = [
        "service unavailable",
        "503",
        "temporarily unavailable",
        "down",
        "maintenance",
    ]
    
    @staticmethod
    def categorize_error(exception: Exception) -> ErrorCategory:
        """
        Categorize an LLM exception.
        
        Args:
            exception: The caught exception
            
        Returns:
            ErrorCategory enum value
        """
        error_msg = str(exception).lower()
        error_type = type(exception).__name__.lower()
        
        # Check authorization errors
        for pattern in LLMErrorHandler.AUTHORIZATION_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as AUTHORIZATION: {pattern} found in error")
                return ErrorCategory.AUTHORIZATION
        
        # Check rate limit errors
        for pattern in LLMErrorHandler.RATE_LIMIT_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as RATE_LIMIT: {pattern} found in error")
                return ErrorCategory.RATE_LIMIT
        
        # Check timeout errors
        for pattern in LLMErrorHandler.TIMEOUT_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as TIMEOUT: {pattern} found in error")
                return ErrorCategory.TIMEOUT
        
        # Check connection errors
        for pattern in LLMErrorHandler.CONNECTION_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as CONNECTION: {pattern} found in error")
                return ErrorCategory.CONNECTION
        
        # Check service unavailable errors
        for pattern in LLMErrorHandler.SERVICE_UNAVAILABLE_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as SERVICE_UNAVAILABLE: {pattern} found in error")
                return ErrorCategory.SERVICE_UNAVAILABLE
        
        # Check configuration errors
        for pattern in LLMErrorHandler.CONFIGURATION_PATTERNS:
            if pattern in error_msg or pattern in error_type:
                logger.debug(f"Categorized as CONFIGURATION: {pattern} found in error")
                return ErrorCategory.CONFIGURATION
        
        logger.debug(f"Could not categorize error, defaulting to UNKNOWN: {str(exception)[:100]}")
        return ErrorCategory.UNKNOWN
    
    @staticmethod
    def should_retry_with_fallback(
        exception: Exception,
        fallback_configured: bool = False
    ) -> Tuple[ErrorShouldRetry, str]:
        """
        Determine if fallback LLM should be attempted.
        
        Args:
            exception: The caught exception
            fallback_configured: Whether fallback LLM is configured
            
        Returns:
            Tuple of (ErrorShouldRetry enum, reason string)
        """
        category = LLMErrorHandler.categorize_error(exception)
        
        # Authorization errors - never retry
        if category == ErrorCategory.AUTHORIZATION:
            return (
                ErrorShouldRetry.NO,
                f"Authorization error ({category.value}): fallback won't help - returning error"
            )
        
        # Configuration errors - never retry
        if category == ErrorCategory.CONFIGURATION:
            return (
                ErrorShouldRetry.NO,
                f"Configuration error ({category.value}): fallback won't help - returning error"
            )
        
        # Transient errors - always retry if fallback available
        if category in [
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.TIMEOUT,
            ErrorCategory.CONNECTION,
            ErrorCategory.SERVICE_UNAVAILABLE
        ]:
            if fallback_configured:
                return (
                    ErrorShouldRetry.YES,
                    f"Transient error ({category.value}): attempting fallback LLM"
                )
            else:
                return (
                    ErrorShouldRetry.NO,
                    f"Transient error ({category.value}): no fallback configured - returning error"
                )
        
        # Unknown errors - attempt fallback only if available
        if category == ErrorCategory.UNKNOWN:
            if fallback_configured:
                return (
                    ErrorShouldRetry.LAST_RESORT,
                    f"Unknown error: attempting fallback as last resort"
                )
            else:
                return (
                    ErrorShouldRetry.NO,
                    f"Unknown error: no fallback configured - returning error"
                )
        
        return (ErrorShouldRetry.NO, f"Unhandled error category: {category.value}")
    
    @staticmethod
    def format_error_response(
        original_exception: Exception,
        error_category: Optional[ErrorCategory] = None,
        attempted_fallback: bool = False,
        fallback_exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Format error for client response.
        
        Args:
            original_exception: The original primary LLM error
            error_category: Category of the error (auto-detected if not provided)
            attempted_fallback: Whether fallback was attempted
            fallback_exception: Exception from fallback attempt if applicable
            
        Returns:
            Error response dict with type and message
        """
        if error_category is None:
            error_category = LLMErrorHandler.categorize_error(original_exception)
        
        error_type = error_category.value
        primary_msg = str(original_exception)
        
        if attempted_fallback and fallback_exception:
            fallback_msg = str(fallback_exception)
            message = (
                f"Primary LLM error ({error_type}): {primary_msg}. "
                f"Fallback LLM also failed: {fallback_msg}"
            )
        elif attempted_fallback:
            message = (
                f"Primary LLM error ({error_type}): {primary_msg}. "
                f"Fallback LLM also failed."
            )
        else:
            message = f"LLM error ({error_type}): {primary_msg}"
        
        return {
            "type": "llm_error",
            "error_category": error_type,
            "message": message,
            "attempted_fallback": attempted_fallback
        }
