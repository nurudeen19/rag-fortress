# Core module
from .logging import setup_logging, get_logger, default_logger
from .email_client import EmailClient, get_email_client, init_email_client
from .exceptions import (
    # Base
    RAGFortressException,
    
    # Configuration
    ConfigurationError,
    InvalidSettingsError,
    MissingEnvironmentVariableError,
    
    # LLM
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMTimeoutError,
    
    # Documents
    DocumentError,
    DocumentNotFoundError,
    DocumentParsingError,
    UnsupportedDocumentTypeError,
    DocumentTooLargeError,
    
    # Vector Store
    VectorStoreError,
    VectorStoreConnectionError,
    CollectionNotFoundError,
    EmbeddingError,
    
    # Database
    DatabaseError,
    DatabaseConnectionError,
    RecordNotFoundError,
    DuplicateRecordError,
    
    # Auth
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    
    # Validation
    ValidationError,
    
    # Rate Limiting
    RateLimitExceededError,
    
    # Handlers
    register_exception_handlers,
)

__all__ = [
    # Logging
    'setup_logging',
    'get_logger',
    'default_logger',
    
    # Email Client
    'EmailClient',
    'get_email_client',
    'init_email_client',
    
    # Base Exceptions
    'RAGFortressException',
    
    # Configuration
    'ConfigurationError',
    'InvalidSettingsError',
    'MissingEnvironmentVariableError',
    
    # LLM
    'LLMError',
    'LLMProviderError',
    'LLMRateLimitError',
    'LLMAuthenticationError',
    'LLMTimeoutError',
    
    # Documents
    'DocumentError',
    'DocumentNotFoundError',
    'DocumentParsingError',
    'UnsupportedDocumentTypeError',
    'DocumentTooLargeError',
    
    # Vector Store
    'VectorStoreError',
    'VectorStoreConnectionError',
    'CollectionNotFoundError',
    'EmbeddingError',
    
    # Database
    'DatabaseError',
    'DatabaseConnectionError',
    'RecordNotFoundError',
    'DuplicateRecordError',
    
    # Auth
    'AuthenticationError',
    'AuthorizationError',
    'InvalidTokenError',
    
    # Validation
    'ValidationError',
    
    # Rate Limiting
    'RateLimitExceededError',
    
    # Handlers
    'register_exception_handlers',
]
