"""
Examples demonstrating exception handling patterns in RAG Fortress.
"""

from app.core import (
    get_logger,
    # Configuration
    ConfigurationError,
    MissingEnvironmentVariableError,
    # LLM
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    # Documents
    DocumentNotFoundError,
    DocumentParsingError,
    UnsupportedDocumentTypeError,
    DocumentTooLargeError,
    # Vector Store
    VectorStoreConnectionError,
    EmbeddingError,
    # Database
    RecordNotFoundError,
    DuplicateRecordError,
    # Auth
    AuthenticationError,
    AuthorizationError,
    # Validation
    ValidationError,
    # Rate Limiting
    RateLimitExceededError,
)

logger = get_logger(__name__)


# ============================================================================
# Example 1: Configuration Errors
# ============================================================================

def example_configuration_errors():
    """Examples of configuration error handling."""
    
    # Missing environment variable
    try:
        api_key = get_required_env_var("API_KEY")
    except MissingEnvironmentVariableError as e:
        logger.error(f"Configuration error: {e.message}")
        # Details: {'variable': 'API_KEY'}
        print(f"Missing: {e.details['variable']}")
    
    # Invalid settings
    try:
        validate_settings()
    except ConfigurationError as e:
        logger.error(f"Settings validation failed: {e.message}")


# ============================================================================
# Example 2: LLM Provider Errors
# ============================================================================

async def example_llm_errors():
    """Examples of LLM error handling with fallback."""
    
    try:
        response = await call_primary_llm("What is AI?")
    except LLMRateLimitError as e:
        logger.warning(f"Rate limit hit: {e.message}")
        retry_after = e.details.get("retry_after", 60)
        logger.info(f"Retry after {retry_after} seconds")
        
        # Try fallback
        try:
            response = await call_fallback_llm("What is AI?")
        except LLMProviderError as e:
            logger.error("Fallback also failed", exc_info=True)
            raise
    
    except LLMTimeoutError as e:
        logger.error(f"Request timeout: {e.message}")
        timeout = e.details["timeout"]
        provider = e.details["provider"]
        logger.info(f"{provider} timed out after {timeout}s")
    
    except LLMProviderError as e:
        logger.error(f"LLM error: {e.message}")
        logger.debug(f"Provider: {e.details.get('provider')}")
        logger.debug(f"Model: {e.details.get('model')}")


# ============================================================================
# Example 3: Document Processing Errors
# ============================================================================

async def example_document_errors(file_path: str, file_size: int):
    """Examples of document error handling."""
    
    # Check file size
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    if file_size > MAX_SIZE:
        raise DocumentTooLargeError(size=file_size, max_size=MAX_SIZE)
    
    # Check file type
    supported_types = [".pdf", ".txt", ".docx", ".md"]
    file_ext = file_path.split(".")[-1]
    
    if f".{file_ext}" not in supported_types:
        raise UnsupportedDocumentTypeError(
            file_type=file_ext,
            supported_types=supported_types
        )
    
    # Parse document
    try:
        content = parse_document(file_path)
    except Exception as e:
        raise DocumentParsingError(
            message=f"Failed to parse document: {str(e)}",
            file_path=file_path,
            details={"error": str(e)}
        )
    
    # Retrieve document
    try:
        doc = get_document("doc_123")
    except DocumentNotFoundError as e:
        logger.warning(f"Document not found: {e.details['document_id']}")
        # Return None or default
        return None


# ============================================================================
# Example 4: Vector Store Errors
# ============================================================================

async def example_vector_store_errors():
    """Examples of vector store error handling."""
    
    # Connection error with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await connect_to_vector_store()
            break
        except VectorStoreConnectionError as e:
            logger.warning(f"Connection attempt {attempt + 1} failed")
            if attempt == max_retries - 1:
                logger.error("Max retries reached", exc_info=True)
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Embedding error
    try:
        embeddings = await generate_embeddings(texts)
    except EmbeddingError as e:
        logger.error(f"Embedding generation failed: {e.message}")
        logger.debug(f"Details: {e.details}")
        # Use cached embeddings or skip
        return None


# ============================================================================
# Example 5: Database Errors
# ============================================================================

async def example_database_errors():
    """Examples of database error handling."""
    
    # Record not found
    try:
        user = db.get_user(user_id="user_123")
    except RecordNotFoundError as e:
        logger.info(f"User not found: {e.details['id']}")
        return None
    
    # Duplicate record
    try:
        user = db.create_user(email="test@example.com")
    except DuplicateRecordError as e:
        logger.warning(f"Duplicate {e.details['field']}: {e.details['value']}")
        # Return existing user
        return db.get_user_by_email(e.details['value'])


# ============================================================================
# Example 6: Authentication & Authorization
# ============================================================================

async def example_auth_errors(token: str, user_id: str, resource_id: str):
    """Examples of authentication and authorization errors."""
    
    # Authentication
    try:
        user = authenticate_token(token)
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.message}")
        # Return 401 response
        raise
    
    # Authorization
    try:
        check_permission(user_id, "delete", resource_id)
    except AuthorizationError as e:
        logger.warning(
            f"User {user_id} lacks permission to delete {resource_id}"
        )
        # Return 403 response
        raise


# ============================================================================
# Example 7: Validation Errors
# ============================================================================

def example_validation_errors(data: dict):
    """Examples of validation error handling."""
    
    # Custom validation
    if "email" not in data:
        raise ValidationError(
            message="Email is required",
            field="email"
        )
    
    if not data["email"].endswith("@example.com"):
        raise ValidationError(
            message="Email must be from example.com domain",
            field="email",
            details={"provided": data["email"]}
        )


# ============================================================================
# Example 8: Rate Limiting
# ============================================================================

async def example_rate_limiting(user_id: str):
    """Examples of rate limiting error handling."""
    
    try:
        await process_request(user_id)
    except RateLimitExceededError as e:
        retry_after = e.details.get("retry_after", 60)
        logger.warning(f"Rate limit exceeded for {user_id}, retry after {retry_after}s")
        # Return 429 with Retry-After header
        raise


# ============================================================================
# Example 9: FastAPI Route with Error Handling
# ============================================================================

from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document with comprehensive error handling."""
    
    try:
        # Validate file size
        file_size = await get_file_size(file)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise DocumentTooLargeError(size=file_size, max_size=10*1024*1024)
        
        # Validate file type
        if not file.filename.endswith((".pdf", ".txt", ".docx")):
            raise UnsupportedDocumentTypeError(
                file_type=file.filename.split(".")[-1],
                supported_types=[".pdf", ".txt", ".docx"]
            )
        
        # Save file
        file_path = await save_uploaded_file(file)
        
        # Parse document
        try:
            content = parse_document(file_path)
        except Exception as e:
            raise DocumentParsingError(
                message="Failed to parse document",
                file_path=file_path,
                details={"error": str(e)}
            )
        
        # Generate embeddings
        try:
            embeddings = await generate_embeddings([content])
        except Exception as e:
            raise EmbeddingError(
                message="Failed to generate embeddings",
                details={"error": str(e)}
            )
        
        # Store in vector database
        try:
            doc_id = await store_document(content, embeddings)
        except VectorStoreConnectionError as e:
            logger.error("Vector store unavailable", exc_info=True)
            raise
        
        logger.info(f"Document uploaded successfully: {doc_id}")
        return {"document_id": doc_id, "status": "success"}
    
    # All custom exceptions are handled by exception handlers
    # They will return appropriate JSON responses
    except (
        DocumentTooLargeError,
        UnsupportedDocumentTypeError,
        DocumentParsingError,
        EmbeddingError,
        VectorStoreConnectionError,
    ):
        # These will be caught by rag_fortress_exception_handler
        raise


# ============================================================================
# Example 10: Service Class with Error Handling
# ============================================================================

class RAGService:
    """RAG service with comprehensive error handling."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.primary_llm = None
        self.fallback_llm = None
    
    async def query(self, question: str) -> str:
        """
        Process RAG query with error handling and fallback.
        
        Args:
            question: User question
            
        Returns:
            Answer string
            
        Raises:
            LLMProviderError: If both primary and fallback LLMs fail
            VectorStoreError: If retrieval fails
        """
        try:
            # Retrieve relevant documents
            try:
                docs = await self.retrieve_documents(question)
            except VectorStoreConnectionError as e:
                self.logger.error("Vector store unavailable", exc_info=True)
                # Fall back to direct LLM query without context
                docs = []
            
            # Generate answer with primary LLM
            try:
                answer = await self.generate_answer(
                    question=question,
                    context=docs,
                    llm=self.primary_llm
                )
                return answer
            
            except (LLMRateLimitError, LLMTimeoutError, LLMProviderError) as e:
                self.logger.warning(f"Primary LLM failed: {e.message}")
                
                # Try fallback LLM
                try:
                    self.logger.info("Attempting fallback LLM")
                    answer = await self.generate_answer(
                        question=question,
                        context=docs,
                        llm=self.fallback_llm
                    )
                    return answer
                
                except LLMProviderError as fallback_error:
                    self.logger.error("Fallback LLM also failed", exc_info=True)
                    raise LLMProviderError(
                        message="All LLM providers failed",
                        details={
                            "primary_error": str(e),
                            "fallback_error": str(fallback_error)
                        }
                    )
        
        except Exception as e:
            self.logger.critical(f"Unexpected error in RAG query: {e}", exc_info=True)
            raise


# ============================================================================
# Helper Functions (Placeholders)
# ============================================================================

def get_required_env_var(name: str) -> str:
    """Get required environment variable or raise error."""
    import os
    value = os.getenv(name)
    if not value:
        raise MissingEnvironmentVariableError(name)
    return value

def validate_settings():
    """Validate settings."""
    pass

async def call_primary_llm(prompt: str) -> str:
    """Call primary LLM."""
    pass

async def call_fallback_llm(prompt: str) -> str:
    """Call fallback LLM."""
    pass

def parse_document(file_path: str) -> str:
    """Parse document."""
    pass

def get_document(doc_id: str) -> dict:
    """Get document."""
    pass

async def connect_to_vector_store():
    """Connect to vector store."""
    pass

async def generate_embeddings(texts: list) -> list:
    """Generate embeddings."""
    pass

def authenticate_token(token: str):
    """Authenticate token."""
    pass

def check_permission(user_id: str, action: str, resource_id: str):
    """Check permission."""
    pass

async def process_request(user_id: str):
    """Process request."""
    pass

async def get_file_size(file) -> int:
    """Get file size."""
    return 0

async def save_uploaded_file(file) -> str:
    """Save uploaded file."""
    return ""

async def store_document(content: str, embeddings: list) -> str:
    """Store document."""
    return "doc_id"


if __name__ == "__main__":
    print("Exception handling examples loaded")
    print("Import these examples to see error handling patterns")
