# RAG Fortress – System Architecture

> **Version**: 1.1.0  
> **Last Updated**: January 2026  
> **Purpose**: Document the actual implementation, design decisions, and trade-offs in the RAG Fortress system

---

## 1. System Overview

### 1.1 What Problem the System Solves

RAG Fortress is a **security-aware, enterprise-grade Retrieval-Augmented Generation (RAG) platform** designed to solve:

1. **Access-Controlled Knowledge Retrieval**: Organizations need to provide AI-powered question answering while respecting document-level security clearances and departmental access restrictions.

2. **Provider-Agnostic AI Integration**: Avoid vendor lock-in by supporting multiple LLM providers (OpenAI, Google, Huggingface, etc.), embedding providers, and vector databases through abstraction layers.

3. **Configurable Query Processing**: Different use cases require different retrieval strategies - from simple keyword search to complex query decomposition with reranking.

4. **Production-Ready RAG**: Bridge the gap between proof-of-concept RAG systems and enterprise deployments with proper caching, error handling, observability, and performance optimization.

### 1.2 High-Level Capabilities

**Core Features** (implemented and active):

- **Retrieval-Augmented Generation**: Combines vector search with LLM generation for accurate, context-grounded responses
- **Multi-Level Security**: Document security levels (PUBLIC, GENERAL, CONFIDENTIAL, TOP_SECRET), departmental isolation, and user permission enforcement
- **Query Understanding**: Optional intent classification and query decomposition for complex questions
- **Reranking**: Optional cross-encoder reranking for improved relevance
- **Multi-Tier Caching**: Response cache, context cache, and semantic cache with Redis
- **Document Management**: File upload, approval workflow, processing pipeline, and vector indexing
- **Admin Dashboard**: User management, file approval, system monitoring, analytics
- **Hybrid Search**: Dense vector search with optional sparse (BM25) retrieval for supported providers

**Optional Components** (feature-flagged):

- Query decomposition (`ENABLE_DECOMPOSITION`)
- Reranking (`ENABLE_RERANKER`)
- Intent classification (`ENABLE_INTENT_CLASSIFIER`)
- Fallback LLM (`ENABLE_FALLBACK_LLM`)
- Hybrid search (`HYBRID_SEARCH` in vector DB settings)

---

## 2. Architectural Principles (Derived from Code)

### 2.1 Observed Design Patterns

#### **Optional by Default**
- **Evidence**: Nearly every advanced feature has an `ENABLE_*` flag
- **Pattern**: `if settings.app_settings.ENABLE_RERANKER: use_reranker() else: skip`
- **Rationale**: Allows gradual adoption and reduces external dependencies
- **Violations**: Database and cache are mandatory (will fail startup if unavailable)

#### **Fail Fast on Critical, Degrade Gracefully on Optional**
- **Critical** (startup failure): Database, Redis cache, vector store initialization
- **Optional** (runtime degradation): Reranker, decomposer, fallback LLM, email
- **Evidence**: See `app/core/startup.py` - optional components log warnings but don't block
- **Example**: Fallback LLM failing logs error but doesn't crash main LLM usage

#### **Provider Abstraction via Factory Pattern**
- **Factories**: `embedding_factory.py`, `llm_factory.py`, `vector_store_factory.py`, `reranker_factory.py`
- **Contract**: LangChain base classes (`Embeddings`, `BaseLLM`, `VectorStore`, `BaseRetriever`)
- **Runtime Selection**: Based on `*_PROVIDER` environment variables
- **Validation**: Startup checks for provider compatibility (e.g., hybrid search support)

#### **Singleton for Expensive Resources**
- **Global Instances**: Vector store, embeddings, LLM clients, cache managers
- **Pattern**: `_instance = None; if _instance is None: _instance = create(); return _instance`
- **Rationale**: Avoid re-initializing expensive connections (embeddings model loading, DB connections)
- **Risk**: Shared state across requests (mitigated by user-scoped filtering)

#### **Explicit Configuration Over Convention**
- **Evidence**: 11 separate settings files in `app/config/`
- **Pattern**: Pydantic BaseSettings with explicit Field() definitions
- **Validation**: Field validators, startup compatibility checks
- **Trade-off**: Verbose but explicit - no hidden defaults

#### **Event-Driven Background Processing**
- **Pattern**: Event bus (`app/core/events.py`) with handlers (`app/events/`, `app/handlers/`)
- **Use Cases**: Activity logging, semantic caching, notifications
- **Non-Blocking**: Handlers run asynchronously, don't block request lifecycle
- **Evidence**: `emit_event("context_cached", data)` in response pipeline

---

## 3. High-Level Component Breakdown

### 3.1 API / Entry Layer

**Location**: `app/main.py`, `app/routes/`

**Framework**: FastAPI with async support

**Request Lifecycle**:
```
Request → Middleware Stack → Route Handler → Service Layer → Core Components → Response
```

**Middleware** (`app/middleware/`):
- CORS handling
- Rate limiting (SlowAPI)
- Error logging
- Request context

**Routes** (`app/routes/`):
- `auth.py` - Authentication (JWT tokens, login, logout)
- `conversation.py` - Chat interactions
- `file_upload.py` - Document management
- `users.py` - User CRUD
- `admin.py` - Administrative functions
- `settings.py` - Dynamic settings management
- `diagnostics.py` - System health checks (hidden from Swagger)

**Startup Sequence**:
1. `lifespan()` context manager in `main.py`
2. Calls `StartupController.initialize()`
3. Initializes components in dependency order (database → cache → embeddings → vector store → LLM)
4. Registers exception handlers
5. Starts job scheduler

**Shutdown**:
- Closes database connections
- Shuts down job scheduler
- Flushes logs

### 3.2 Configuration & Settings

**Location**: `app/config/`

**Architecture**: Modular settings files, unified access via `settings.py`

**Settings Hierarchy**:

```
settings.py (root)
├── app_settings.py         (general app config, feature flags)
├── database_settings.py    (PostgreSQL connection)
├── cache_settings.py       (Redis configuration)
├── vectordb_settings.py    (vector store provider & config)
├── embedding_settings.py   (embedding provider & model)
├── llm_settings.py         (primary LLM configuration)
├── reranker_settings.py    (reranker model settings)
├── email_settings.py       (SMTP configuration)
├── prompt_settings.py      (system prompts)
└── response_templates.py   (error messages)
```

**Loading Strategy**:
- **Startup**: Environment variables → Pydantic validation → In-memory settings objects
- **Runtime**: Database-backed settings override defaults (see `settings_loader.py`)
- **Hot Reload**: Settings cached in Redis with TTL, invalidation on update

**Validation**:
- Pydantic field validators (type checking, value ranges)
- Custom validators (e.g., URL format, file paths)
- Startup compatibility checks (e.g., hybrid search + unsupported provider = warning)

**Encryption**:
- Sensitive settings encrypted in database (using Fernet + HKDF key derivation)
- Master key: `MASTER_ENCRYPTION_KEY` environment variable
- Purpose-specific keys derived via HKDF

**Single Source of Truth**:
- Environment variables are the ultimate source
- Database settings provide per-category overrides
- In-memory cache for performance

---

## 4. Request Lifecycle Analysis

### 4.1 End-to-End Chat Request Flow

**Entry**: `POST /api/v1/conversation/chat`

```
1. Route Handler (app/routes/conversation.py)
   ├─ Validate request (ConversationRequest schema)
   ├─ Extract user from JWT token
   ├─ Rate limit check (per-user limits)
   └─ Call ConversationService.chat()

2. Conversation Service (app/services/conversation/service.py)
   ├─ Load conversation history from DB
   ├─ Validate message count limits
   ├─ Intent classification (optional)
   │  └─ IntentClassifier.classify() → "rag" | "chat" | "greeting"
   │
   ├─ IF intent == "rag":
   │  └─ Call response_service.generate_rag_response()
   │
   ├─ ELSE:
   │  └─ Call llm_provider.generate_chat_response()
   │
   └─ Save to database, emit events, return response

3. RAG Response Service (app/services/conversation/response_service.py)
   ├─ Query decomposition (optional)
   │  └─ QueryDecomposer → List[sub_queries] or single query
   │
   ├─ FOR EACH query:
   │  ├─ Check context cache (Redis)
   │  │  ├─ HIT: Return cached context text + metadata
   │  │  └─ MISS: Proceed to retrieval
   │  │
   │  ├─ Retrieval Coordinator (retrieval_coordinator.py)
   │  │  ├─ Vector search (RetrieverService)
   │  │  │  ├─ Embedding generation
   │  │  │  ├─ Similarity search (k=TOP_K, hybrid optional)
   │  │  │  └─ Return documents with scores
   │  │  │
   │  │  ├─ Security Filtering (app/services/permission_service.py)
   │  │  │  ├─ Get user permissions from DB
   │  │  │  ├─ Filter by security_level
   │  │  │  ├─ Filter by department (if is_department_only=True)
   │  │  │  └─ Track blocked_count for partial access scenarios
   │  │  │
   │  │  ├─ Quality Filtering (retriever.py)
   │  │  │  └─ Drop docs below RETRIEVAL_SCORE_THRESHOLD (default 0.5)
   │  │  │
   │  │  └─ Reranking (optional, if ENABLE_RERANKER)
   │  │     ├─ Cross-encoder scoring
   │  │     ├─ Filter by RERANKER_SCORE_THRESHOLD
   │  │     └─ Re-sort by reranker scores
   │  │
   │  └─ Emit context cache event (background)
   │
   ├─ Aggregate contexts (if decomposed)
   ├─ Check response cache (semantic cache using RedisVL)
   │  ├─ Compute query embedding
   │  ├─ Vector similarity search in cache
   │  ├─ HIT: Return cached response
   │  └─ MISS: Proceed to generation
   │
   └─ LLM Generation Pipeline (response/pipeline.py)
      ├─ Build prompt (context + query + history)
      ├─ Streaming or non-streaming mode
      ├─ Primary LLM call
      ├─ ON ERROR: Fallback LLM (if enabled)
      ├─ Emit response cache event (background)
      └─ Return response

4. Response Formatting
   ├─ Add metadata (sources, security info)
   ├─ Log activity (event bus → ActivityLogHandler)
   └─ Return JSON or SSE stream

5. Background Events (non-blocking)
   ├─ Context caching (formats documents, extracts metadata, stores in Redis)
   ├─ Response caching (validates length, stores in semantic cache)
   ├─ Activity logging (writes to activity_logs table)
   └─ Notifications (if configured)
```

**Early Exit Scenarios**:

- **No permission**: Returns empty context, LLM uses general knowledge
- **Cached context**: Skips retrieval entirely
- **Cached response**: Skips retrieval + generation
- **Intent = greeting**: Bypasses RAG, direct LLM response
- **Empty query**: Validation error at route level

**Optional Steps** (skipped if disabled):

- Intent classification → Always "rag" if disabled
- Query decomposition → Single query if disabled
- Reranking → Uses retrieval scores only if disabled
- Fallback LLM → Error if primary fails and no fallback

---

## 5. Query Understanding Layer

### 5.1 Intent Classifier

**Location**: `app/services/llm/intent_classifier.py`

**Purpose**: Route queries to appropriate handler (RAG vs chat vs greeting)

**Types Implemented**:

1. **Heuristic Classifier** (`SimpleIntentClassifier`)
   - Regex patterns for greetings ("hi", "hello", "hey")
   - Keyword matching for RAG triggers ("document", "file", "show me")
   - Default: "chat" for general conversation
   - **Fast**, no LLM call required
   - Configured via `CLASSIFIER_TYPE=simple`

2. **LLM-Based Classifier** (`LLMIntentClassifier`)
   - Calls dedicated classifier LLM (can be different model than main LLM)
   - Structured output with categories
   - More accurate but slower and costs API calls
   - Configured via `CLASSIFIER_TYPE=llm`

**Configuration**:
```python
ENABLE_INTENT_CLASSIFIER = True/False  # Feature toggle
CLASSIFIER_TYPE = "simple" | "llm"     # Which implementation
CLASSIFIER_LLM_PROVIDER = "openai"     # Provider for LLM classifier
CLASSIFIER_MODEL = "gpt-4o-mini"       # Model for LLM classifier
```

**Fallback Logic**:
- If classifier fails → defaults to "rag" (safer to over-retrieve than miss)
- Logged but doesn't crash request

**Trade-offs**:
- **Simple**: Fast, deterministic, but misses nuanced queries
- **LLM**: Accurate, adaptable, but adds latency and cost
- **Disabled**: Everything is "rag", wastes retrieval on non-knowledge queries

### 5.2 Query Decomposer

**Location**: `app/services/conversation/response/query_decomposer.py`

**Trigger**: Multi-part or complex queries that benefit from sub-query splitting

**Implementation**:
- LLM-based decomposition using structured output
- Prompt instructs LLM to split "What are the core values and mission statement?" into ["What are the core values?", "What is the mission statement?"]
- Returns `DecompositionResult` with `decomposed_queries` list

**When Used**:
```python
if settings.app_settings.ENABLE_DECOMPOSITION:
    result = await decomposer.decompose(query)
    sub_queries = result.decomposed_queries
else:
    sub_queries = [query]  # No decomposition
```

**Retrieval Strategy**:
- Each sub-query retrieves separately
- Results aggregated before reranking (if enabled)
- Context from all sub-queries merged

**Failure Handling**:
- If decomposition fails → falls back to original query
- Logged but doesn't fail request
- `use_fallback=True` flag in result

**Output Format**:
```python
{
    "decomposed_queries": ["sub query 1", "sub query 2"],
    "use_fallback": False,  # True if decomposition failed
    "original_query": "..."
}
```

**Edge Cases**:
- Single-part queries → Returns [original_query]
- Decomposition returns empty list → Falls back to [original_query]
- Decomposer enabled but LLM call fails → Falls back

---

## 6. Retrieval Layer

### 6.1 Vector Store Abstraction

**Location**: `app/core/vector_store_factory.py`

**Pattern**: Factory + Singleton

**Supported Providers**:
```python
SUPPORTED_PROVIDERS = {
    "qdrant":   # Dense + sparse vectors, hybrid search
    "weaviate", # BM25F hybrid search
    "milvus",   # Sparse vector support
    "chroma",   # Dense only
    "faiss",    # Dense only, local storage
}
```

**Interface Contract**: LangChain `VectorStore` and `BaseRetriever`

**Provider Selection**:
```python
VECTOR_DB_PROVIDER = "qdrant"  # Environment variable
vector_store = get_vector_store()  # Returns provider-specific instance
retriever = get_retriever()        # Wraps vector store as retriever
```

**Capability Detection**:

```python
# Hybrid search validation
hybrid_supported = {"qdrant", "weaviate", "milvus"}
if settings.vectordb_settings.hybrid_search:
    if provider not in hybrid_supported:
        logger.warning(f"{provider} doesn't support hybrid search, falling back to dense only")
```

**Startup Validation**:
- Checks provider availability (imports, dependencies)
- Validates connection parameters
- Tests basic operations (add/search)
- **Fails startup** if vector store unavailable (critical component)

**Configuration Per Provider**:

**Qdrant**:
```python
{
    "provider": "qdrant",
    "url": "http://localhost:6333",
    "collection_name": "documents",
    "hybrid_search": True,  # Enable BM25 sparse vectors
    "api_key": "..."
}
```

**FAISS** (local):
```python
{
    "provider": "faiss",
    "index_path": "./data/vector_store/faiss_index",
    "save_local": True
}
```

**Singleton Pattern**:
```python
_vector_store_instance = None
_retriever_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = _create_vector_store(...)
    return _vector_store_instance
```

### 6.2 Search Strategies

**Dense Vector Search** (always enabled):
- Query → Embedding → Cosine similarity search
- Top-K results based on `TOP_K` setting (default 10)
- Scores normalized 0.0-1.0

**Hybrid Search** (optional):
- **Dense + Sparse**: Vector similarity + keyword matching (BM25)
- Reciprocal Rank Fusion (RRF) to combine scores
- Configured via `hybrid_search: true` in vector DB settings
- **Provider-dependent**: Only Qdrant, Weaviate, Milvus support

**Fallback Behavior**:
```python
if hybrid_search_enabled and provider_supports_hybrid:
    results = vector_store.hybrid_search(query, k=TOP_K)
else:
    logger.info("Using dense-only search")
    results = vector_store.similarity_search(query, k=TOP_K)
```

**Score Filtering**:
- `RETRIEVAL_SCORE_THRESHOLD = 0.5` (default)
- Documents below threshold are dropped
- Prevents low-quality matches from contaminating context

**Metadata Filtering** (ACL enforcement):
```python
# Applied at search time
filter = {
    "security_level": {"$lte": user_max_level},
    "department_id": {"$in": user_departments} if is_department_only
}
results = vector_store.similarity_search(query, filter=filter)
```

---

## 7. Security Model

### 7.1 Access Control Mechanisms

**Hierarchy**: 4-level clearance system

```python
class PermissionLevel(IntEnum):
  GENERAL = 1                     # Open company-wide
  RESTRICTED = 2                  # Managerial data access
  CONFIDENTIAL = 3                # Confidential information
  HIGHLY_CONFIDENTIAL = 4         # Sensitive management access
```

**Document-Level Security**:
- Each document chunk has `security_level` metadata
- Stored in vector store metadata
- User has `max_permission_level` in database

**Enforcement Points**:

1. **Vector Store Metadata Filtering** (primary):
   - Filter applied at search time
   - `WHERE security_level <= user_max_level`
   - Most efficient, reduces retrieved document count

2. **Post-Retrieval Filtering** (secondary):
   - In `PermissionService.filter_by_user_permissions()`
   - Double-check in case metadata filtering unavailable
   - Handles edge cases (outdated metadata, manual edits)

3. **Departmental Isolation**:
   - Documents marked `is_department_only=True`
   - User must be member of `department_id`
   - Enforced via `department_id IN user.departments`

**Code Location**: `app/services/permission_service.py`

```python
async def filter_by_user_permissions(user_id, documents):
    user = await get_user_with_permissions(user_id)
    
    filtered = []
    blocked_count = 0
    
    for doc in documents:
        doc_level = doc.metadata.get("security_level", 0)
        
        # Security level check
        if doc_level > user.max_permission_level:
            blocked_count += 1
            continue
        
        # Department check
        if doc.metadata.get("is_department_only"):
            if doc.metadata.get("department_id") not in user.departments:
                blocked_count += 1
                continue
        
        filtered.append(doc)
    
    return filtered, blocked_count
```

### 7.2 Partial Context Handling

**Scenario**: User queries "company policies" but lacks access to some policy documents

**Tracking**:
```python
{
    "documents_retrieved": 10,
    "documents_accessible": 6,
    "documents_blocked": 4,  # Tracked for transparency
    "context_incomplete": True  # Flag for LLM prompt
}
```

**LLM Prompt Adjustment**:
```python
if context_incomplete:
    prompt += """
    Note: Some relevant documents were not accessible due to security restrictions.
    Base your answer only on the provided context. If the context is insufficient,
    acknowledge the limitation.
    """
```

**User Notification**:
- Response metadata includes `blocked_document_count`
- Frontend can display warning: "Some results restricted due to permissions"

**Distinction**:
- **No data**: No documents in vector store matching query
- **Irrelevant data**: Documents exist but low similarity scores
- **Inaccessible data**: Documents exist and relevant but user lacks clearance

**Security Logging**:
- Access denials logged to `activity_logs` table
- Includes user_id, document_id, reason (security_level or department)
- Auditable for compliance

---

## 8. Reranking Layer

**Location**: `app/services/vector_store/reranker.py`, `app/core/reranker_factory.py`

**Purpose**: Improve relevance ranking using cross-encoder models

**When Applied**:
```python
if settings.app_settings.ENABLE_RERANKER:
    reranked_docs = reranker.rerank(query, documents)
else:
    reranked_docs = documents  # Use retrieval scores as-is
```

**Dependency**:
- Requires `ENABLE_RERANKER=True`
- Configured via `reranker_settings.py`
- Supports multiple providers (Cohere, HuggingFace, Jina)

**Supported Providers**:
```python
{
    "cohere": CohereRerank (API-based),
    "huggingface": CrossEncoderReranker (local model),
    "jina": JinaRerank (API-based)
}
```

**Reranking Process**:
1. Retrieval returns top-K documents (e.g., 10)
2. Reranker scores all pairs (query, doc)
3. Re-sort by reranker scores
4. Filter by `RERANKER_SCORE_THRESHOLD` (default 0.5)
5. Return top-N (e.g., 5)

**Scoring**:
- Reranker scores are typically 0.0-1.0
- Replaces original similarity scores
- Stored in `metadata['reranker_score']`

**Configuration**:
```python
RERANKER_PROVIDER = "cohere"
RERANKER_MODEL = "rerank-english-v3.0"
RERANKER_SCORE_THRESHOLD = 0.5
RERANKER_TOP_N = 5  # Return top 5 after reranking
```

**Interaction with Query Decomposition**:
- If decomposition enabled → retrieve separately, then aggregate before reranking
- Reranker sees combined document pool from all sub-queries
- Prevents duplicate documents (uses document ID deduplication)

**Interaction with Security Filtering**:
- Security filtering happens **before** reranking
- Reranker only sees accessible documents
- Ensures no security leaks via reranker scores

**Known Edge Cases**:

1. **Empty Results After Filtering**:
   ```python
   if not accessible_docs:
       logger.info("No documents passed security filtering, skipping reranking")
       return []
   ```

2. **Reranker Failure**:
   ```python
   try:
       reranked = reranker.rerank(query, docs)
   except Exception as e:
       logger.error(f"Reranking failed: {e}, using retrieval scores")
       return docs  # Fallback to original order
   ```

3. **All Documents Below Threshold**:
   - Returns empty list
   - LLM receives "no relevant context" signal

**Performance Trade-offs**:
- **Accuracy**: Significant improvement for complex queries (10-20% better in tests)
- **Latency**: Adds 100-500ms depending on provider and document count
- **Cost**: API-based rerankers (Cohere, Jina) charge per request

---

## 9. Generation Layer

### 9.1 Primary LLM Configuration

**Location**: `app/core/llm_factory.py`, `app/config/llm_settings.py`

**Architecture**: Unified configuration supporting multiple providers

**Supported Providers**:
```python
{
    "openai": ChatOpenAI,
    "anthropic": ChatAnthropic,
    "google": ChatGoogleGenerativeAI,
    "groq": ChatGroq,
    "ollama": ChatOllama,  # Local models
    "bedrock": BedrockChat  # AWS
}
```

**Configuration Structure**:
```python
{
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 2000,
    "streaming": True,  # SSE streaming for real-time responses
    "api_key": "...",
    "base_url": None,  # Optional for custom endpoints
    "timeout": 60
}
```

**Model Selection Logic**:
```python
# Primary LLM for generation
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o"

# Classifier (can be different/cheaper model)
CLASSIFIER_LLM_PROVIDER = "openai"
CLASSIFIER_MODEL = "gpt-4o-mini"

# Internal operations (decomposition, validation)
INTERNAL_LLM_PROVIDER = "openai"
INTERNAL_LLM_MODEL = "gpt-4o-mini"
```

**Streaming Support**:
```python
if settings.llm_settings.streaming:
    async for chunk in llm_provider.stream(prompt):
        yield chunk  # Server-Sent Events to frontend
else:
    response = await llm_provider.generate(prompt)
    return response
```

**Prompt Construction**:
```python
# System prompt
system = settings.prompt_settings.SYSTEM_PROMPT

# Context injection
context = "\n\n".join([doc.page_content for doc in documents])

# Final prompt
prompt = f"{system}\n\nContext:\n{context}\n\nQuestion: {query}"
```

### 9.2 Fallback LLM

**Purpose**: Automatic failover if primary LLM is unavailable

**Configuration**:
```python
ENABLE_FALLBACK_LLM = True
FALLBACK_LLM_PROVIDER = "groq"  # Often a faster/cheaper alternative
FALLBACK_LLM_MODEL = "llama-3.1-70b"
```

**Trigger Scenarios**:
1. Primary LLM API error (timeout, 500, rate limit)
2. Primary LLM returns empty response
3. Primary LLM throws exception

**Fallback Logic**:
```python
try:
    response = await primary_llm.generate(prompt)
    if response.strip():
        return response
except Exception as e:
    logger.error(f"Primary LLM failed: {e}")
    
    if settings.app_settings.ENABLE_FALLBACK_LLM:
        logger.info("Attempting fallback LLM")
        try:
            response = await fallback_llm.generate(prompt)
            metadata["used_fallback"] = True
            return response
        except Exception as fallback_error:
            logger.error(f"Fallback LLM also failed: {fallback_error}")
            raise
    else:
        raise  # No fallback, propagate error
```

**Dependency on Configuration**:
- Fallback LLM **must** be configured if `ENABLE_FALLBACK_LLM=True`
- Startup validation checks fallback provider availability
- Warning logged if fallback enabled but not properly configured

**Failure Handling**:
- Both LLMs fail → Returns error to user
- Logged with full context for debugging
- Activity log records LLM failures

**Trade-offs**:
- **Reliability**: Reduces downtime from single provider outages
- **Complexity**: Another LLM to configure and monitor
- **Cost**: Potential surprise costs if fallback is expensive model
- **Consistency**: Fallback may produce different quality responses

---

## 10. Caching & Performance Optimization

### 10.1 Cache Types

RAG Fortress implements **three distinct cache layers**:

#### **1. Response Cache (Semantic Cache)**

**Location**: `app/core/semantic_cache.py` (uses RedisVL)

**Purpose**: Cache complete LLM responses for similar queries

**Technology**: Vector similarity search in Redis using RedisVL

**How It Works**:
```python
# Store
query_embedding = embed(query)
cache_key = hash(query_embedding)
redis_vl.set(cache_key, {
    "response": llm_response,
    "query_text": query,
    "embedding": query_embedding,
    "metadata": {...}
}, ttl=3600)

# Retrieve
query_embedding = embed(new_query)
similar_cached = redis_vl.vector_search(query_embedding, similarity_threshold=0.95)
if similar_cached:
    return similar_cached["response"]  # Cache hit
```

**Similarity Threshold**: 0.95 (configurable)
- Queries must be very similar to match
- Prevents false positives (wrong cached answer)

**TTL**: 1 hour (default)
- Stale responses automatically purged
- Configurable via `SEMANTIC_CACHE_TTL`

**Validation** (before caching):
```python
# Don't cache if:
if len(response) < 20:  # Too short
    return
if "I don't know" in response.lower():  # Generic negative
    return
if "cannot answer" in response.lower():
    return
# Only cache substantive responses
```

**Trade-offs**:
- **Pros**: Avoids expensive LLM calls for common questions
- **Cons**: Stale data if documents updated, requires embedding computation
- **Risk**: User A's response visible to User B if query identical (see security note)

#### **2. Context Cache**

**Location**: Background event handler in `app/events/semantic_cache_event.py`

**Purpose**: Cache formatted context text to skip retrieval

**Storage**: Redis key-value

**How It Works**:
```python
# Key generation
cache_key = f"context:{hash(query)}:{user_id}:{max_level}:{department_ids}"

# Store (in background event handler)
context_text = "\n\n".join([doc.page_content for doc in documents])
metadata = {
    "source_count": len(documents),
    "min_security_level": max([doc.metadata["security_level"] for doc in documents]),
    "is_departmental": any([doc.metadata.get("is_department_only") for doc in documents]),
    "department_ids": list(set([doc.metadata.get("department_id") for doc in documents]))
}
redis.set(cache_key, {
    "context_text": context_text,
    **metadata
}, ttl=1800)

# Retrieve (in response_service)
cached = redis.get(cache_key)
if cached:
    return cached["context_text"]  # Skip retrieval
```

**Key Composition**:
- Includes `user_id` for security isolation
- Includes `max_level` and `department_ids` to prevent privilege escalation
- Hash of query for deterministic lookup

**TTL**: 30 minutes (default)
- Balances freshness vs cache hit rate
- Shorter than response cache (context changes more frequently)

**Security Design**:
- User-scoped keys prevent cross-user leaks
- Permission metadata validated on retrieval

**Emission** (non-blocking):
```python
# In retrieval pipeline
emit_event("context_cached", {
    "query": query,
    "user_id": user_id,
    "documents": documents
})
# Request continues immediately, caching happens in background
```

#### **3. Settings Cache**

**Location**: `app/core/settings_cache.py`

**Purpose**: Cache database-backed settings to avoid repeated DB queries

**Storage**: Redis hash

**How It Works**:
```python
# Load from DB, cache in Redis
settings = await load_settings_from_db(category="llm")
redis.hset("settings:llm", {
    "provider": settings.provider,
    "model": settings.model,
    ...
}, ttl=300)  # 5 minutes

# Retrieve
cached = redis.hget("settings:llm")
if cached:
    return cached  # Skip DB query
```

**Invalidation**:
- Manual: When settings updated via admin UI
- Automatic: TTL expiration (5 minutes)

**Encryption**:
- Sensitive settings (API keys) encrypted before caching
- Decrypted on retrieval

### 10.2 Cache Storage

**Backend**: Redis

**Configuration**:
```python
CACHE_BACKEND = "redis"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = "..."
```

**Connection Pooling**:
```python
pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=50
)
client = redis.Redis(connection_pool=pool)
```

**TTL Strategy**:
- Response cache: 1 hour (queries change slowly)
- Context cache: 30 minutes (documents update more frequently)
- Settings cache: 5 minutes (balance DB load vs freshness)

**Encryption** (optional):
```python
ENCRYPT_CACHE = True  # Encrypt sensitive cached data
CACHE_ENCRYPTION_KEY = "..."  # Derived from master key
```

**Key Namespacing**:
```
rag_fortress:response:{hash}
rag_fortress:context:{hash}:{user_id}
rag_fortress:settings:{category}
rag_fortress:diagnostic:test:{timestamp}
```

**Eviction Policy**: `allkeys-lru` (least recently used)

**Monitoring**:
- Cache hit rate logged periodically
- Miss reasons tracked (no key, expired, similarity threshold)

### 10.3 Cache Safety

**Security Risks**:

1. **Cross-User Data Leakage** (Response Cache):
   - **Risk**: User A's cached response returned to User B for identical query
   - **Mitigation**: Queries with same text but different user permissions should NOT share cache
   - **Current State**: Response cache is NOT user-scoped (KNOWN LIMITATION)
   - **Warning**: Documented in CACHING_GUIDE.md, not suitable for multi-tenant strict isolation

2. **Privilege Escalation** (Context Cache):
   - **Risk**: User gains access to restricted documents via cached context
   - **Mitigation**: Cache key includes `user_id`, `max_level`, `department_ids`
   - **Validation**: Metadata checked on retrieval to ensure user still has access

3. **Stale Data**:
   - **Risk**: Cached response outdated after document update
   - **Mitigation**: Short TTLs, manual invalidation on document changes
   - **Trade-off**: Lower TTL = less cache hits but fresher data

**Safeguards**:

1. **User Isolation** (Context Cache):
   ```python
   cache_key = f"context:{query_hash}:{user_id}:{permissions_hash}"
   # Different users → different keys, even for same query
   ```

2. **Metadata Validation**:
   ```python
   cached_context = get_from_cache(key)
   if cached_context["min_security_level"] > user.max_level:
       # User's permissions changed, invalidate cache
       delete_from_cache(key)
       return None
   ```

3. **Explicit Warnings**:
   - `CACHING_GUIDE.md` explicitly warns about response cache cross-user risk
   - Recommends disabling semantic cache for high-security deployments

**Profile Interaction**:
- User permission changes → Context cache keys change (new permissions hash)
- Old cached contexts with old permissions become inaccessible
- No explicit invalidation needed (TTL handles cleanup)

**Encryption**:
```python
# Cache encryption (optional)
if settings.cache_settings.ENCRYPT_CACHE:
    encrypted = encrypt(data, key=derived_cache_key)
    redis.set(key, encrypted)
else:
    redis.set(key, data)
```

---

## 11. Data Security & Encryption

### 11.1 Encryption Scope

**What is Encrypted**:

1. **Database** (column-level):
   - Conversation messages (`messages.content`)
   - User API keys (`users.api_keys`)
   - Dynamic settings (`settings.encrypted_value`)
   - File metadata sensitive fields

2. **Cache** (optional):
   - Cached responses (if `ENCRYPT_CACHE=True`)
   - Cached contexts
   - NOT encrypted by default (performance trade-off)

3. **Settings** (database-backed):
   - LLM API keys
   - Embedding provider keys
   - Email credentials
   - Any setting marked `is_encrypted=True`

**What is NOT Encrypted**:

1. **Vector Store**:
   - Document chunks stored in plain text
   - Rationale: Vector databases need text for similarity search
   - Security: Access control via metadata filtering

2. **Logs**:
   - Application logs sanitized but not encrypted
   - Sensitive data (API keys, tokens) redacted via `log_sanitizer.py`

3. **Database Metadata**:
   - User emails, names, roles
   - File names, upload timestamps
   - Security levels (needed for queries)

### 11.2 Key Management

**Architecture**: HKDF (HMAC-based Key Derivation Function)

**Master Key**:
```python
MASTER_ENCRYPTION_KEY = "base64-encoded-32-byte-key"
```

**Purpose-Specific Keys Derived**:
```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def derive_key(master_key: bytes, purpose: str) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=purpose.encode()
    )
    return hkdf.derive(master_key)

# Usage
conversation_key = derive_key(MASTER_ENCRYPTION_KEY, "conversations")
settings_key = derive_key(MASTER_ENCRYPTION_KEY, "settings")
cache_key = derive_key(MASTER_ENCRYPTION_KEY, "cache")
```

**Benefits**:
- Single master key to manage
- Purpose-specific keys limit blast radius if one is compromised
- No need to store derived keys (deterministically regenerated)

**Encryption Algorithm**: Fernet (symmetric encryption)
```python
from cryptography.fernet import Fernet

cipher = Fernet(derived_key)
encrypted = cipher.encrypt(plaintext.encode())
decrypted = cipher.decrypt(encrypted).decode()
```

**Key Storage**:
- Master key: Environment variable (`MASTER_ENCRYPTION_KEY`)
- **NEVER** committed to git
- Rotated via environment update + database re-encryption script

**Rotation Considerations**:

- **Current**: No built-in rotation mechanism
- **Manual Process**:
  1. Generate new master key
  2. Decrypt all data with old key
  3. Re-encrypt with new key
  4. Update environment variable
  5. Restart application

- **Trade-off**: Simple but manual, suitable for current scale
- **Future**: Automated rotation with key versioning

**Legacy Support**:
```python
# Backward compatibility
SETTINGS_ENCRYPTION_KEY = "..."  # Legacy key for settings only
if MASTER_ENCRYPTION_KEY:
    use_hkdf_derived_keys()
else:
    use_legacy_single_key()  # Fallback
```

---

## 12. Startup Validation & Failure Modes

**Location**: `app/core/startup.py`

### 12.1 Startup Sequence

**Order** (dependency-driven):

```
1. Database (CRITICAL - blocks startup if unavailable)
   ├─ Connection pool creation
   ├─ Schema validation (tables exist)
   └─ Migration check (warns if out of sync)

2. Cache (CRITICAL - blocks startup if unavailable)
   ├─ Redis connection test
   ├─ RedisVL module check (for semantic cache)
   └─ Connection pool creation

3. Settings (CRITICAL - blocks if encryption keys missing)
   ├─ Load environment variables
   ├─ Validate encryption keys
   └─ Load database-backed settings

4. Event Bus (CRITICAL - required for async operations)
   ├─ Initialize event bus
   └─ Register event handlers

5. Embeddings (CRITICAL - required for vector operations)
   ├─ Load embedding provider
   ├─ Validate API key (if cloud provider)
   ├─ Test embedding generation
   └─ Measure embedding dimensions

6. Vector Store (CRITICAL - core RAG functionality)
   ├─ Initialize provider-specific client
   ├─ Test connection
   ├─ Validate collection/index exists
   └─ Create retriever instance

7. LLM Provider (CRITICAL - required for generation)
   ├─ Initialize primary LLM
   ├─ Validate API key
   └─ Test simple generation call

8. Fallback LLM (OPTIONAL - warn if enabled but unavailable)
   ├─ Initialize if ENABLE_FALLBACK_LLM=True
   └─ Warn if fails (doesn't block startup)

9. Classifier LLM (OPTIONAL - warn if enabled but unavailable)
   ├─ Initialize if ENABLE_INTENT_CLASSIFIER=True and type=llm
   └─ Fallback to simple classifier if fails

10. Reranker (OPTIONAL - warn if enabled but unavailable)
    ├─ Initialize if ENABLE_RERANKER=True
    └─ Warn if fails (reranking disabled at runtime)

11. Email Client (OPTIONAL - warn if unavailable)
    ├─ Initialize SMTP connection
    └─ Warn if fails (email features disabled)

12. Job Scheduler (CRITICAL - required for background tasks)
    ├─ Initialize APScheduler
    ├─ Register jobs
    └─ Start scheduler
```

### 12.2 What Causes Startup Failure

**CRITICAL Failures** (application won't start):

1. Database unavailable
   ```python
   try:
       await database.connect()
   except Exception as e:
       logger.critical(f"Database connection failed: {e}")
       raise  # Kills startup
   ```

2. Redis cache unavailable
   ```python
   if not await cache.ping():
       raise RuntimeError("Cache not available")
   ```

3. Missing encryption keys
   ```python
   if not settings.app_settings.MASTER_ENCRYPTION_KEY:
       raise ValueError("MASTER_ENCRYPTION_KEY required")
   ```

4. Vector store initialization failed
   ```python
   try:
       vector_store = get_vector_store()
       await vector_store.test_connection()
   except Exception as e:
       logger.critical("Vector store unavailable")
       raise
   ```

5. Primary LLM provider failed
   ```python
   try:
       llm = get_llm_provider()
       await llm.test_generate("test")
   except Exception as e:
       logger.critical("LLM provider unavailable")
       raise
   ```

### 12.3 What Only Triggers Warnings

**NON-CRITICAL Warnings** (application starts with degraded functionality):

1. Fallback LLM unavailable
   ```python
   if settings.app_settings.ENABLE_FALLBACK_LLM:
       try:
           fallback_llm = get_fallback_llm_provider()
       except Exception as e:
           logger.warning(f"Fallback LLM disabled: {e}")
           # Continue startup
   ```

2. Reranker unavailable
   ```python
   if settings.app_settings.ENABLE_RERANKER:
       try:
           reranker = get_reranker()
       except Exception as e:
           logger.warning("Reranker disabled, using retrieval scores")
   ```

3. Email client failed
   ```python
   try:
       email_client = init_email_client()
   except Exception as e:
       logger.warning("Email disabled, notifications unavailable")
   ```

4. Hybrid search on unsupported provider
   ```python
   if hybrid_search_enabled and provider not in hybrid_supported:
       logger.warning(f"{provider} doesn't support hybrid search, falling back to dense")
       # Continues with dense-only search
   ```

5. Semantic cache (RedisVL) unavailable
   ```python
   try:
       verify_redis_vl_support()
   except ImportError:
       logger.warning("RedisVL not available, semantic cache disabled")
       # Response cache disabled, context cache still works
   ```

### 12.4 Feature Compatibility Checks

**Hybrid Search Validation**:
```python
hybrid_supported = {"qdrant", "weaviate", "milvus"}
if settings.vectordb_settings.hybrid_search:
    if settings.vectordb_settings.provider not in hybrid_supported:
        logger.warning(
            f"Hybrid search not supported by {provider}, "
            f"falling back to dense vector search only"
        )
        settings.vectordb_settings.hybrid_search = False
```

**Reranker Dependencies**:
```python
if settings.app_settings.ENABLE_RERANKER:
    required_packages = {
        "cohere": "cohere",
        "huggingface": "sentence-transformers",
        "jina": "jina"
    }
    provider = settings.reranker_settings.provider
    if not is_package_installed(required_packages[provider]):
        logger.warning(f"Reranker package {required_packages[provider]} not installed")
        settings.app_settings.ENABLE_RERANKER = False
```

**Embedding Dimension Mismatch**:
```python
embedding_dim = len(get_embedding_provider().embed_query("test"))
vector_store_dim = vector_store.get_dimension()

if embedding_dim != vector_store_dim:
    raise ValueError(
        f"Embedding dimension ({embedding_dim}) doesn't match "
        f"vector store ({vector_store_dim}). Rebuild index required."
    )
```

### 12.5 Rationale Inferred from Code

**Why Database is CRITICAL**:
- User authentication requires database
- Conversation history stored in database
- File metadata, permissions all in database
- No meaningful functionality without it

**Why LLM is CRITICAL** (vs optional in some RAG systems):
- Core value proposition is AI responses
- Even with fallback, at least one LLM must work
- Alternative: Could make LLM optional, return only retrieved documents (not implemented)

**Why Reranker is OPTIONAL**:
- Retrieval scores alone are "good enough" for many queries
- Reranking is quality enhancement, not functional requirement
- Allows deployment without reranker dependencies

**Why Email is OPTIONAL**:
- Notifications are nice-to-have
- Core RAG functionality independent of email
- Admin can still monitor via dashboard/logs

---

## 13. Observability & Debugging

### 13.1 Logging Strategy

**Framework**: Python `logging` module with custom configuration

**Location**: `app/core/logging.py`

**Log Levels**:
```python
DEBUG:    Detailed trace (not in production)
INFO:     Normal operations (requests, cache hits, component init)
WARNING:  Recoverable issues (fallback used, optional feature disabled)
ERROR:    Failures requiring attention (LLM call failed, DB error)
CRITICAL: Startup failures, system unavailable
```

**Log Format**:
```python
[2026-01-28 10:30:45] INFO [app.services.conversation] user_id=123 query="core values" - RAG request received
[2026-01-28 10:30:45] DEBUG [app.services.retrieval] - Retrieved 10 documents, 6 accessible
[2026-01-28 10:30:46] WARNING [app.core.llm_factory] - Primary LLM timeout, using fallback
[2026-01-28 10:30:47] INFO [app.services.conversation] response_time=2.1s - Response generated
```

**Structured Logging** (JSON option):
```python
{
    "timestamp": "2026-01-28T10:30:45Z",
    "level": "INFO",
    "logger": "app.services.conversation",
    "user_id": 123,
    "query": "core values",
    "message": "RAG request received"
}
```

**Log Sanitization** (`log_sanitizer.py`):
```python
# Redact sensitive data before logging
sanitized = sanitize_log_data({
    "api_key": "sk-1234567890",  # Redacted
    "password": "secret123",      # Redacted
    "query": "what is the secret sauce?"  # NOT redacted (business data)
})
# Output: {"api_key": "***REDACTED***", "password": "***REDACTED***", "query": "..."}
```

**Log Destinations**:
- **Development**: Console (stdout) with colors
- **Production**: File (`logs/app.log`) + optional external service (DataDog, CloudWatch)

### 13.2 Error Classification

**Error Types** (from `app/core/exceptions.py`):

1. **VectorStoreError**: Vector database issues (connection, indexing)
2. **LLMProviderError**: LLM API failures (timeout, quota, invalid response)
3. **EmbeddingError**: Embedding generation failures
4. **PermissionError**: Access control violations
5. **ValidationError**: Input validation failures
6. **CacheError**: Redis failures (non-critical)

**Error Context**:
```python
raise VectorStoreError(
    message="Query failed",
    details={
        "provider": "qdrant",
        "collection": "documents",
        "query": sanitized_query,
        "error": str(original_error)
    }
)
```

**Error Handlers** (FastAPI):
```python
@app.exception_handler(VectorStoreError)
async def vector_store_error_handler(request, exc):
    logger.error(f"Vector store error: {exc.details}")
    return JSONResponse(
        status_code=503,
        content={"error": "Search temporarily unavailable"}
    )
```

### 13.3 Security-Relevant Logging

**What is Logged**:
- Access denials (user tried to access restricted document)
- Permission changes (user granted/revoked clearance)
- Failed login attempts
- API key usage (for rate limiting)
- Document uploads (file_id, uploader, timestamp)

**What is NOT Logged** (security risk):
- Full query text if contains PII (sanitized)
- Retrieved document content (only metadata)
- API keys, passwords (redacted)
- User session tokens

**Activity Log** (dedicated table):
```sql
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50),  -- "query", "upload", "access_denied"
    resource_type VARCHAR(50),
    resource_id INTEGER,
    metadata JSONB,
    timestamp TIMESTAMP
);
```

**Example Entries**:
```json
{
    "user_id": 123,
    "action": "access_denied",
    "resource_type": "document",
    "resource_id": 456,
    "metadata": {
        "reason": "insufficient_clearance",
        "required_level": "TOP_SECRET",
        "user_level": "CONFIDENTIAL"
    }
}
```

### 13.4 Debug vs Production Behavior

**Debug Mode** (`DEBUG=True`):
- Verbose logging (DEBUG level)
- Full stack traces in responses
- Auto-reload on code changes
- Detailed error pages

**Production Mode** (`DEBUG=False`):
- INFO level logging only
- Generic error messages to users
- Stack traces in logs only
- Performance optimizations enabled

**Toggle Points**:
```python
if settings.app_settings.DEBUG:
    logger.setLevel(logging.DEBUG)
    app.debug = True
else:
    logger.setLevel(logging.INFO)
    app.debug = False
```

### 13.5 Performance Monitoring

**Metrics Tracked**:
- Request latency (retrieval, generation, total)
- Cache hit rates (response, context, settings)
- LLM token usage
- Vector search timing
- Database query counts

**Logging**:
```python
start_time = datetime.now(timezone.utc)
# ... operation ...
duration = (datetime.now(timezone.utc) - start_time).total_seconds()
logger.info(f"Operation completed in {duration:.2f}s")
```

**Dashboard**:
- Admin dashboard shows aggregate metrics
- Per-user usage statistics
- System health indicators

---

## 14. Trade-offs & Constraints (Observed)

### 14.1 Security vs Performance

**Trade-off**: Metadata filtering in vector search vs post-retrieval filtering

**Decision**: Hybrid approach
- Primary: Metadata filters at search time (efficient)
- Secondary: Post-retrieval double-check (security guarantee)

**Rationale**:
- Metadata filtering reduces documents processed (faster)
- Post-retrieval ensures no metadata sync issues (safer)
- Code: `app/services/permission_service.py` and `app/services/vector_store/retriever.py`

**Complexity**: Maintains filtering logic in two places

---

### 14.2 Flexibility vs Simplicity

**Trade-off**: Unified LLM configuration vs per-use-case configs

**Decision**: Separate LLM instances for different purposes
- Primary LLM (generation)
- Classifier LLM (intent classification)
- Internal LLM (decomposition, validation)
- Fallback LLM (error recovery)

**Rationale**:
- Cost optimization (use cheaper models for classification)
- Latency optimization (use faster models for decomposition)
- Reliability (fallback to different provider)

**Complexity**: 4 LLM configurations to manage

**Code**: `app/core/llm_factory.py` - separate factory methods

---

### 14.3 Caching Aggressiveness vs Freshness

**Trade-off**: Long TTL (more hits) vs short TTL (fresher data)

**Decision**: Tiered TTLs
- Response cache: 1 hour (queries change slowly)
- Context cache: 30 minutes (documents update occasionally)
- Settings cache: 5 minutes (admin changes rare but critical)

**Rationale**:
- Response cache: Identical queries likely within an hour
- Context cache: Balance between retrieval cost and document updates
- Settings cache: Admin changes need quick propagation

**Risk**: Stale data if documents updated
- Mitigation: Manual cache invalidation on document changes (not implemented)
- **TODO**: Document update webhook to clear relevant cache entries

**Code**: `app/events/semantic_cache_event.py` - TTL constants

---

### 14.4 Feature Richness vs Startup Reliability

**Trade-off**: Fail startup if optional feature unavailable vs warn and continue

**Decision**: Optional features degrade gracefully
- Reranker unavailable → Use retrieval scores
- Fallback LLM failed → Rely on primary LLM
- Email client failed → Disable notifications

**Rationale**:
- Core RAG functionality (retrieval + generation) still works
- Avoid deployment failures due to non-critical dependencies
- Allow incremental feature adoption

**Risk**: Silent degradation
- Mitigation: Prominent warnings in logs
- Dashboard shows enabled/disabled features

**Code**: `app/core/startup.py` - try/except with warnings for optional components

---

### 14.5 Provider Abstraction vs Native Features

**Trade-off**: LangChain abstraction (portable) vs native SDK (full features)

**Decision**: LangChain as primary interface, native SDKs where needed

**Rationale**:
- LangChain: Provider-agnostic, easier to swap
- Native: Access to provider-specific features (hybrid search, function calling)

**Example**:
- Vector search: LangChain `VectorStore` interface
- Hybrid search: Native Qdrant client for BM25 configuration

**Complexity**: Mixed usage - some code uses LangChain, some uses native SDKs

**Code**: `app/core/vector_store_factory.py` - LangChain wrappers around native clients

---

### 14.6 Security Isolation vs Cache Efficiency

**Trade-off**: User-scoped cache keys (secure) vs global keys (efficient)

**Decision**: Mixed approach
- **Context cache**: User-scoped (secure)
- **Response cache**: Global (efficient but risky)

**Rationale**:
- Context cache: Document access varies by user → must isolate
- Response cache: Identical queries often have same answer → share for efficiency

**Risk**: Cross-user data leakage in response cache
- **Mitigation**: Documented in `CACHING_GUIDE.md`
- **Recommendation**: Disable semantic cache for strict isolation requirements

**Code**:
- Context cache: `app/events/semantic_cache_event.py` - includes `user_id` in key
- Response cache: `app/core/semantic_cache.py` - no user scoping

---

## 15. Known Limitations & Deferred Decisions

### 15.1 Explicit TODOs

**From Code Comments**:

1. **Document Update Invalidation** (`app/events/semantic_cache_event.py`):
   ```python
   # TODO: Implement cache invalidation on document updates
   # Currently relies on TTL, may serve stale data
   ```

2. **Encryption Key Rotation** (`app/core/security.py`):
   ```python
   # TODO: Automated key rotation with versioning
   # Currently manual process requiring database re-encryption
   ```

3. **Hybrid Search Fallback** (`app/core/vector_store_factory.py`):
   ```python
   # TODO: Automatic fallback to dense search if hybrid fails
   # Currently logs warning but doesn't retry
   ```

4. **Reranker Batch Processing** (`app/services/vector_store/reranker.py`):
   ```python
   # TODO: Batch rerank requests for efficiency
   # Currently one request per query, can be expensive
   ```

5. **Semantic Cache User Scoping** (`app/core/semantic_cache.py`):
   ```python
   # TODO: Add optional user_id parameter for strict isolation
   # Currently global, documented as limitation
   ```

### 15.2 Feature Flags Indicating Incomplete Work

**Disabled by Default** (experimental or incomplete):

1. `ENABLE_DECOMPOSITION` - Query decomposition
   - Works but adds latency
   - Needs fine-tuning for production use
   - May over-decompose simple queries

2. `ENABLE_INTENT_CLASSIFIER` - Intent classification
   - LLM-based classifier needs prompt optimization
   - Simple classifier too basic for nuanced queries
   - Considering hybrid approach

3. `HYBRID_SEARCH` - Dense + sparse retrieval
   - Works for Qdrant, Weaviate, Milvus
   - Configuration complexity high
   - Needs more testing in production scenarios

### 15.3 Areas Designed for Future Extension

**Pluggable Components** (designed for addition):

1. **Reranker Providers**:
   - Current: Cohere, HuggingFace, Jina
   - Future: Custom cross-encoders, learned rerankers
   - Extension point: `app/core/reranker_factory.py`

2. **Vector Store Providers**:
   - Current: Qdrant, Weaviate, Milvus, Chroma, FAISS, PGVector
   - Future: Pinecone, Elasticsearch, custom stores
   - Extension point: `app/core/vector_store_factory.py`

3. **LLM Providers**:
   - Current: OpenAI, Anthropic, Google, Groq, Ollama, Bedrock
   - Future: Azure OpenAI, Vertex AI, custom endpoints
   - Extension point: `app/core/llm_factory.py`

4. **Embedding Providers**:
   - Current: OpenAI, HuggingFace, Cohere, Google
   - Future: Custom embeddings, fine-tuned models
   - Extension point: `app/core/embedding_factory.py`

5. **Event Handlers**:
   - Current: Activity logging, caching
   - Future: Webhooks, metrics export, audit trails
   - Extension point: `app/handlers/`, auto-registered

**Extension Pattern**:
```python
# Add new provider to factory
def get_new_provider(settings):
    if settings.provider == "new_provider":
        return NewProviderClass(settings)
    # ... existing providers
```

### 15.4 Deferred Architectural Decisions

**Multi-Tenancy**:
- Current: Single organization, multiple users
- Future: Full multi-tenant isolation (separate vector stores per tenant)
- Deferred: Adds significant complexity, not needed for current scale

**Async Vector Search**:
- Current: Synchronous vector search (LangChain retriever)
- Future: Async retriever for better concurrency
- Deferred: LangChain async support still evolving

**Distributed Caching**:
- Current: Single Redis instance
- Future: Redis Cluster for horizontal scaling
- Deferred: Premature optimization, current Redis handles load

**Query Analytics**:
- Current: Basic logging
- Future: Query understanding patterns, success metrics, A/B testing
- Deferred: Requires dedicated analytics infrastructure

**Document Versioning**:
- Current: Replace on update (no history)
- Future: Track document versions, rollback capability
- Deferred: Storage and UX complexity

---

## 16. Summary for Reviewers

### 16.1 What the System Does Particularly Well

1. **Provider Flexibility**: Genuinely provider-agnostic, can swap LLMs/embeddings/vector stores without code changes

2. **Security-First Design**: Multi-level access control enforced at multiple layers with clear isolation

3. **Graceful Degradation**: Optional features fail safely without crashing core functionality

4. **Comprehensive Configuration**: Every aspect configurable via environment or database, no hardcoded assumptions

5. **Production-Ready Error Handling**: Explicit error types, fallback strategies, detailed logging

6. **Event-Driven Architecture**: Background processing doesn't block user requests, extensible handler system

### 16.2 Where Complexity is Highest

1. **Configuration Layer** (11 settings files):
   - Pro: Explicit and modular
   - Con: Overwhelming for new developers, easy to misconfigure
   - Mitigation: Validation at startup, comprehensive documentation

2. **Caching System** (3 distinct cache types):
   - Pro: Performance optimization
   - Con: Cache invalidation complexity, user isolation challenges
   - Mitigation: Documented trade-offs, conservative TTLs

3. **Security Filtering** (metadata + post-retrieval):
   - Pro: Defense in depth
   - Con: Duplicate logic, potential for inconsistencies
   - Mitigation: Shared permission service, comprehensive tests

4. **Startup Sequence** (12-step initialization):
   - Pro: Controlled dependency order
   - Con: Complex failure modes, hard to reason about partial startup
   - Mitigation: Clear critical vs optional distinction, detailed logging

### 16.3 Where Future Contributors Should Be Careful

1. **Cache Key Composition**:
   - **Risk**: Forgetting to include user_id or permissions in key → security leak
   - **Mitigation**: Code review checklist, automated tests for cross-user isolation

2. **Security Filtering**:
   - **Risk**: Adding retrieval path that bypasses permission checks
   - **Mitigation**: Centralize filtering in `PermissionService`, never bypass

3. **Optional Feature Flags**:
   - **Risk**: Assuming feature is always enabled → runtime errors
   - **Mitigation**: Always check `if settings.*.ENABLE_*: ...` before using feature

4. **LLM Provider Changes**:
   - **Risk**: Breaking fallback logic or introducing new API requirements
   - **Mitigation**: Test matrix for all providers, integration tests

5. **Database Migrations**:
   - **Risk**: Breaking encrypted column handling
   - **Mitigation**: Alembic migrations, explicit encryption/decryption in models

### 16.4 Which Subsystems are Most Sensitive to Change

1. **Security & Permissions** (`app/services/permission_service.py`):
   - Changes here affect all document access
   - Requires security review
   - Extensive testing needed

2. **Startup Controller** (`app/core/startup.py`):
   - Changes affect application availability
   - Dependency order is fragile
   - Regressions break entire system

3. **Caching Layer** (`app/core/semantic_cache.py`, event handlers):
   - Changes affect performance AND security
   - Cache invalidation bugs hard to detect
   - Test with real workloads

4. **Vector Store Factory** (`app/core/vector_store_factory.py`):
   - Changes affect all providers
   - Provider-specific quirks easy to break
   - Test across multiple providers

5. **Conversation Service** (`app/services/conversation/service.py`):
   - Core user-facing functionality
   - Complex orchestration of many components
   - Changes have wide-reaching effects

### 16.5 Recommended Next Steps for New Contributors

1. **Start Here**:
   - Read `docs/INSTALLATION.md` - Setup instructions
   - Read `docs/SETTINGS_GUIDE.md` - Configuration deep dive
   - Read `docs/CACHING_GUIDE.md` - Performance optimization

2. **Understand Core Flow**:
   - Trace a request: `app/routes/conversation.py` → `app/services/conversation/service.py` → `app/services/conversation/response_service.py`
   - Read `app/core/startup.py` - Component initialization
   - Review `app/services/permission_service.py` - Security model

3. **Safe Areas to Experiment**:
   - Adding event handlers (`app/handlers/`)
   - Adding new LLM/embedding providers (factories)
   - Customizing prompts (`app/config/prompt_settings.py`)
   - Admin dashboard features (`app/routes/admin.py`)

4. **High-Risk Changes** (require careful review):
   - Security filtering logic
   - Caching key generation
   - Startup sequence changes
   - Database schema migrations

---

## Appendix A: Component Dependency Graph

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
    ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
    │  Routes  │  │Middleware│  │Exception │  │ Startup  │
    │          │  │          │  │ Handlers │  │Controller│
    └────┬─────┘  └──────────┘  └──────────┘  └────┬─────┘
         │                                          │
    ┌────▼─────────────────────────────────────────▼─────┐
    │              Service Layer                          │
    ├──────────────────────┬──────────────────────────────┤
    │ ConversationService  │  PermissionService           │
    │ ResponseService      │  DocumentIngestionService    │
    │ UserService          │  SettingsService             │
    └──────────┬───────────┴──────────┬───────────────────┘
               │                      │
    ┌──────────▼──────────┐  ┌────────▼──────────┐
    │    Core Layer       │  │   Event Bus       │
    ├─────────────────────┤  ├───────────────────┤
    │ LLM Factory         │  │ Handlers Registry │
    │ Embedding Factory   │  │ Activity Logger   │
    │ Vector Store Factory│  │ Cache Handlers    │
    │ Reranker Factory    │  └───────────────────┘
    │ Cache Manager       │
    │ Database Manager    │
    └──────────┬──────────┘
               │
    ┌──────────▼─────────────────────┐
    │   External Dependencies        │
    ├────────────────────────────────┤
    │ PostgreSQL (Database)          │
    │ Redis (Cache)                  │
    │ Qdrant/Weaviate (Vector Store) │
    │ OpenAI/Anthropic (LLM)         │
    │ OpenAI/HF (Embeddings)         │
    └────────────────────────────────┘
```

---

## Appendix B: Configuration Files Map

```
app/config/
│
├── settings.py                 # Root settings aggregator
│   └── Imports all other settings, provides unified interface
│
├── app_settings.py             # General application settings
│   ├── APP_NAME, VERSION
│   ├── DEBUG, ENVIRONMENT
│   ├── Feature flags (ENABLE_DECOMPOSITION, ENABLE_RERANKER, etc.)
│   ├── SECRET_KEY, encryption keys
│   └── CORS, rate limiting, file paths
│
├── database_settings.py        # PostgreSQL configuration
│   ├── DB_HOST, DB_PORT, DB_NAME
│   ├── DB_USER, DB_PASSWORD
│   ├── Connection pool settings
│   └── SSL/TLS options
│
├── cache_settings.py           # Redis configuration
│   ├── REDIS_HOST, REDIS_PORT
│   ├── Connection pool settings
│   ├── TTL defaults
│   └── Encryption options
│
├── vectordb_settings.py        # Vector store configuration
│   ├── VECTOR_DB_PROVIDER (qdrant, weaviate, etc.)
│   ├── Provider-specific settings (URL, API key, collection name)
│   ├── HYBRID_SEARCH toggle
│   └── Search parameters (TOP_K, similarity threshold)
│
├── embedding_settings.py       # Embedding provider configuration
│   ├── EMBEDDING_PROVIDER (openai, huggingface, cohere, google)
│   ├── EMBEDDING_MODEL (text-embedding-3-large, etc.)
│   ├── API keys
│   ├── Model parameters (dimensions, batch size)
│   └── Provider-specific options
│
├── llm_settings.py             # LLM provider configuration
│   ├── Primary LLM (LLM_PROVIDER, LLM_MODEL)
│   ├── Fallback LLM (FALLBACK_LLM_PROVIDER, etc.)
│   ├── Classifier LLM (CLASSIFIER_LLM_PROVIDER, etc.)
│   ├── Internal LLM (INTERNAL_LLM_PROVIDER, etc.)
│   ├── API keys, base URLs
│   ├── Model parameters (temperature, max_tokens, streaming)
│   └── Timeout, retry settings
│
├── reranker_settings.py        # Reranker configuration
│   ├── RERANKER_PROVIDER (cohere, huggingface, jina)
│   ├── RERANKER_MODEL
│   ├── Score threshold
│   ├── Top-N results
│   └── API keys
│
├── email_settings.py           # SMTP configuration
│   ├── SMTP_HOST, SMTP_PORT
│   ├── SMTP_USER, SMTP_PASSWORD
│   ├── TLS/SSL settings
│   └── FROM_EMAIL, default recipients
│
├── prompt_settings.py          # System prompts
│   ├── SYSTEM_PROMPT (main RAG prompt)
│   ├── CLASSIFICATION_PROMPT
│   ├── DECOMPOSITION_PROMPT
│   └── Fallback prompts
│
└── response_templates.py       # Error messages
    ├── Generic error responses
    ├── Permission denied messages
    ├── Rate limit messages
    └── Maintenance mode messages
```

---

**End of Architecture Document**

This document reflects the system as implemented in January 2026. For the most current information, consult the codebase and inline documentation.
