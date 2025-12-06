# Settings & Configuration Guide

## Overview

RAG Fortress uses a modular settings architecture with environment-based configuration. Settings are organized into focused modules for maintainability and clarity.

## Configuration Structure

```
app/config/
├── settings.py              # Main Settings (composition)
├── app_settings.py          # Application config
├── llm_settings.py          # LLM providers
├── embedding_settings.py    # Embedding providers
├── vectordb_settings.py     # Vector databases
└── database_settings.py     # SQL databases
```

## Quick Start

### Basic Usage

```python
from app.config import settings

# Access settings
settings.APP_NAME
settings.LLM_PROVIDER
settings.EMBEDDING_PROVIDER
settings.VECTOR_DB_PROVIDER

# Get provider configurations
llm_config = settings.get_llm_config()
embedding_config = settings.get_embedding_config()
vectordb_config = settings.get_vector_db_config()
database_url = settings.get_database_url()

# Validate all settings
settings.validate_all()
```

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Application
APP_NAME=RAG Fortress
ENVIRONMENT=development  # development/staging/production
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost/rag_fortress

# LLM Provider (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Embedding Provider
EMBEDDING_PROVIDER=huggingface  # Free, no API key
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Database
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333
```

## Configuration Modules

### 1. AppSettings

**Core application configuration:**
- App metadata (name, version, environment)
- Server settings (host, port)
- Security (secret key, JWT, CORS)
- RAG parameters (chunk size, overlap, top-k, similarity threshold)
- Logging configuration

**Key Settings:**
- `ENVIRONMENT`: development/staging/production
- `DEBUG`: Boolean (auto-disabled in production)
- `SECRET_KEY`: Required for JWT
- `CHUNK_SIZE`: Default 1000
- `CHUNK_OVERLAP`: Default 200
- `TOP_K_RESULTS`: Default 5

### 2. LLMSettings

**Supported Providers:**
- **OpenAI**: GPT-3.5, GPT-4
- **Google**: Gemini Pro
- **HuggingFace**: Llama, Flan-T5
- **Llama.cpp**: Local GGUF models

**Fallback LLM:**
Configure automatic fallback if primary fails:
```bash
FALLBACK_LLM_PROVIDER=huggingface
FALLBACK_LLM_MODEL=google/flan-t5-base
```

**Key Methods:**
- `get_llm_config()`: Primary LLM configuration
- `get_fallback_llm_config()`: Fallback configuration
- `validate_llm_config()`: Validates API keys and models

### 3. EmbeddingSettings

**Supported Providers:**
- **HuggingFace**: Free, no API key (default)
- **OpenAI**: text-embedding-3-small/large
- **Google**: gemini-embedding-001
- **Cohere**: embed-english-v3.0
- **Voyage AI**: voyage-2

**Configuration:**
```bash
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cpu  # or cuda
```

### 4. VectorDBSettings

**Supported Providers:**
- **Chroma**: Development only ⚠️
- **Qdrant**: Recommended for production ✅
- **Pinecone**: Managed cloud service
- **Weaviate**: Self-hosted or cloud
- **Milvus**: High-performance

**Production Restriction:**
Chroma is blocked in production. Use Qdrant/Pinecone/Weaviate instead.

**Qdrant Configuration:**
```bash
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-api-key
QDRANT_COLLECTION_NAME=rag_fortress
```

### 5. DatabaseSettings

**Supported Databases:**
- **PostgreSQL**: Recommended for production (asyncpg)
- **MySQL**: Alternative for production (aiomysql)
- **SQLite**: Development only (aiosqlite)

**Configuration:**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/rag_fortress
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=False
```

**Methods:**
- `get_database_url()`: Sync connection string
- `get_async_database_url()`: Async connection string
- `get_database_config()`: Complete config with pool settings

## Provider Selection Guide

### Development Setup (Free)

```bash
LLM_PROVIDER=huggingface
HF_API_TOKEN=  # Optional for public models
HF_LLM_MODEL=google/flan-t5-base

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

VECTOR_DB_PROVIDER=chroma
CHROMA_PERSIST_DIRECTORY=./data/vector_store

DATABASE_URL=sqlite:///./rag_fortress.db
```

### Production Setup (Recommended)

```bash
ENVIRONMENT=production

LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

FALLBACK_LLM_PROVIDER=google
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-pro

EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=...

DATABASE_URL=postgresql://user:pass@host:5432/rag_fortress
```

## Validation & Error Handling

### Automatic Validation

Settings are validated on application startup:

```python
from app.config import settings

settings.validate_all()  # Runs all validators
```

**Validation Checks:**
- Required API keys for selected providers
- Environment values (development/staging/production)
- RAG parameter ranges (chunk size, top-k, etc.)
- Fallback LLM differs from primary
- Production restrictions (no Chroma, no SQLite)

### Common Validation Errors

**Missing API Key:**
```
ConfigurationError: OPENAI_API_KEY is required when LLM_PROVIDER=openai
```

**Production Restriction:**
```
ConfigurationError: Chroma is not allowed in production. Use Qdrant, Pinecone, or Weaviate
```

**Invalid Fallback:**
```
ConfigurationError: Fallback LLM must be different from primary LLM
```

## Advanced Configuration

### Internal LLM

Use separate LLM for sensitive operations:

```bash
INTERNAL_LLM_PROVIDER=huggingface
INTERNAL_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
INTERNAL_HF_API_TOKEN=...
```

### Caching

```bash
ENABLE_CACHING=True
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300
```

### Reranking

```bash
ENABLE_RERANKER=True
RERANKER_PROVIDER=huggingface
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=3
RERANKER_SCORE_THRESHOLD=0.3
```

### Adaptive Retrieval

```bash
MIN_TOP_K=3
MAX_TOP_K=10
RETRIEVAL_SCORE_THRESHOLD=0.5
```

## Testing

```bash
# Run all configuration tests
pytest tests/test_config/ -v

# Test specific module
pytest tests/test_config/test_llm_settings.py -v

# Test production restrictions
pytest tests/test_config/test_production_restrictions.py -v
```

## Migration Notes

The modular architecture maintains **100% backward compatibility**. All existing imports continue to work:

```python
from app.config import settings

# All attributes still accessible
settings.OPENAI_API_KEY
settings.LLM_PROVIDER
settings.get_llm_config()
```

## Troubleshooting

### Settings Not Loading

**Check `.env` file location:**
```bash
backend/.env  # Should be here
```

**Verify environment variables:**
```python
import os
print(os.getenv("LLM_PROVIDER"))
```

### Provider Not Working

**Verify API key:**
```python
from app.config import settings
print(settings.OPENAI_API_KEY)  # Should not be None
```

**Check provider spelling:**
- Correct: `openai`, `google`, `huggingface`
- Incorrect: `OpenAI`, `GOOGLE`, `hf`

### Production Issues

**Debug mode enabled:**
```bash
# Ensure DEBUG is not True in production
DEBUG=False
ENVIRONMENT=production
```

**Invalid vector database:**
```bash
# Don't use Chroma in production
VECTOR_DB_PROVIDER=qdrant  # or pinecone/weaviate/milvus
```

## See Also

- [Installation Guide](installation-guide.md) - Setup instructions
- [Vector Store Architecture](vector-store-architecture.md) - Vector database details
- [Fallback LLM Guide](FALLBACK_LLM_GUIDE.md) - Fallback configuration
- [Exception Handling](EXCEPTION_HANDLING_GUIDE.md) - Error handling
