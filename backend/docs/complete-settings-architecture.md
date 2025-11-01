# Complete Settings Architecture with Database Support

## Visual Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                      app/config/                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              settings.py (45 lines)                       │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │  class Settings(AppSettings,                       │ │ │
│  │  │                 LLMSettings,                        │ │ │
│  │  │                 EmbeddingSettings,                  │ │ │
│  │  │                 VectorDBSettings,                   │ │ │
│  │  │                 DatabaseSettings) ✨ NEW            │ │ │
│  │  │                                                      │ │ │
│  │  │  + validate_all()                                   │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
│          ┌───────────────┼───────────────┬──────────┬─────────┐│
│          │               │               │          │         ││
│  ┌───────▼────────┐ ┌───▼────────┐ ┌───▼────────┐ ┌─▼──────┐┌▼────────┐
│  │ app_settings   │ │llm_settings│ │embedding_  │ │vectordb││database_│
│  │ .py            │ │.py         │ │settings.py │ │_settings││settings │
│  │ (130 lines)    │ │(180 lines) │ │(130 lines) │ │.py     ││.py ✨   │
│  │                │ │            │ │            │ │(140    ││(240     │
│  │                │ │            │ │            │ │lines)  ││lines)   │
│  ├────────────────┤ ├────────────┤ ├────────────┤ ├────────┤├─────────┤
│  │ • App info     │ │ • OpenAI   │ │ • HF       │ │ • Chroma││• PostgreSQL
│  │ • Server       │ │ • Google   │ │ • OpenAI   │ │ • Qdrant││• MySQL  │
│  │ • RAG params   │ │ • HF       │ │ • Google   │ │ • Pinecone│• SQLite│
│  │ • Security     │ │ • Fallback │ │ • Cohere   │ │ • Weaviate│        │
│  │ • CORS         │ │            │ │ • Voyage   │ │ • Milvus││Pool:   │
│  │ • Logging      │ │ Methods:   │ │            │ │         ││• Size  │
│  │                │ │ • get_llm_ │ │ Methods:   │ │ Methods:││• SSL   │
│  │ Methods:       │ │   config() │ │ • get_     │ │ • get_  ││• Async │
│  │ • validate_    │ │ • get_     │ │   embedding│ │   vector││        │
│  │   rag_config() │ │   fallback │ │   _config()│ │   _db_  ││Methods:│
│  │                │ │   _llm_    │ │ • validate │ │   config││• get_  │
│  │                │ │   config() │ │   _config()│ │ • validate│ database│
│  │                │ │ • validate │ │            │ │   _config()│ _url()│
│  └────────────────┘ └────────────┘ └────────────┘ └─────────┘│• get_  │
│                                                               ││  async_│
│                                                               ││  url() │
│                                                               ││• get_  │
│                                                               ││  config│
│                                                               │└────────┘
└─────────────────────────────────────────────────────────────────┘
```

## Two-Database Architecture

RAG Fortress uses **TWO separate database systems**:

```
┌───────────────────────────────────────────────────────────────┐
│                    RAG FORTRESS                               │
└───────────────────────────────────────────────────────────────┘
                              │
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│    SQL Database          │    │    Vector Database       │
│  (Structured Data)       │    │  (Embeddings/Vectors)    │
├──────────────────────────┤    ├──────────────────────────┤
│ PURPOSE:                 │    │ PURPOSE:                 │
│ • User accounts          │    │ • Document embeddings    │
│ • Authentication         │    │ • Semantic search        │
│ • Chat history           │    │ • Similarity matching    │
│ • Document metadata      │    │ • RAG retrieval          │
│ • Application settings   │    │                          │
│                          │    │                          │
│ PROVIDERS:               │    │ PROVIDERS:               │
│ ✓ PostgreSQL (prod)      │    │ ✓ Qdrant (prod)          │
│ ✓ MySQL (prod)           │    │ ✓ Pinecone (cloud)       │
│ ✓ SQLite (dev)           │    │ ✓ Weaviate (open-src)    │
│                          │    │ ✓ Milvus (perf)          │
│                          │    │ ✓ Chroma (dev only)      │
│                          │    │                          │
│ CONFIGURED BY:           │    │ CONFIGURED BY:           │
│ DatabaseSettings         │    │ VectorDBSettings         │
│                          │    │                          │
│ ENV VAR:                 │    │ ENV VAR:                 │
│ DATABASE_PROVIDER        │    │ VECTOR_DB_PROVIDER       │
└──────────────────────────┘    └──────────────────────────┘
```

## Complete Module Breakdown

### Module Responsibilities

```
┌────────────────────────────────────────────────────────────┐
│ AppSettings (130 lines)                                    │
├────────────────────────────────────────────────────────────┤
│ General application configuration                          │
│ • APP_NAME, APP_VERSION, ENVIRONMENT                       │
│ • HOST, PORT                                               │
│ • CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS                 │
│ • SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES       │
│ • CORS_ORIGINS, CORS_CREDENTIALS                           │
│ • LOG_LEVEL, LOG_FORMAT, LOG_FILE                          │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ LLMSettings (180 lines)                                    │
├────────────────────────────────────────────────────────────┤
│ Language Model providers                                   │
│ • LLM_PROVIDER (openai/google/huggingface)                 │
│ • OpenAI: OPENAI_API_KEY, OPENAI_MODEL                     │
│ • Google: GOOGLE_API_KEY, GOOGLE_MODEL                     │
│ • HuggingFace: HF_API_TOKEN, HF_MODEL                      │
│ • Fallback: FALLBACK_LLM_PROVIDER, FALLBACK_LLM_MODEL      │
│                                                            │
│ Methods:                                                   │
│ • get_llm_config() → dict                                  │
│ • get_fallback_llm_config() → dict                         │
│ • validate_llm_config()                                    │
│ • validate_fallback_config()                               │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ EmbeddingSettings (130 lines)                              │
├────────────────────────────────────────────────────────────┤
│ Embedding providers (5 options)                            │
│ • EMBEDDING_PROVIDER (huggingface/openai/google/...)       │
│ • HuggingFace: HF_EMBEDDING_MODEL, HF_EMBEDDING_DEVICE     │
│ • OpenAI: OPENAI_EMBEDDING_MODEL                           │
│ • Google: GOOGLE_EMBEDDING_MODEL, GOOGLE_EMBEDDING_...     │
│ • Cohere: COHERE_API_KEY, COHERE_EMBEDDING_MODEL           │
│ • Voyage: VOYAGE_API_KEY, VOYAGE_EMBEDDING_MODEL           │
│                                                            │
│ Methods:                                                   │
│ • get_embedding_config() → dict                            │
│ • validate_config()                                        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ VectorDBSettings (140 lines)                               │
├────────────────────────────────────────────────────────────┤
│ Vector database providers (5 options)                      │
│ • VECTOR_DB_PROVIDER (chroma/qdrant/pinecone/...)          │
│ • Qdrant: QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY         │
│ • Chroma: CHROMA_HOST, CHROMA_PERSIST_DIRECTORY            │
│ • Pinecone: PINECONE_API_KEY, PINECONE_ENVIRONMENT         │
│ • Weaviate: WEAVIATE_URL, WEAVIATE_API_KEY                 │
│ • Milvus: MILVUS_HOST, MILVUS_PORT                         │
│                                                            │
│ Methods:                                                   │
│ • get_vector_db_config() → dict                            │
│ • validate_config(environment)                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ DatabaseSettings (240 lines) ✨ NEW                        │
├────────────────────────────────────────────────────────────┤
│ SQL database providers (3 options)                         │
│ • DATABASE_PROVIDER (postgresql/mysql/sqlite)              │
│ • PostgreSQL: POSTGRES_HOST, POSTGRES_USER, ...            │
│   - POSTGRES_SSL_MODE (6 modes)                            │
│   - Connection pooling                                     │
│ • MySQL: MYSQL_HOST, MYSQL_USER, MYSQL_CHARSET             │
│   - Connection pooling                                     │
│ • SQLite: SQLITE_PATH, SQLITE_CHECK_SAME_THREAD            │
│   - File-based, no pooling                                 │
│                                                            │
│ Pool Settings:                                             │
│ • DB_POOL_SIZE, DB_MAX_OVERFLOW                            │
│ • DB_POOL_TIMEOUT, DB_POOL_RECYCLE                         │
│ • DB_ECHO (query logging)                                  │
│                                                            │
│ Migration:                                                 │
│ • DB_AUTO_MIGRATE, DB_DROP_ALL                             │
│                                                            │
│ Methods:                                                   │
│ • get_database_url() → str                                 │
│ • get_async_database_url() → str                           │
│ • get_database_config() → dict                             │
│ • validate_config(environment)                             │
└────────────────────────────────────────────────────────────┘
```

## Provider Options Summary

### Total Provider Options: 15

| Category | Providers | Count |
|----------|-----------|-------|
| **LLM** | OpenAI, Google, HuggingFace (+ Fallback) | 3 + Fallback |
| **Embedding** | HuggingFace, OpenAI, Google, Cohere, Voyage | 5 |
| **Vector DB** | Chroma, Qdrant, Pinecone, Weaviate, Milvus | 5 |
| **SQL DB** | PostgreSQL, MySQL, SQLite ✨ | 3 |
| **Total** | | **16** |

## Configuration Flow

```
┌──────────────┐
│   .env file  │
└──────┬───────┘
       │
       │ Environment variables
       │
       ▼
┌─────────────────────────────────────────┐
│         Pydantic Settings               │
│  (automatic loading & validation)       │
└─────────────────────────────────────────┘
       │
       │ Composed via multiple inheritance
       │
       ▼
┌─────────────────────────────────────────┐
│           Settings Class                │
│                                         │
│  AppSettings                            │
│  + LLMSettings                          │
│  + EmbeddingSettings                    │
│  + VectorDBSettings                     │
│  + DatabaseSettings ✨                  │
└─────────────────────────────────────────┘
       │
       │ settings.validate_all()
       │
       ▼
┌─────────────────────────────────────────┐
│      Validated Configuration            │
│  Ready for application use              │
└─────────────────────────────────────────┘
```

## File Size Summary

| File | Lines | Purpose |
|------|-------|---------|
| `settings.py` | 45 | Main composition |
| `app_settings.py` | 130 | App configuration |
| `llm_settings.py` | 180 | LLM providers |
| `embedding_settings.py` | 130 | Embedding providers |
| `vectordb_settings.py` | 140 | Vector databases |
| `database_settings.py` ✨ | 240 | SQL databases |
| **Total** | **865** | **6 focused modules** |

## Benefits of Database Settings Addition

### 1. User Choice
```bash
# Startup? Use SQLite
DATABASE_PROVIDER=sqlite

# Small production? Use MySQL
DATABASE_PROVIDER=mysql

# Enterprise? Use PostgreSQL
DATABASE_PROVIDER=postgresql
```

### 2. Environment-Specific
```bash
# Development
DATABASE_PROVIDER=sqlite
SQLITE_PATH=./dev.db

# Staging
DATABASE_PROVIDER=postgresql
POSTGRES_HOST=staging-db.example.com

# Production
DATABASE_PROVIDER=postgresql
POSTGRES_HOST=prod-db.example.com
POSTGRES_SSL_MODE=require
```

### 3. Zero Code Changes
Switch databases by changing ONE environment variable!

### 4. Production Safety
- ❌ Blocks SQLite in production
- ❌ Blocks dangerous flags in production
- ✅ Requires passwords in production
- ✅ Validates all settings

## Usage Example

```python
from app.config import settings
from sqlalchemy import create_engine

# Works with any provider!
engine = create_engine(
    settings.get_database_url(),
    pool_size=settings.DB_POOL_SIZE,
    echo=settings.DB_ECHO,
)

# Or async
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    settings.get_async_database_url()
)
```

## Complete Settings Architecture Achievement

✅ **6 Modular Configuration Files**
✅ **16 Provider Options**
✅ **2 Database Systems** (SQL + Vector)
✅ **100% Backward Compatible**
✅ **Production-Ready Validation**
✅ **Comprehensive Documentation**
✅ **Maximum Flexibility**

**Philosophy**: "Give users options to choose whatever they want without being restricted to a single thing they may or may not be able to use" ✨
