# Settings & Configuration Guide

## Overview

This document describes the actual settings modules and environment variables used by the backend.
It is intentionally concise and mirrors the code in `app/config/` so you can use it as a quick reference.

## Files (actual config modules)

The configuration is modular and implemented in `backend/app/config/`:

```
app/config/
├── settings.py              # Main composed settings class (Settings)
├── app_settings.py          # General application settings
├── llm_settings.py          # LLM provider configuration
├── embedding_settings.py    # Embedding provider configuration
├── vectordb_settings.py     # Vector database configuration
├── database_settings.py     # SQL/database configuration
├── prompt_settings.py       # Prompt templates and defaults
├── email_settings.py        # SMTP / email link configuration
└── cache_settings.py        # Cache backend and TTLs
```

A single `Settings` instance is exposed from `app.config.settings` and composes all modules:

```python
from app.config import settings

# Examples
settings.APP_NAME
settings.LLM_PROVIDER
settings.get_llm_config()
settings.get_embedding_config()
settings.get_vector_db_config()
settings.get_database_config()
settings.validate_all()
```

## Key environment variables (by module)

Below are the primary environment variables used by each config module. Defaults shown are the code defaults.

- App / application (in `app_settings.py`)
  - `APP_NAME` ("RAG Fortress")
  - `APP_VERSION` ("0.1.0")
  - `ENVIRONMENT` ("development") — one of `development`, `staging`, `production`
  - `DEBUG` (False)
  - `DEMO_MODE` (False) — when True, destructive endpoints are blocked by the `prevent_in_demo_mode` decorator
  - `HOST`, `PORT` ("0.0.0.0", 8000)
  - RAG parameters: `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MIN_TOP_K`, `MAX_TOP_K`, `RETRIEVAL_SCORE_THRESHOLD`, `SIMILARITY_THRESHOLD`
  - Reranker: `ENABLE_RERANKER`, `RERANKER_MODEL`, `RERANKER_TOP_K`, `RERANKER_SCORE_THRESHOLD`
  - Logging: `LOG_LEVEL`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`

- LLMs (in `llm_settings.py`)
  - `LLM_PROVIDER` (default: `openai`) — supported providers: `openai`, `google`, `huggingface`, `llamacpp`
  - OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS`
  - Google: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, `GOOGLE_TEMPERATURE`, `GOOGLE_MAX_TOKENS`
  - HuggingFace: `HF_API_TOKEN`, `HF_MODEL`, `HF_ENDPOINT_URL`, `HF_TASK`, `HF_TEMPERATURE`, `HF_MAX_TOKENS`
  - Llama.cpp: `LLAMACPP_MODE`, `LLAMACPP_MODEL_PATH`, `LLAMACPP_ENDPOINT_URL`, `LLAMACPP_ENDPOINT_MODEL`, `LLAMACPP_ENDPOINT_API_KEY`, `LLAMACPP_*` tuning vars
  - Fallback/internal LLM: `FALLBACK_LLM_PROVIDER`, `FALLBACK_LLM_MODEL`, `USE_INTERNAL_LLM`, `INTERNAL_LLM_PROVIDER`, etc.

- Embeddings (in `embedding_settings.py`)
  - `EMBEDDING_PROVIDER` (default: `huggingface`) — supported: `openai`, `google`, `huggingface`, `cohere`
  - OpenAI embedding key: `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`
  - HF embedding model: `HF_EMBEDDING_MODEL`, `HF_EMBEDDING_DEVICE`, `HF_API_TOKEN`
  - Cohere: `COHERE_API_KEY`, `COHERE_EMBEDDING_MODEL`

- Vector DB (in `vectordb_settings.py`)
  - `VECTOR_DB_PROVIDER` (default: `chroma`) — supported: `chroma`, `qdrant`, `pinecone`, `weaviate`, `milvus`
  - Qdrant: `QDRANT_URL` or `QDRANT_HOST`/`QDRANT_PORT`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_NAME`
  - Pinecone: `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`
  - Weaviate / Milvus: provider-specific host/url and class/collection names

- Database (in `database_settings.py`)
  - `DATABASE_PROVIDER` (default: `postgresql`) — one of `postgresql`, `mysql`, `sqlite`
  - Unified fields (Postgres/MySQL): `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - SQLite-specific: `SQLITE_PATH` (example default `./rag_fortress.db`)
  - Pooling & flags: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_ECHO`, `DB_AUTO_MIGRATE`, `DB_DROP_ALL`

- Prompt (in `prompt_settings.py`)
  - `RAG_SYSTEM_PROMPT`, `NO_CONTEXT_RESPONSE`

- Email (in `email_settings.py`)
  - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`, `SMTP_USE_SSL`
  - Frontend links used in email templates: `FRONTEND_URL`, `EMAIL_VERIFICATION_URL`, `PASSWORD_RESET_URL`, `INVITE_URL`

- Cache (in `cache_settings.py`)
  - `CACHE_ENABLED`, `CACHE_BACKEND` (`memory` or `redis`), `CACHE_REDIS_URL` (or `CACHE_REDIS_HOST`, `CACHE_REDIS_PORT`, ...)
  - TTLs: `CACHE_TTL_DEFAULT`, `CACHE_TTL_STATS`, etc.

## Important behavior notes

- Settings are composed in `Settings` (in `settings.py`) which supports loading overrides from a cached DB layer. Priority is: explicit kwargs → cached DB → ENV → defaults.
- Sensitive values stored in cache are kept encrypted and are decrypted on-demand by attribute access.
- Validation: call `settings.validate_all()` to run cross-module checks. This is executed at application startup.

## Demo mode

- Toggle with `DEMO_MODE=True`. When enabled, the `prevent_in_demo_mode` decorator in `app/utils/demo_mode.py` will block annotated endpoints and return HTTP 403 for destructive operations.

## Seeder control

- Seeders are controlled via `setup.py` and `run_seeders.py`. You can limit or skip seeders using environment variables or CLI flags:

```bash
ENABLED_SEEDERS=admin,roles_permissions   # only these seeders will run (comma-separated)
DISABLED_SEEDERS=knowledge_base          # skip these seeders
# CLI flags override env vars: python setup.py --only-seeder admin,roles_permissions
```

Note: `ENABLED_SEEDERS` takes priority when both are set.

## Examples: development vs production

- Development (local, inexpensive providers):

```bash
ENVIRONMENT=development
DATABASE_PROVIDER=sqlite
SQLITE_PATH=./rag_fortress.db
LLM_PROVIDER=huggingface
EMBEDDING_PROVIDER=huggingface
VECTOR_DB_PROVIDER=chroma
CACHE_BACKEND=memory
DEMO_MODE=True
```

- Production (recommended variables):

```bash
ENVIRONMENT=production
DATABASE_PROVIDER=postgresql
DB_HOST=db.example.com
DB_PORT=5432
DB_USER=rag_fortress
DB_PASSWORD=secure_password
DB_NAME=rag_fortress

LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=...

CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://:password@redis.example.com:6379/0
```

## Validation & common errors

- Use `settings.validate_all()` to run validations performed by each module.
- Common runtime checks enforced by code:
  - `ENVIRONMENT` must be one of `development`, `staging`, `production`.
  - If `ENVIRONMENT=production`, `DATABASE_PROVIDER` must not be `sqlite`.
  - If `ENVIRONMENT=production`, Chroma is discouraged/invalid as a vector DB.
  - Required API keys: e.g., `OPENAI_API_KEY` for OpenAI LLM/embeddings, `PINECONE_API_KEY` for Pinecone, etc.

## Where to look in code

- Composed settings instance: `backend/app/config/settings.py` (`settings` instance at module bottom)
- App-level defaults & validators: `backend/app/config/app_settings.py`
- LLM logic & builders: `backend/app/config/llm_settings.py`
- Embedding logic: `backend/app/config/embedding_settings.py`
- Vector database config & validation: `backend/app/config/vectordb_settings.py`
- Database connection config: `backend/app/config/database_settings.py`
- Prompt defaults: `backend/app/config/prompt_settings.py`
- Email & FastMail config: `backend/app/config/email_settings.py`
- Cache settings: `backend/app/config/cache_settings.py`


## See Also
 
- [Installation Guide](INSTALLATION.md) - Setup instructions, `uv` usage, and seeder examples
- [Vector Stores Guide](VECTOR_STORES_GUIDE.md) - Vector database details and provider guidance
- [Fallback LLM Guide](FALLBACK_LLM_GUIDE.md) - Fallback LLM configuration and behavior
- [Exception Handling Guide](EXCEPTION_HANDLING_GUIDE.md) - Error handling patterns and examples
