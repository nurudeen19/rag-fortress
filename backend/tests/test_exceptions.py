"""
Tests for exception handling system.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.exceptions import (
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


# ============================================================================
# Test Base Exceptions
# ============================================================================

class TestBaseExceptions:
    """Test base exception classes."""
    
    def test_rag_fortress_exception_basic(self):
        """Test basic RAGFortressException."""
        exc = RAGFortressException("Test error")
        
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {}
        assert str(exc) == "Test error"
    
    def test_rag_fortress_exception_with_details(self):
        """Test RAGFortressException with details."""
        exc = RAGFortressException(
            message="Test error",
            status_code=400,
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}


# ============================================================================
# Test Configuration Exceptions
# ============================================================================

class TestConfigurationExceptions:
    """Test configuration exception classes."""
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("Config error")
        
        assert exc.message == "Config error"
        assert exc.status_code == 500
        assert isinstance(exc, RAGFortressException)
    
    def test_invalid_settings_error(self):
        """Test InvalidSettingsError."""
        exc = InvalidSettingsError("Invalid setting")
        
        assert exc.message == "Invalid setting"
        assert isinstance(exc, ConfigurationError)
    
    def test_missing_environment_variable_error(self):
        """Test MissingEnvironmentVariableError."""
        exc = MissingEnvironmentVariableError("API_KEY")
        
        assert "API_KEY" in exc.message
        assert exc.details["variable"] == "API_KEY"
        assert isinstance(exc, ConfigurationError)


# ============================================================================
# Test LLM Exceptions
# ============================================================================

class TestLLMExceptions:
    """Test LLM exception classes."""
    
    def test_llm_error_basic(self):
        """Test basic LLMError."""
        exc = LLMError("LLM failed")
        
        assert exc.message == "LLM failed"
        assert exc.status_code == 503
        assert exc.details == {}
    
    def test_llm_error_with_provider(self):
        """Test LLMError with provider info."""
        exc = LLMError(
            message="LLM failed",
            provider="openai",
            model="gpt-4"
        )
        
        assert exc.details["provider"] == "openai"
        assert exc.details["model"] == "gpt-4"
    
    def test_llm_provider_error(self):
        """Test LLMProviderError."""
        exc = LLMProviderError(
            message="Provider error",
            provider="openai"
        )
        
        assert exc.message == "Provider error"
        assert exc.details["provider"] == "openai"
        assert isinstance(exc, LLMError)
    
    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError."""
        exc = LLMRateLimitError(
            provider="openai",
            retry_after=60
        )
        
        assert "openai" in exc.message
        assert exc.details["retry_after"] == 60
        assert isinstance(exc, LLMError)
    
    def test_llm_authentication_error(self):
        """Test LLMAuthenticationError."""
        exc = LLMAuthenticationError(provider="openai")
        
        assert "openai" in exc.message
        assert exc.details["provider"] == "openai"
        assert isinstance(exc, LLMError)
    
    def test_llm_timeout_error(self):
        """Test LLMTimeoutError."""
        exc = LLMTimeoutError(
            provider="openai",
            timeout=30.0
        )
        
        assert "openai" in exc.message
        assert "30" in exc.message
        assert exc.details["timeout"] == 30.0
        assert isinstance(exc, LLMError)


# ============================================================================
# Test Document Exceptions
# ============================================================================

class TestDocumentExceptions:
    """Test document exception classes."""
    
    def test_document_error_basic(self):
        """Test basic DocumentError."""
        exc = DocumentError("Doc error")
        
        assert exc.message == "Doc error"
        assert exc.status_code == 400
    
    def test_document_error_with_id(self):
        """Test DocumentError with document ID."""
        exc = DocumentError(
            message="Doc error",
            document_id="doc_123"
        )
        
        assert exc.details["document_id"] == "doc_123"
    
    def test_document_not_found_error(self):
        """Test DocumentNotFoundError."""
        exc = DocumentNotFoundError("doc_123")
        
        assert "doc_123" in exc.message
        assert exc.details["document_id"] == "doc_123"
        assert exc.status_code == 404
        assert isinstance(exc, DocumentError)
    
    def test_document_parsing_error(self):
        """Test DocumentParsingError."""
        exc = DocumentParsingError(
            message="Parse failed",
            file_path="/path/to/file.pdf"
        )
        
        assert exc.message == "Parse failed"
        assert exc.details["file_path"] == "/path/to/file.pdf"
        assert exc.status_code == 422
        assert isinstance(exc, DocumentError)
    
    def test_unsupported_document_type_error(self):
        """Test UnsupportedDocumentTypeError."""
        exc = UnsupportedDocumentTypeError(
            file_type="xyz",
            supported_types=[".pdf", ".txt"]
        )
        
        assert "xyz" in exc.message
        assert exc.details["file_type"] == "xyz"
        assert exc.details["supported_types"] == [".pdf", ".txt"]
        assert exc.status_code == 415
        assert isinstance(exc, DocumentError)
    
    def test_document_too_large_error(self):
        """Test DocumentTooLargeError."""
        exc = DocumentTooLargeError(
            size=20_000_000,
            max_size=10_000_000
        )
        
        assert "20000000" in exc.message
        assert "10000000" in exc.message
        assert exc.details["size"] == 20_000_000
        assert exc.details["max_size"] == 10_000_000
        assert exc.status_code == 413
        assert isinstance(exc, DocumentError)


# ============================================================================
# Test Vector Store Exceptions
# ============================================================================

class TestVectorStoreExceptions:
    """Test vector store exception classes."""
    
    def test_vector_store_error_basic(self):
        """Test basic VectorStoreError."""
        exc = VectorStoreError("Store error")
        
        assert exc.message == "Store error"
        assert exc.status_code == 500
    
    def test_vector_store_error_with_collection(self):
        """Test VectorStoreError with collection."""
        exc = VectorStoreError(
            message="Store error",
            collection="documents"
        )
        
        assert exc.details["collection"] == "documents"
    
    def test_vector_store_connection_error(self):
        """Test VectorStoreConnectionError."""
        exc = VectorStoreConnectionError("Connection failed")
        
        assert exc.message == "Connection failed"
        assert isinstance(exc, VectorStoreError)
    
    def test_collection_not_found_error(self):
        """Test CollectionNotFoundError."""
        exc = CollectionNotFoundError("documents")
        
        assert "documents" in exc.message
        assert exc.details["collection"] == "documents"
        assert isinstance(exc, VectorStoreError)
    
    def test_embedding_error(self):
        """Test EmbeddingError."""
        exc = EmbeddingError(
            message="Embedding failed",
            details={"model": "sentence-transformers"}
        )
        
        assert exc.message == "Embedding failed"
        assert exc.details["model"] == "sentence-transformers"
        assert isinstance(exc, VectorStoreError)


# ============================================================================
# Test Database Exceptions
# ============================================================================

class TestDatabaseExceptions:
    """Test database exception classes."""
    
    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("DB error")
        
        assert exc.message == "DB error"
        assert exc.status_code == 500
    
    def test_database_connection_error(self):
        """Test DatabaseConnectionError."""
        exc = DatabaseConnectionError("Connection failed")
        
        assert exc.message == "Connection failed"
        assert isinstance(exc, DatabaseError)
    
    def test_record_not_found_error(self):
        """Test RecordNotFoundError."""
        exc = RecordNotFoundError(model="User", record_id=123)
        
        assert "User" in exc.message
        assert "123" in exc.message
        assert exc.details["model"] == "User"
        assert exc.details["id"] == 123
        assert exc.status_code == 404
        assert isinstance(exc, DatabaseError)
    
    def test_duplicate_record_error(self):
        """Test DuplicateRecordError."""
        exc = DuplicateRecordError(
            model="User",
            field="email",
            value="test@example.com"
        )
        
        assert "User" in exc.message
        assert "email" in exc.message
        assert exc.details["model"] == "User"
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "test@example.com"
        assert exc.status_code == 409
        assert isinstance(exc, DatabaseError)


# ============================================================================
# Test Auth Exceptions
# ============================================================================

class TestAuthExceptions:
    """Test authentication and authorization exception classes."""
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError()
        
        assert "Authentication" in exc.message
        assert exc.status_code == 401
    
    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        exc = AuthenticationError("Invalid credentials")
        
        assert exc.message == "Invalid credentials"
        assert exc.status_code == 401
    
    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError()
        
        assert "permission" in exc.message.lower()
        assert exc.status_code == 403
    
    def test_invalid_token_error(self):
        """Test InvalidTokenError."""
        exc = InvalidTokenError()
        
        assert "token" in exc.message.lower()
        assert exc.status_code == 401
        assert isinstance(exc, AuthenticationError)


# ============================================================================
# Test Validation Exceptions
# ============================================================================

class TestValidationExceptions:
    """Test validation exception classes."""
    
    def test_validation_error_basic(self):
        """Test basic ValidationError."""
        exc = ValidationError("Validation failed")
        
        assert exc.message == "Validation failed"
        assert exc.status_code == 422
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field."""
        exc = ValidationError(
            message="Invalid email",
            field="email"
        )
        
        assert exc.details["field"] == "email"


# ============================================================================
# Test Rate Limiting Exceptions
# ============================================================================

class TestRateLimitingExceptions:
    """Test rate limiting exception classes."""
    
    def test_rate_limit_exceeded_error_basic(self):
        """Test basic RateLimitExceededError."""
        exc = RateLimitExceededError()
        
        assert "Rate limit" in exc.message
        assert exc.status_code == 429
    
    def test_rate_limit_exceeded_error_with_retry(self):
        """Test RateLimitExceededError with retry_after."""
        exc = RateLimitExceededError(
            message="Too many requests",
            retry_after=60
        )
        
        assert exc.message == "Too many requests"
        assert exc.details["retry_after"] == 60


# ============================================================================
# Test Exception Handlers
# ============================================================================

class TestExceptionHandlers:
    """Test exception handler registration and functionality."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with exception handlers."""
        app = FastAPI()
        register_exception_handlers(app)
        
        # Add test routes that raise exceptions
        @app.get("/test/rag-fortress-exception")
        async def test_rag_exception():
            raise RAGFortressException("Test error", status_code=400)
        
        @app.get("/test/document-not-found")
        async def test_doc_not_found():
            raise DocumentNotFoundError("doc_123")
        
        @app.get("/test/llm-rate-limit")
        async def test_llm_rate():
            raise LLMRateLimitError(provider="openai", retry_after=60)
        
        @app.get("/test/validation-error")
        async def test_validation():
            raise ValidationError("Invalid input", field="email")
        
        @app.get("/test/unhandled-exception")
        async def test_unhandled():
            raise ValueError("Unhandled error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_rag_fortress_exception_handler(self, client):
        """Test RAGFortressException handler."""
        response = client.get("/test/rag-fortress-exception")
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "RAGFortressException"
        assert data["error"]["message"] == "Test error"
        assert "details" in data["error"]
    
    def test_document_not_found_handler(self, client):
        """Test DocumentNotFoundError handler."""
        response = client.get("/test/document-not-found")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["type"] == "DocumentNotFoundError"
        assert "doc_123" in data["error"]["message"]
        assert data["error"]["details"]["document_id"] == "doc_123"
    
    def test_llm_rate_limit_handler(self, client):
        """Test LLMRateLimitError handler."""
        response = client.get("/test/llm-rate-limit")
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["type"] == "LLMRateLimitError"
        assert data["error"]["details"]["retry_after"] == 60
    
    def test_validation_error_handler(self, client):
        """Test ValidationError handler."""
        response = client.get("/test/validation-error")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["type"] == "ValidationError"
        assert data["error"]["details"]["field"] == "email"
    
    def test_unhandled_exception_handler(self, client):
        """Test general exception handler."""
        response = client.get("/test/unhandled-exception")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["type"] == "InternalServerError"
        # In test environment, should show error details
        assert "message" in data["error"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestExceptionIntegration:
    """Test exception handling in realistic scenarios."""
    
    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        # All custom exceptions inherit from RAGFortressException
        assert issubclass(ConfigurationError, RAGFortressException)
        assert issubclass(LLMError, RAGFortressException)
        assert issubclass(DocumentError, RAGFortressException)
        assert issubclass(VectorStoreError, RAGFortressException)
        assert issubclass(DatabaseError, RAGFortressException)
        
        # Specific exceptions inherit from their base
        assert issubclass(InvalidSettingsError, ConfigurationError)
        assert issubclass(LLMProviderError, LLMError)
        assert issubclass(DocumentNotFoundError, DocumentError)
    
    def test_catch_base_exception(self):
        """Test catching base exception catches specific ones."""
        try:
            raise DocumentNotFoundError("doc_123")
        except RAGFortressException as e:
            assert isinstance(e, DocumentNotFoundError)
            assert e.status_code == 404
    
    def test_catch_category_exception(self):
        """Test catching category exception."""
        try:
            raise LLMRateLimitError(provider="openai")
        except LLMError as e:
            assert isinstance(e, LLMRateLimitError)
            assert e.details["provider"] == "openai"
