# Settings Configuration - Modular Architecture

## Overview

The RAG Fortress settings system has been refactored into a modular architecture for improved maintainability and readability. Instead of one large monolithic settings file, configurations are now organized into focused modules based on their purpose.

## Structure

```
backend/app/config/
├── __init__.py              # Package exports
├── settings.py              # Main Settings class (composition)
├── app_settings.py          # General app configuration
├── llm_settings.py          # LLM provider configuration
├── embedding_settings.py    # Embedding provider configuration
├── vectordb_settings.py     # Vector database configuration
└── database_settings.py     # SQL database configuration
```

## Modules

### 1. AppSettings (`app_settings.py`)

General application configuration including:
- Application metadata (name, version, environment)
- Server settings (host, port)
- RAG parameters (chunk size, overlap, top-k, similarity threshold)
- Security settings (secret key, JWT algorithm, token expiration)
- CORS configuration
- Logging settings

**Key Methods:**
- `validate_environment()`: Ensures environment is one of: development, staging, production
- `validate_log_level()`: Validates log level
- `validate_rag_config()`: Ensures RAG parameters are valid

### 2. LLMSettings (`llm_settings.py`)

LLM provider configuration for:
- **OpenAI**: GPT models
- **Google**: Gemini models
- **HuggingFace**: Llama, Flan-T5, and other models
- **Fallback LLM**: Configurable backup with smart defaults

**Key Methods:**
- `get_llm_config()`: Returns configuration dict for active provider
- `get_fallback_llm_config()`: Returns fallback configuration with smart defaults
- `validate_llm_config()`: Validates primary LLM configuration
- `validate_fallback_config()`: Ensures fallback differs from primary

### 3. EmbeddingSettings (`embedding_settings.py`)

Embedding provider configuration for:
- **HuggingFace**: Sentence transformers (default, free)
- **OpenAI**: text-embedding models
- **Google**: Gemini embedding models
- **Cohere**: embed-english models
- **Voyage AI**: voyage-2 model

**Key Methods:**
- `get_embedding_config()`: Returns configuration dict for active provider
- `validate_config()`: Validates provider configuration and API keys

### 4. VectorDBSettings (`vectordb_settings.py`)

Vector database configuration for:
- **Chroma**: Development only (not recommended for production)
- **Qdrant**: Recommended for production
- **Pinecone**: Fully managed vector database
- **Weaviate**: Open-source vector search engine
- **Milvus**: High-performance vector database

**Key Methods:**
- `get_vector_db_config()`: Returns configuration dict for active provider
- `validate_config()`: Validates provider configuration and enforces production restrictions

### 5. DatabaseSettings (`database_settings.py`)

SQL database configuration for user data and application metadata:
- **PostgreSQL**: Recommended for production (robust, ACID-compliant)
- **MySQL**: Alternative for production (widely supported)
- **SQLite**: Development/testing only (simple, file-based)

**Key Methods:**
- `get_database_url()`: Returns SQLAlchemy database URL for sync operations
- `get_async_database_url()`: Returns async SQLAlchemy database URL
- `get_database_config()`: Returns complete database configuration including pool settings
- `validate_config()`: Validates provider configuration and enforces production restrictions

📚 **Detailed Guide**: See `docs/database-configuration.md` for comprehensive database setup

### 6. Settings (`settings.py`)

Main settings class that composes all specialized modules using multiple inheritance.

**Key Method:**
- `validate_all()`: Runs all validation methods across all modules

## Usage

### Basic Import

```python
from app.config import settings

# Access any setting
print(settings.APP_NAME)
print(settings.APP_DESCRIPTION)
print(settings.LLM_PROVIDER)
print(settings.EMBEDDING_PROVIDER)
print(settings.VECTOR_DB_PROVIDER)
print(settings.DATABASE_PROVIDER)
```

### Get Provider Configurations

```python
from app.config import settings

# Get LLM configuration
llm_config = settings.get_llm_config()
# Returns: {"provider": "openai", "api_key": "...", "model": "gpt-3.5-turbo", ...}

# Get fallback LLM configuration
fallback_config = settings.get_fallback_llm_config()

# Get embedding configuration
embedding_config = settings.get_embedding_config()

# Get vector database configuration
vectordb_config = settings.get_vector_db_config()

# Get SQL database configuration
database_url = settings.get_database_url()
# Returns: postgresql://user:pass@localhost:5432/rag_fortress
#      or: mysql+pymysql://user:pass@localhost:3306/rag_fortress
#      or: sqlite:///./rag_fortress.db

# Get async database URL
async_database_url = settings.get_async_database_url()
# Returns: postgresql+asyncpg://... or mysql+aiomysql://... or sqlite+aiosqlite://...

# Get complete database config with pool settings
database_config = settings.get_database_config()
```

### Validate All Settings

```python
from app.config import settings

try:
    settings.validate_all()
    print("All settings are valid!")
except ValueError as e:
    print(f"Configuration error: {e}")
```

### Import Specific Modules

```python
from app.config import AppSettings, LLMSettings, EmbeddingSettings, VectorDBSettings

# Use specific modules if needed
app_settings = AppSettings()
llm_settings = LLMSettings()
```

## Environment Variables

All settings can be configured via environment variables in the `.env` file. See `.env.example` for a complete list of available variables.

### Example Configuration

```bash
# General App Settings
APP_NAME=RAG Fortress
APP_DESCRIPTION=Secure document intelligence platform for teams
ENVIRONMENT=development
DEBUG=True

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Fallback LLM (optional)
FALLBACK_LLM_PROVIDER=huggingface
FALLBACK_LLM_MODEL=google/flan-t5-small

# Embedding Configuration
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Database Configuration
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Benefits of Modular Architecture

1. **Improved Readability**: Each module focuses on one aspect of configuration
2. **Easier Maintenance**: Changes to LLM configuration don't affect embedding settings
3. **Better Organization**: Related settings are grouped together
4. **No Performance Impact**: Multiple inheritance in Pydantic is efficient
5. **Cleaner Imports**: Can import specific modules if needed
6. **Self-Documenting**: Module names clearly indicate their purpose
7. **Easier Testing**: Can test each module independently

## Migration Notes

The refactoring maintains **100% backward compatibility**. All existing code using `settings` will continue to work without any changes:

```python
# This still works exactly as before
from app.config import settings

settings.OPENAI_API_KEY
settings.get_llm_config()
settings.get_embedding_config()
```

## Production Considerations

### Environment-Specific Validation

The settings system enforces certain restrictions in production:

1. **Chroma Database**: Blocked in production (use Qdrant, Pinecone, Weaviate, or Milvus)
2. **Debug Mode**: Automatically disabled in production
3. **Log Level**: Automatically set to WARNING in production

### API Key Validation

Settings validate that required API keys are present based on the selected provider:

- OpenAI embeddings require `OPENAI_API_KEY`
- Google embeddings require `GOOGLE_API_KEY`
- Cohere embeddings require `COHERE_API_KEY`
- Voyage embeddings require `VOYAGE_API_KEY`
- HuggingFace embeddings can work without API key for public models

## Testing

Run the comprehensive test suite to ensure everything works:

```bash
cd backend
pytest tests/test_settings.py -v
```

The test suite includes 53 test cases covering:
- All provider configurations
- Fallback LLM logic
- Production restrictions
- Validation rules
- Edge cases and error handling
