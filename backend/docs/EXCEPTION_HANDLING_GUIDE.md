# Exception Handling Guide

## Overview

RAG Fortress provides a comprehensive exception handling system with custom exceptions, structured error responses, and automatic error logging.

## Features

✅ **Hierarchical Exceptions** - Organized exception categories  
✅ **Structured Error Responses** - Consistent JSON error format  
✅ **Automatic Logging** - All errors logged with context  
✅ **Status Code Mapping** - HTTP status codes for each error type  
✅ **Error Details** - Additional context for debugging  
✅ **FastAPI Integration** - Automatic exception handling  

## Exception Hierarchy

```
RAGFortressException (Base)
├── ConfigurationError (500)
│   ├── InvalidSettingsError
│   └── MissingEnvironmentVariableError
├── LLMError (503)
│   ├── LLMProviderError
│   ├── LLMRateLimitError
│   ├── LLMAuthenticationError
│   └── LLMTimeoutError
├── DocumentError (400)
│   ├── DocumentNotFoundError (404)
│   ├── DocumentParsingError (422)
│   ├── UnsupportedDocumentTypeError (415)
│   └── DocumentTooLargeError (413)
├── VectorStoreError (500)
│   ├── VectorStoreConnectionError
│   ├── CollectionNotFoundError
│   └── EmbeddingError
├── DatabaseError (500)
│   ├── DatabaseConnectionError
│   ├── RecordNotFoundError (404)
│   └── DuplicateRecordError (409)
├── AuthenticationError (401)
│   └── InvalidTokenError
├── AuthorizationError (403)
├── ValidationError (422)
└── RateLimitExceededError (429)
```

## Quick Start

### Raising Exceptions

```python
from app.core import DocumentNotFoundError

# Raise with document ID
raise DocumentNotFoundError("doc_123")

# Exception includes:
# - message: "Document not found: doc_123"
# - status_code: 404
# - details: {"document_id": "doc_123"}
```

### Catching Exceptions

```python
from app.core import DocumentError, DocumentNotFoundError

try:
    doc = get_document("doc_123")
except DocumentNotFoundError as e:
    # Handle specific case
    logger.warning(f"Document not found: {e.details['document_id']}")
    return None
except DocumentError as e:
    # Handle any document error
    logger.error(f"Document error: {e.message}")
    raise
```

## Exception Categories

### 1. Configuration Exceptions

For configuration and settings errors.

```python
from app.core import (
    ConfigurationError,
    InvalidSettingsError,
    MissingEnvironmentVariableError
)

# Missing environment variable
if not os.getenv("API_KEY"):
    raise MissingEnvironmentVariableError("API_KEY")

# Invalid settings
if settings.MAX_TOKENS < 1:
    raise InvalidSettingsError(
        "MAX_TOKENS must be positive",
        details={"value": settings.MAX_TOKENS}
    )
```

**Status Code:** 500

### 2. LLM Exceptions

For Large Language Model provider errors.

```python
from app.core import (
    LLMProviderError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMTimeoutError
)

# Provider error
try:
    response = await openai.complete(prompt)
except openai.APIError as e:
    raise LLMProviderError(
        message="OpenAI API error",
        provider="openai",
        model="gpt-4",
        details={"error": str(e)}
    )

# Rate limit
if response.status_code == 429:
    raise LLMRateLimitError(
        provider="openai",
        retry_after=60
    )

# Authentication
if response.status_code == 401:
    raise LLMAuthenticationError(provider="openai")

# Timeout
if time.time() - start > timeout:
    raise LLMTimeoutError(
        provider="openai",
        timeout=timeout
    )
```

**Status Code:** 503 (Service Unavailable)

### 3. Document Exceptions

For document processing errors.

```python
from app.core import (
    DocumentNotFoundError,
    DocumentParsingError,
    UnsupportedDocumentTypeError,
    DocumentTooLargeError
)

# Not found
doc = db.get_document(doc_id)
if not doc:
    raise DocumentNotFoundError(doc_id)

# Unsupported type
allowed = [".pdf", ".txt", ".docx"]
if file_ext not in allowed:
    raise UnsupportedDocumentTypeError(
        file_type=file_ext,
        supported_types=allowed
    )

# Too large
if file_size > MAX_SIZE:
    raise DocumentTooLargeError(
        size=file_size,
        max_size=MAX_SIZE
    )

# Parsing error
try:
    content = parse_pdf(file_path)
except Exception as e:
    raise DocumentParsingError(
        message="Failed to parse PDF",
        file_path=file_path,
        details={"error": str(e)}
    )
```

**Status Codes:** 400, 404, 413, 415, 422

### 4. Vector Store Exceptions

For vector database errors.

```python
from app.core import (
    VectorStoreConnectionError,
    CollectionNotFoundError,
    EmbeddingError
)

# Connection error
try:
    client = chromadb.Client()
except Exception as e:
    raise VectorStoreConnectionError(
        message="Failed to connect to ChromaDB",
        details={"error": str(e)}
    )

# Collection not found
if collection_name not in client.list_collections():
    raise CollectionNotFoundError(collection_name)

# Embedding error
try:
    embeddings = model.encode(texts)
except Exception as e:
    raise EmbeddingError(
        message="Failed to generate embeddings",
        details={"error": str(e), "model": model.name}
    )
```

**Status Code:** 500

### 5. Database Exceptions

For database operation errors.

```python
from app.core import (
    DatabaseConnectionError,
    RecordNotFoundError,
    DuplicateRecordError
)

# Connection error
try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    raise DatabaseConnectionError(
        message="Failed to connect to database",
        details={"error": str(e)}
    )

# Record not found
user = db.query(User).filter(User.id == user_id).first()
if not user:
    raise RecordNotFoundError(model="User", record_id=user_id)

# Duplicate record
existing = db.query(User).filter(User.email == email).first()
if existing:
    raise DuplicateRecordError(
        model="User",
        field="email",
        value=email
    )
```

**Status Codes:** 404, 409, 500

### 6. Authentication & Authorization

For auth-related errors.

```python
from app.core import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError
)

# Authentication failed
if not verify_password(password, user.password_hash):
    raise AuthenticationError("Invalid credentials")

# Invalid token
try:
    payload = jwt.decode(token, SECRET_KEY)
except jwt.InvalidTokenError:
    raise InvalidTokenError()

# Authorization failed
if user.role != "admin":
    raise AuthorizationError("Admin access required")
```

**Status Codes:** 401 (Authentication), 403 (Authorization)

### 7. Validation Exceptions

For input validation errors.

```python
from app.core import ValidationError

# Field validation
if not email.endswith("@example.com"):
    raise ValidationError(
        message="Email must be from example.com domain",
        field="email",
        details={"provided": email}
    )

# Custom validation
if len(password) < 8:
    raise ValidationError(
        message="Password must be at least 8 characters",
        field="password"
    )
```

**Status Code:** 422

### 8. Rate Limiting

For rate limit errors.

```python
from app.core import RateLimitExceededError

# Rate limit check
if requests_count > MAX_REQUESTS:
    raise RateLimitExceededError(
        message=f"Max {MAX_REQUESTS} requests per hour",
        retry_after=3600
    )
```

**Status Code:** 429

## Error Response Format

All exceptions return a consistent JSON format:

```json
{
  "error": {
    "type": "DocumentNotFoundError",
    "message": "Document not found: doc_123",
    "details": {
      "document_id": "doc_123"
    }
  }
}
```

### Response Fields

- **type**: Exception class name
- **message**: Human-readable error message
- **details**: Additional context (optional)

## FastAPI Integration

### Automatic Handling

Register exception handlers in your FastAPI app:

```python
from fastapi import FastAPI
from app.core import register_exception_handlers

app = FastAPI()

# Register all exception handlers
register_exception_handlers(app)
```

Now all custom exceptions are automatically handled:

```python
@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    # If exception is raised, it's automatically handled
    if not doc_exists(doc_id):
        raise DocumentNotFoundError(doc_id)
    
    return get_document(doc_id)
```

Response (404):
```json
{
  "error": {
    "type": "DocumentNotFoundError",
    "message": "Document not found: doc_123",
    "details": {
      "document_id": "doc_123"
    }
  }
}
```

### Manual Handling

You can also catch and handle exceptions manually:

```python
@app.post("/upload")
async def upload(file: UploadFile):
    try:
        doc_id = await process_file(file)
        return {"document_id": doc_id}
    
    except UnsupportedDocumentTypeError as e:
        # Return custom response
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "File type not supported",
                "supported": e.details["supported_types"]
            }
        )
    
    except DocumentError as e:
        # Let handler deal with it
        raise
```

## Common Patterns

### Pattern 1: Try-Except with Fallback

```python
from app.core import LLMProviderError, get_logger

logger = get_logger(__name__)

async def query_with_fallback(prompt: str) -> str:
    """Query LLM with fallback."""
    
    # Try primary LLM
    try:
        return await primary_llm.complete(prompt)
    
    except LLMProviderError as e:
        logger.warning(f"Primary LLM failed: {e.message}")
        
        # Try fallback
        try:
            logger.info("Attempting fallback LLM")
            return await fallback_llm.complete(prompt)
        
        except LLMProviderError as fallback_error:
            logger.error("All LLMs failed", exc_info=True)
            raise LLMProviderError(
                message="All LLM providers unavailable",
                details={
                    "primary_error": str(e),
                    "fallback_error": str(fallback_error)
                }
            )
```

### Pattern 2: Retry with Exponential Backoff

```python
import asyncio
from app.core import VectorStoreConnectionError, get_logger

logger = get_logger(__name__)

async def connect_with_retry(max_retries: int = 3):
    """Connect to vector store with retry."""
    
    for attempt in range(max_retries):
        try:
            await vector_store.connect()
            logger.info("Connected to vector store")
            return
        
        except VectorStoreConnectionError as e:
            if attempt == max_retries - 1:
                logger.error("Max retries reached", exc_info=True)
                raise
            
            wait_time = 2 ** attempt
            logger.warning(
                f"Connection attempt {attempt + 1} failed, "
                f"retrying in {wait_time}s"
            )
            await asyncio.sleep(wait_time)
```

### Pattern 3: Graceful Degradation

```python
from app.core import VectorStoreError, get_logger

logger = get_logger(__name__)

async def query_with_degradation(question: str) -> str:
    """Query with graceful degradation."""
    
    # Try with vector search
    try:
        docs = await vector_store.search(question)
        context = "\n".join(docs)
        return await llm.complete(f"Context: {context}\n\nQ: {question}")
    
    except VectorStoreError as e:
        logger.warning("Vector store unavailable, using direct LLM")
        # Fall back to LLM without context
        return await llm.complete(question)
```

### Pattern 4: Validation Before Processing

```python
from app.core import (
    UnsupportedDocumentTypeError,
    DocumentTooLargeError,
    get_logger
)

logger = get_logger(__name__)

async def validate_and_process(file_path: str, file_size: int):
    """Validate file before processing."""
    
    # Validate size
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    if file_size > MAX_SIZE:
        raise DocumentTooLargeError(
            size=file_size,
            max_size=MAX_SIZE
        )
    
    # Validate type
    allowed = [".pdf", ".txt", ".docx", ".md"]
    ext = os.path.splitext(file_path)[1]
    if ext not in allowed:
        raise UnsupportedDocumentTypeError(
            file_type=ext,
            supported_types=allowed
        )
    
    # Process file
    logger.info(f"Processing {file_path}")
    return await process_file(file_path)
```

### Pattern 5: Service Class with Error Handling

```python
from app.core import (
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
    get_logger
)

class UserService:
    """User service with error handling."""
    
    def __init__(self, db):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def get_user(self, user_id: str):
        """Get user by ID."""
        try:
            user = await self.db.get(User, user_id)
            
            if not user:
                raise RecordNotFoundError(
                    model="User",
                    record_id=user_id
                )
            
            return user
        
        except DatabaseError as e:
            self.logger.error("Database error", exc_info=True)
            raise
    
    async def create_user(self, email: str, password: str):
        """Create new user."""
        try:
            # Check for duplicate
            existing = await self.db.get_by_email(User, email)
            if existing:
                raise DuplicateRecordError(
                    model="User",
                    field="email",
                    value=email
                )
            
            # Create user
            user = User(email=email, password=hash_password(password))
            await self.db.add(user)
            
            self.logger.info(f"User created: {user.id}")
            return user
        
        except DatabaseError as e:
            self.logger.error("Failed to create user", exc_info=True)
            raise
```

## Best Practices

### ✅ Do

1. **Use Specific Exceptions**
   ```python
   # Good
   raise DocumentNotFoundError(doc_id)
   
   # Bad
   raise Exception("Document not found")
   ```

2. **Include Contextual Details**
   ```python
   raise LLMProviderError(
       message="API call failed",
       provider="openai",
       model="gpt-4",
       details={"status_code": 500}
   )
   ```

3. **Log Before Re-raising**
   ```python
   try:
       result = await process()
   except DocumentError as e:
       logger.error("Processing failed", exc_info=True)
       raise  # Re-raise for handler
   ```

4. **Catch Specific Exceptions First**
   ```python
   try:
       result = await operation()
   except DocumentNotFoundError:
       # Handle specific case
       pass
   except DocumentError:
       # Handle general case
       pass
   ```

5. **Use Exception Hierarchy**
   ```python
   # Catch all LLM errors
   try:
       response = await llm.complete(prompt)
   except LLMError as e:
       # Handles all: Provider, RateLimit, Timeout, etc.
       logger.error(f"LLM error: {e.message}")
   ```

### ❌ Don't

1. **Don't Use Generic Exceptions**
   ```python
   # Bad
   raise Exception("Something went wrong")
   
   # Good
   raise VectorStoreConnectionError("Failed to connect")
   ```

2. **Don't Catch and Ignore**
   ```python
   # Bad
   try:
       result = await operation()
   except:
       pass
   
   # Good
   try:
       result = await operation()
   except SpecificError as e:
       logger.error("Error occurred", exc_info=True)
       # Handle or re-raise
   ```

3. **Don't Lose Original Exception**
   ```python
   # Bad
   try:
       result = await operation()
   except Exception as e:
       raise NewError("Failed")
   
   # Good
   try:
       result = await operation()
   except Exception as e:
       raise NewError("Failed", details={"original": str(e)})
   ```

4. **Don't Mix HTTP and Domain Logic**
   ```python
   # Bad (in service layer)
   from fastapi import HTTPException
   raise HTTPException(status_code=404, detail="Not found")
   
   # Good (in service layer)
   raise DocumentNotFoundError(doc_id)
   ```

## Testing

### Test Exception Raising

```python
import pytest
from app.core import DocumentNotFoundError

def test_document_not_found():
    """Test DocumentNotFoundError is raised."""
    
    with pytest.raises(DocumentNotFoundError) as exc_info:
        get_document("invalid_id")
    
    # Check exception properties
    exc = exc_info.value
    assert exc.status_code == 404
    assert "invalid_id" in exc.message
    assert exc.details["document_id"] == "invalid_id"
```

### Test Exception Handling

```python
from fastapi.testclient import TestClient

def test_document_not_found_response(client: TestClient):
    """Test API returns proper error response."""
    
    response = client.get("/documents/invalid_id")
    
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["type"] == "DocumentNotFoundError"
    assert "invalid_id" in data["error"]["message"]
```

## Summary

The exception handling system provides:

- 🏗️ **Hierarchical exceptions** for organized error handling
- 📋 **Consistent error format** across all endpoints
- 🔍 **Detailed error context** for debugging
- 📊 **Automatic logging** of all errors
- 🔄 **Status code mapping** for proper HTTP responses
- 🎯 **Type-safe catching** with specific exception types

Start using exceptions:
```python
from app.core import DocumentNotFoundError

if not document_exists(doc_id):
    raise DocumentNotFoundError(doc_id)
```
