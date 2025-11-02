# Embedding & Vector DB Configuration - Quick Reference

## Quick Start

### Development (Free)
```bash
EMBEDDING_PROVIDER=huggingface  # Default, no API key needed
VECTOR_DB_PROVIDER=chroma        # Default, local storage
```

### Production (Recommended)
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=qdrant_...
```

## Embedding Providers

| Provider | Setup | API Key | Cost |
|----------|-------|---------|------|
| **huggingface** | Default | No | Free |
| **openai** | Add `OPENAI_API_KEY` | Yes | Paid |
| **google** | Add `GOOGLE_API_KEY` | Yes | Paid |
| **cohere** | Add `COHERE_API_KEY` | Yes | Paid |
| **voyage** | Add `VOYAGE_API_KEY` | Yes | Paid |

### Usage in Code
```python
from app.config import settings

config = settings.get_embedding_config()
# Returns: {"provider": "huggingface", "model": "...", ...}
```

## Vector Databases

| Provider | Environment | Setup |
|----------|-------------|-------|
| **chroma** | Dev Only ❌ | Default, local storage |
| **qdrant** | Dev + Prod ✅ | Local or cloud |
| **pinecone** | Prod ✅ | Cloud only |
| **weaviate** | Dev + Prod ✅ | Self-hosted or cloud |
| **milvus** | Dev + Prod ✅ | Self-hosted or cloud |

### Usage in Code
```python
from app.config import settings

config = settings.get_vector_db_config()
# Returns: {"provider": "qdrant", "host": "...", ...}
```

## Common Configurations

### 1. Local Development (Free)
```bash
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

VECTOR_DB_PROVIDER=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### 2. Production with OpenAI + Qdrant Cloud
```bash
ENVIRONMENT=production

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://my-cluster.qdrant.io
QDRANT_API_KEY=qdrant_...
```

### 3. Production with HuggingFace + Qdrant Local
```bash
ENVIRONMENT=production

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cuda  # If GPU available

VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=vector-db.internal
QDRANT_PORT=6333
```

### 4. Production with Cohere + Pinecone
```bash
ENVIRONMENT=production

EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=cohere_...
COHERE_EMBEDDING_MODEL=embed-english-v3.0

VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pinecone_...
PINECONE_ENVIRONMENT=us-west1-gcp
```

## Key Rules

### ✅ Allowed
- Any embedding provider in any environment
- Chroma in `development` and `staging`
- Qdrant anywhere (recommended for production)
- Pinecone, Weaviate, Milvus in production

### ❌ Not Allowed
- Chroma in `production` (will raise error)

## Environment Variables

### Minimal Required
```bash
# App basics
SECRET_KEY=...
ENVIRONMENT=development

# Use defaults for everything else
```

### Add Embedding Provider
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Add Vector Database
```bash
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=localhost  # or QDRANT_URL for cloud
```

## Testing Configuration

### Check Current Config
```python
from app.config import settings

print(f"Embedding: {settings.EMBEDDING_PROVIDER}")
print(f"Vector DB: {settings.VECTOR_DB_PROVIDER}")

embedding_config = settings.get_embedding_config()
vector_config = settings.get_vector_db_config()

print(f"Embedding config: {embedding_config}")
print(f"Vector DB config: {vector_config}")
```

## Error Messages

### Chroma in Production
```
ValueError: Chroma is not recommended for production. 
Please use Qdrant, Pinecone, Weaviate, or Milvus instead.
```

**Fix:** Change `VECTOR_DB_PROVIDER` to `qdrant` or another production DB

### Missing API Key
```
ValueError: OPENAI_API_KEY is required for OpenAI embeddings
```

**Fix:** Add `OPENAI_API_KEY=sk-...` to `.env`

### Invalid Provider
```
ValueError: Unsupported EMBEDDING_PROVIDER: invalid_name
```

**Fix:** Use one of: `huggingface`, `openai`, `google`, `cohere`, `voyage`

## Migration Guide

### Step 1: Start Local
```bash
EMBEDDING_PROVIDER=huggingface
VECTOR_DB_PROVIDER=chroma
```

### Step 2: Add Staging with Qdrant
```bash
# staging.env
EMBEDDING_PROVIDER=huggingface
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=staging-qdrant
```

### Step 3: Production with Cloud Services
```bash
# production.env
ENVIRONMENT=production
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://prod.qdrant.io
QDRANT_API_KEY=...
```

## Troubleshooting

### Can't connect to Qdrant
1. Check `QDRANT_HOST` and `QDRANT_PORT`
2. Ensure Qdrant is running: `docker ps | grep qdrant`
3. Try `curl http://localhost:6333/health`

### Chroma persistence issues
1. Check `CHROMA_PERSIST_DIRECTORY` exists and is writable
2. Ensure path is absolute or relative to app root
3. Check disk space

### Embedding generation slow
1. If using HuggingFace, set `HF_EMBEDDING_DEVICE=cuda` if GPU available
2. Consider switching to API-based provider (OpenAI, Cohere)
3. Check model size (smaller = faster)

## Best Practices

### Development
- ✅ Use HuggingFace embeddings (free, local)
- ✅ Use Chroma (simple, no setup)
- ✅ Keep models small for speed

### Staging
- ✅ Use production-like setup
- ✅ Test with Qdrant or target prod DB
- ✅ Same embedding provider as prod

### Production
- ✅ Use managed services (Qdrant Cloud, Pinecone)
- ✅ Use API-based embeddings (OpenAI, Cohere)
- ✅ Enable monitoring and backups
- ❌ Never use Chroma

## Cost Optimization

### Free Options
- **Embeddings:** HuggingFace (self-hosted)
- **Vector DB:** Qdrant (self-hosted), Chroma (dev only)

### Paid but Cost-Effective
- **Embeddings:** OpenAI text-embedding-3-small ($0.02/1M tokens)
- **Vector DB:** Qdrant Cloud (starts at $25/month)

### Premium Options
- **Embeddings:** OpenAI text-embedding-3-large (higher quality)
- **Vector DB:** Pinecone (fully managed, auto-scaling)

## Summary

**Quick Setup:** Just set provider names in `.env`
```bash
EMBEDDING_PROVIDER=huggingface  # or openai, google, cohere, voyage
VECTOR_DB_PROVIDER=chroma       # or qdrant, pinecone, weaviate, milvus
```

**Add API keys as needed** based on provider requirements

**Remember:** Chroma = dev only, Qdrant = recommended for production
