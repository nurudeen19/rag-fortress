# Embedding & Vector Database Configuration - Implementation Summary

## Overview

Extended the settings system to support multiple embedding providers and vector databases with the same modular approach as LLM configuration.

## What Was Added

### Embedding Providers (5 providers)

1. **HuggingFace** (default) - Sentence Transformers
   - No API key required for public models
   - CPU or CUDA device support
   - Default model: `sentence-transformers/all-MiniLM-L6-v2`

2. **OpenAI** - text-embedding-3 series
   - Requires API key
   - Supports custom dimensions
   - Models: text-embedding-3-small, text-embedding-3-large, ada-002

3. **Google** - Gemini embeddings
   - Requires API key only
   - Model: gemini-embedding-001
   - Supports custom dimensions (768, 1536, 3072)
   - Configurable task types (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)

4. **Cohere** - embed-english-v3.0
   - Requires API key
   - Supports different input types (search_document, search_query, classification, clustering)

5. **Voyage AI** - High-quality embeddings
   - Requires API key
   - Model: voyage-2

### Vector Databases (5 providers)

1. **Chroma** (default for local/dev)
   - ❌ **NOT allowed in production**
   - Local persistent storage
   - No API key required
   - Easy setup for development

2. **Qdrant** (recommended for production)
   - ✅ **Recommended for production**
   - Supports local and cloud deployment
   - Local: host + port configuration
   - Cloud: URL + API key
   - gRPC support optional

3. **Pinecone** (cloud-based)
   - ✅ **Production-ready**
   - Fully managed cloud service
   - Requires API key and environment
   - Auto-scaling

4. **Weaviate** (open-source)
   - ✅ **Production-ready**
   - Self-hosted or cloud
   - GraphQL API
   - Optional API key for cloud

5. **Milvus** (scalable)
   - ✅ **Production-ready**
   - High-performance vector search
   - Optional authentication
   - Distributed architecture

## Configuration Methods

### New Methods in Settings Class

```python
# Get embedding configuration
config = settings.get_embedding_config()
# Returns: {
#     "provider": "huggingface",
#     "model": "sentence-transformers/all-MiniLM-L6-v2",
#     "device": "cpu",
#     ...
# }

# Get vector database configuration
config = settings.get_vector_db_config()
# Returns: {
#     "provider": "qdrant",
#     "host": "localhost",
#     "port": 6333,
#     "collection_name": "rag_documents",
#     ...
# }
```

### Validation Methods

```python
# Validates embedding provider and required fields
settings._validate_embedding_config()

# Validates vector DB provider and production restrictions
settings._validate_vector_db_config()
```

## Environment Variables

### Embedding Provider

```bash
# Provider selection (default: huggingface)
EMBEDDING_PROVIDER=huggingface

# OpenAI
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536  # Optional

# Google
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
GOOGLE_EMBEDDING_DIMENSIONS=768  # Optional: 768, 1536, or 3072
GOOGLE_EMBEDDING_TASK_TYPE=RETRIEVAL_DOCUMENT

# HuggingFace (default)
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cpu  # or cuda

# Cohere
COHERE_API_KEY=your-api-key
COHERE_EMBEDDING_MODEL=embed-english-v3.0
COHERE_INPUT_TYPE=search_document

# Voyage AI
VOYAGE_API_KEY=your-api-key
VOYAGE_EMBEDDING_MODEL=voyage-2
```

### Vector Database

```bash
# Provider selection (default: chroma)
VECTOR_DB_PROVIDER=chroma

# Qdrant (local)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_PREFER_GRPC=false
QDRANT_COLLECTION_NAME=rag_documents

# Qdrant (cloud)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key

# Chroma (dev only)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=rag_documents

# Pinecone
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=rag-documents

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key  # Optional
WEAVIATE_CLASS_NAME=Document

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=rag_documents
MILVUS_USER=username  # Optional
MILVUS_PASSWORD=password  # Optional
```

## Validation Rules

### Embedding Provider Validation

- ✅ Supported providers: openai, google, huggingface, cohere, voyage
- ✅ OpenAI requires: `OPENAI_API_KEY`
- ✅ Google requires: `GOOGLE_API_KEY`, `GOOGLE_PROJECT_ID`
- ✅ Cohere requires: `COHERE_API_KEY`
- ✅ Voyage requires: `VOYAGE_API_KEY`
- ✅ HuggingFace: No API key required (optional for private models)

### Vector Database Validation

- ✅ Supported providers: chroma, qdrant, pinecone, weaviate, milvus
- ❌ **Chroma NOT allowed in production** (raises ValueError)
- ✅ Qdrant Cloud requires: `QDRANT_URL`, `QDRANT_API_KEY`
- ✅ Qdrant Local: Uses host + port (API key optional)
- ✅ Pinecone requires: `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`
- ✅ Weaviate: Works with just URL (API key optional)
- ✅ Milvus: Works with defaults (auth optional)

## Usage Examples

### Development Setup (defaults)

```bash
# .env
EMBEDDING_PROVIDER=huggingface
VECTOR_DB_PROVIDER=chroma
```

No API keys required!

### Production Setup (Qdrant + OpenAI)

```bash
# .env
ENVIRONMENT=production
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://my-cluster.qdrant.io
QDRANT_API_KEY=qdrant_key_...
```

### Production Setup (Qdrant Local + HuggingFace)

```bash
# .env
ENVIRONMENT=production
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_DEVICE=cuda  # If GPU available

VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=vector-db.internal
QDRANT_PORT=6333
```

### Multi-Provider Example

```python
from app.config import settings

# Get embedding config
embedding_config = settings.get_embedding_config()
print(f"Using {embedding_config['provider']} for embeddings")

# Get vector DB config
vector_config = settings.get_vector_db_config()
print(f"Using {vector_config['provider']} for vector storage")

# Both configs are ready to pass to initialization functions
embedder = create_embedder(**embedding_config)
vector_store = create_vector_store(**vector_config)
```

## Test Coverage

### New Test Classes

1. **TestEmbeddingProviderConfiguration** (14 tests)
   - Default provider (HuggingFace)
   - All 5 providers configuration
   - Invalid provider handling
   - Missing API key validation for each provider

2. **TestVectorDBConfiguration** (19 tests)
   - Default provider (Chroma)
   - Chroma production restriction
   - Qdrant local vs cloud configuration
   - Pinecone configuration and validation
   - Weaviate with/without API key
   - Milvus with/without auth
   - Invalid provider handling

**Total New Tests:** 33 tests

## Files Modified

### Configuration
- **`backend/app/config/settings.py`**
  - Added 30+ new settings fields
  - Added 3 new validation methods
  - Added 2 new config getter methods

### Environment
- **`backend/.env`**
  - Added 40+ new environment variables
  - Organized into clear sections

- **`backend/.env.example`**
  - Added comprehensive documentation
  - Examples for each provider
  - Production vs development guidance

### Tests
- **`backend/tests/test_settings.py`**
  - Updated `clean_env` fixture
  - Added 33 new test cases
  - Full coverage of new functionality

## Provider Comparison

### Embedding Providers

| Provider | API Key | Default Model | Dimensions | Use Case |
|----------|---------|---------------|------------|----------|
| HuggingFace | No* | all-MiniLM-L6-v2 | 384 | Development, Cost-free |
| OpenAI | Yes | text-embedding-3-small | 1536 | Production, High-quality |
| Google | Yes | gemini-embedding-001 | 768 | Production, Multi-modal |
| Cohere | Yes | embed-english-v3.0 | 1024 | Multi-lingual |
| Voyage | Yes | voyage-2 | 1024 | Latest research |

*Optional for public models

### Vector Databases

| Provider | Deployment | Production | API Key | Use Case |
|----------|-----------|------------|---------|----------|
| Chroma | Local | ❌ No | No | Development only |
| Qdrant | Both | ✅ Yes | Optional | Recommended |
| Pinecone | Cloud | ✅ Yes | Yes | Fully managed |
| Weaviate | Both | ✅ Yes | Optional | GraphQL API |
| Milvus | Both | ✅ Yes | Optional | High performance |

## Production Recommendations

### Embedding Provider

1. **Best Quality:** OpenAI text-embedding-3-large
2. **Best Value:** OpenAI text-embedding-3-small
3. **Self-Hosted:** HuggingFace with GPU
4. **Multi-lingual:** Cohere embed-multilingual

### Vector Database

1. **Cloud Managed:** Qdrant Cloud or Pinecone
2. **Self-Hosted:** Qdrant or Milvus
3. **GraphQL API:** Weaviate
4. **Development:** Chroma (local only)

## Migration Path

### From Chroma to Qdrant

```bash
# Development
VECTOR_DB_PROVIDER=chroma

# Staging
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=staging-qdrant.internal

# Production
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://prod-cluster.qdrant.io
QDRANT_API_KEY=prod_key_...
```

### From Basic to OpenAI Embeddings

```bash
# Start with free HuggingFace
EMBEDDING_PROVIDER=huggingface

# Upgrade to OpenAI for better quality
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Error Handling

### Production Safety

```python
# Will raise ValueError in production
ENVIRONMENT=production
VECTOR_DB_PROVIDER=chroma
# ValueError: Chroma is not recommended for production
```

### Missing API Keys

```python
# Will raise ValueError
EMBEDDING_PROVIDER=openai
# ValueError: OPENAI_API_KEY is required for OpenAI embeddings

VECTOR_DB_PROVIDER=pinecone
# ValueError: PINECONE_API_KEY is required for Pinecone provider
```

### Invalid Providers

```python
EMBEDDING_PROVIDER=invalid
# ValueError: Unsupported EMBEDDING_PROVIDER: invalid

VECTOR_DB_PROVIDER=redis
# ValueError: Unsupported VECTOR_DB_PROVIDER: redis
```

## Summary

✅ **5 embedding providers** - HuggingFace (default), OpenAI, Google, Cohere, Voyage  
✅ **5 vector databases** - Chroma (dev), Qdrant, Pinecone, Weaviate, Milvus  
✅ **Production validation** - Chroma blocked in production  
✅ **Modular configuration** - Same pattern as LLM providers  
✅ **Comprehensive tests** - 33 new test cases  
✅ **Full documentation** - Environment variables documented  
✅ **Default to free** - HuggingFace embeddings + Chroma for development  
✅ **Production ready** - Qdrant recommended, Pinecone/Weaviate/Milvus supported  

The system now supports:
- **Free development** with HuggingFace + Chroma
- **Production deployment** with any combination of providers
- **Environment-based restrictions** (Chroma dev-only)
- **Flexible configuration** for local or cloud services
- **Comprehensive validation** of required fields
