# Architecture: Retriever & Response Service

## Data Flow

```
User Request (conversation API)
    ↓
routes/conversation.py (FastAPI endpoints)
    ↓
handlers/conversation.py (handle_stream_response)
    ↓
    ┌─────────────────────────────────────────────────────────┐
    │  ConversationResponseService.generate_response()        │
    │  ────────────────────────────────────────────────────   │
    │  Pure Orchestration Layer:                              │
    │                                                         │
    │  1. Get user info (clearance, department)              │
    │  2. await retriever.query(...)  ← DELEGATED           │
    │  3. Select LLM based on doc security level             │
    │  4. Get conversation history                           │
    │  5. Generate streaming response                        │
    │  6. Persist messages                                   │
    └─────────────────────────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  RetrieverService.query()                               │
    │  ────────────────────────────────────────────────────   │
    │  All Query/Retrieval Logic:                             │
    │                                                         │
    │  Step 1: Preprocess query                              │
    │          (remove stop words, normalize)                │
    │          ↓                                             │
    │  Step 2: Generate cache key                            │
    │          (query + scope + clearance + dept)            │
    │          ↓                                             │
    │  Step 3: Check Redis cache                             │
    │          ├─ HIT  → Return cached result               │
    │          └─ MISS → Continue to Step 4                 │
    │                                                         │
    │  Step 4: Adaptive retrieval                            │
    │          ├─ _perform_retrieval()                       │
    │          │  ├─ Start with MIN_TOP_K documents         │
    │          │  ├─ Check quality (threshold)              │
    │          │  ├─ Increase k if needed (up to MAX_TOP_K) │
    │          │  ├─ Try reranking if quality is low        │
    │          │  └─ Return results                         │
    │          ↓                                             │
    │  Step 5: Cache successful results (5 min TTL)         │
    │          ↓                                             │
    │  Step 6: Return to response service                    │
    └─────────────────────────────────────────────────────────┘
              ↓
    LLM Generation & Response Streaming
```

## Cache Key Security Model

### Problem
- User A (Org CONFIDENTIAL) and User B (Dept 10 CONFIDENTIAL) both query "budget"
- Without proper scoping, User A could see User B's department-specific results
- Different clearance levels shouldn't share cached results

### Solution: Multi-Factor Cache Key

```python
cache_key = hash({
    "query": "budget",                    # Preprocessed
    "scope": "org" or "dept",             # WHO can access: org-wide or dept-specific
    "org_level": 1,                       # User's org-wide clearance (1=GENERAL...4=TOP_SECRET)
    "dept_id": None or 10,                # User's department (only if scope=dept)
    "dept_level": None or 2               # User's dept clearance (only if scope=dept)
})
```

### Example Scenarios

**Scenario 1: Two org-wide users with same clearance**
```
User A: org_level=2, dept=None
User B: org_level=2, dept=None
Query: "revenue report"

Cache Key A: hash(query, scope="org", org_level=2, dept_id=None, dept_level=None)
Cache Key B: hash(query, scope="org", org_level=2, dept_id=None, dept_level=None)

Result: ✅ SHARE cache (same clearance, no dept restrictions)
```

**Scenario 2: Same org-level but different departments**
```
User A: org_level=2, dept=10, dept_level=2
User B: org_level=2, dept=20, dept_level=2
Query: "revenue report"

Cache Key A: hash(query, scope="dept", org_level=2, dept_id=10, dept_level=2)
Cache Key B: hash(query, scope="dept", org_level=2, dept_id=20, dept_level=2)

Result: ❌ NO SHARE (different departments)
```

**Scenario 3: Org-wide vs department user**
```
User A: org_level=2, dept=None
User B: org_level=2, dept=10, dept_level=2
Query: "revenue report"

Cache Key A: hash(query, scope="org", org_level=2, dept_id=None, dept_level=None)
Cache Key B: hash(query, scope="dept", org_level=2, dept_id=10, dept_level=2)

Result: ❌ NO SHARE (different scopes)
```

## Method Signatures

### RetrieverService.query()

```python
async def query(
    self,
    query_text: str,                              # User query (will be preprocessed)
    top_k: Optional[int] = None,                  # Override MIN_TOP_K (uses setting by default)
    user_security_level: Optional[int] = None,   # Org-wide clearance (1=GENERAL to 4=TOP_SECRET)
    user_department_id: Optional[int] = None,    # User's department ID
    user_department_security_level: Optional[int] = None,  # Dept-specific clearance
    user_id: Optional[int] = None                 # For logging
) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": bool,
        "context": List[Document],    # Retrieved documents
        "count": int,                 # Number of documents
        "max_security_level": int,    # Highest security level accessed
        "error": str,                 # Error code if failed
        "message": str                # User-friendly error message
    }
    """
```

### ConversationResponseService.generate_response()

```python
async def generate_response(
    self,
    conversation_id: str,
    user_id: int,
    user_query: str,
    stream: bool = True
) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": bool,
        "streaming": bool,
        "generator": AsyncGenerator,  # If streaming=True
        "response": str,              # If streaming=False
        "error": str,                 # Error code if failed
        "message": str                # User-friendly error message
    }
    """
```

## Settings Used

```python
# From app.config.app_settings
MIN_TOP_K: int = 3                      # Minimum documents to retrieve
MAX_TOP_K: int = 10                     # Maximum documents before giving up
RETRIEVAL_SCORE_THRESHOLD: float = 0.5  # Quality threshold (0-1)
ENABLE_RERANKER: bool = True            # Use reranker if quality is low

# From app.config.cache_settings
CACHE_BACKEND: str = "redis"            # or "memory"
CACHE_ENABLED: bool = True
CACHE_REDIS_URL: str = "redis://localhost:6379/0"
```

## Test Coverage

✅ Query preprocessing (stop word removal)
✅ Cache key generation (security context included)
✅ Cache hit optimization (vector store not called)
✅ Cache miss retrieval (vector store called)
✅ Security-aware caching (no cross-clearance sharing)
✅ Async operations (Redis compatibility)
✅ Conversation service orchestration (simplified)

## Performance Characteristics

### Cache Hit (95% of repeated queries)
- Vector store: Not called
- Reranker: Not called
- Latency: < 10ms (Redis roundtrip)

### Cache Miss with Quality Results
- Vector store: Called once (MIN_TOP_K documents)
- Reranker: Not called
- Latency: 100-500ms

### Cache Miss with Low Quality (5% of queries)
- Vector store: Called 2-3 times (adaptive k)
- Reranker: Called once (if enabled)
- Latency: 500-2000ms

## Security Guarantees

1. **No Clearance Leakage**: Different clearance levels have separate cache entries
2. **No Cross-Department Leakage**: Department queries separate from org-wide queries
3. **Cache Expiry**: 5-minute TTL ensures updates are visible
4. **Failed Results Not Cached**: Only successful retrievals cached
