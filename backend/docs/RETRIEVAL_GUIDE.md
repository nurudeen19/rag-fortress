# Document Retrieval Guide

Complete guide to adaptive retrieval, reranking, and caching in RAG-Fortress.

## Overview

The retrieval system uses a multi-stage approach combining:
1. **Adaptive top-k adjustment** - Dynamically adjusts retrieval size based on quality
2. **Reranking system** - Cross-encoder models for improved relevance scoring
3. **Quality-based filtering** - Returns only high-quality results
4. **Caching integration** - Redis-backed caching with security-aware keys
5. **Fallback strategies** - Multiple retrieval attempts with increasing scope

## Architecture

### Data Flow

```
User Query
    ↓
┌─────────────────────────────────────────────────────┐
│  RetrieverService.query()                           │
│  ──────────────────────────────────────────────────│
│  Step 1: Preprocess query                          │
│          (remove stop words, normalize)            │
│          ↓                                         │
│  Step 2: Generate cache key                        │
│          (query + scope + clearance + dept)        │
│          ↓                                         │
│  Step 3: Check Redis cache                         │
│          ├─ HIT  → Return cached result           │
│          └─ MISS → Continue to Step 4             │
│                                                     │
│  Step 4: Adaptive retrieval                        │
│          ├─ Retrieve MAX_K candidates             │
│          ├─ Apply reranking if enabled            │
│          ├─ Filter by threshold                   │
│          └─ Return top TOP_K results              │
│          ↓                                         │
│  Step 5: Cache successful results (5 min TTL)     │
│          ↓                                         │
│  Step 6: Apply security filtering                 │
│          ↓                                         │
│  Step 7: Return to response service               │
└─────────────────────────────────────────────────────┘
          ↓
ConversationResponseService
    ↓
LLM Generation & Streaming
```

## Adaptive Retrieval System

### How It Works

The retrieval system uses a streamlined process:

1. **Retrieve candidates**: Fetches `MAX_K` documents from vector store (default: 15)
2. **Apply security filter**: Removes documents user doesn't have access to
3. **Rerank if enabled**: Uses cross-encoder model to re-score for better relevance
4. **Filter by threshold**: Keeps only documents above quality threshold
5. **Return final results**: Returns top `TOP_K` documents (default: 5)

### Configuration

```env
# Retrieval Settings
TOP_K=5                         # Final number of results to return
MAX_K=15                        # Maximum candidates to retrieve
RETRIEVAL_SCORE_THRESHOLD=0.5   # Minimum quality score (0.0-1.0)

# Reranker Settings
ENABLE_RERANKER=True            # Enable reranking
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_SCORE_THRESHOLD=0.5    # Minimum reranker score (0.0-1.0)
```

### Retrieval Flow

```
1. Retrieve MAX_K candidates from vector store
2. Apply security filtering (remove inaccessible docs)
3. If reranker enabled:
   a. Rerank all candidates using cross-encoder
   b. Filter by RERANKER_SCORE_THRESHOLD
   c. Return top TOP_K documents
4. If reranker disabled:
   a. Filter by RETRIEVAL_SCORE_THRESHOLD
   b. Return top TOP_K documents
5. If no quality results:
   - Return empty with no context message
```

## Reranking System

### Why Reranking?

**Bi-encoders (embeddings):**
- Fast similarity search
- Good for initial retrieval
- Less accurate for true relevance

**Cross-encoders (rerankers):**
- Slower but more accurate
- See query + document together
- Better understanding of semantic relevance
- Perfect for reranking small result sets

### When Reranking Activates

Reranking activates when:
- `ENABLE_RERANKER=True` in configuration
- System retrieves MAX_K candidates and reranks all of them

### Reranking Process

```python
# 1. Retrieve candidates
candidates = vector_store.query(query, k=MAX_K)

# 2. Apply security filtering
accessible_docs = filter_by_security(candidates, user)

# 3. Rerank with cross-encoder if enabled
if reranker_enabled:
    reranked = cross_encoder.predict([
        (query, doc.content) for doc in accessible_docs
    ])
    
    # 4. Sort by reranker score and filter
    top_docs = [
        doc for doc, score in sorted(reranked, reverse=True)
        if score >= RERANKER_SCORE_THRESHOLD
    ][:TOP_K]
else:
    # 5. Use similarity scores
    top_docs = [
        doc for doc, score in accessible_docs
        if score >= RETRIEVAL_SCORE_THRESHOLD
    ][:TOP_K]

return top_docs
```

### Fallback Without Reranker

If reranker is disabled:
- Uses only vector similarity scores
- Filters by RETRIEVAL_SCORE_THRESHOLD
- Returns top TOP_K documents

## Security-Aware Caching

### Cache Key Model

Cache keys include full security context to prevent cross-user data leakage:

```python
cache_key = hash({
    "query": "preprocessed_query_text",
    "scope": "org" or "dept",           # Query scope
    "org_level": 1,                     # User's org-wide clearance (1-4)
    "dept_id": None or 10,              # User's department ID
    "dept_level": None or 2             # User's dept clearance (1-4)
})
```

### Cache Sharing Rules

**Scenario 1: Same org-wide clearance**
```
User A: org_level=2, dept=None
User B: org_level=2, dept=None
Query: "revenue report"

Result: ✅ SHARE cache (same clearance, no dept restrictions)
```

**Scenario 2: Different departments**
```
User A: org_level=2, dept=10, dept_level=2
User B: org_level=2, dept=20, dept_level=2
Query: "revenue report"

Result: ❌ NO SHARE (different departments)
```

**Scenario 3: Org-wide vs department user**
```
User A: org_level=2, dept=None
User B: org_level=2, dept=10, dept_level=2
Query: "revenue report"

Result: ❌ NO SHARE (different scopes)
```

### Cache Configuration

```env
# Cache Settings
CACHE_BACKEND=redis                     # or "memory"
CACHE_ENABLED=True
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300                          # 5 minutes
```

### Performance Benefits

**Cache Hit (95% of repeated queries):**
- Vector store: Not called
- Reranker: Not called
- Latency: < 10ms (Redis roundtrip)

**Cache Miss:**
- Vector store: Called once (MAX_K)
- Reranker: Called if enabled
- Latency: 100-500ms (no reranker) or 500-2000ms (with reranker)

## Service Architecture

### RetrieverService

**Responsibility:** All query and retrieval logic

```python
async def query(
    self,
    query_text: str,                              # User query
    top_k: Optional[int] = None,                  # Override TOP_K
    user_security_level: Optional[int] = None,   # Org-wide clearance (1-4)
    user_department_id: Optional[int] = None,    # User's department
    user_department_security_level: Optional[int] = None,  # Dept clearance
    user_id: Optional[int] = None                 # For logging
) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": bool,
        "context": List[Document],    # Retrieved documents
        "count": int,                 # Number of documents
        "max_security_level": int,    # Highest security accessed
        "error": str,                 # Error code if failed
        "message": str                # User-friendly error message
    }
    """
```

**Key Methods:**
- `query()` - Main retrieval method with caching
- `_preprocess_query()` - Remove stop words, normalize
- `_generate_cache_key()` - Security-aware cache keys
- `_perform_retrieval()` - Adaptive retrieval with quality checks
- `_rerank_documents()` - Cross-encoder reranking

### ConversationResponseService

**Responsibility:** Pure orchestration

```python
async def generate_response(
    self,
    conversation_id: str,
    user_id: int,
    user_query: str,
    stream: bool = True
) -> Dict[str, Any]:
    """
    Orchestrates:
    1. Get user info (clearance, department)
    2. Call retriever.query() → DELEGATED
    3. Select LLM based on doc security level
    4. Get conversation history
    5. Generate streaming response
    6. Persist messages
    
    Returns:
    {
        "success": bool,
        "streaming": bool,
        "generator": AsyncGenerator,  # If streaming=True
        "response": str,              # If streaming=False
        "error": str,                 # Error code if failed
        "message": str                # User-friendly message
    }
    """
```

## Query Processing

### Query Preprocessing

Remove stop words and normalize:

```python
# Original query
"What is the company's revenue report for Q4?"

# Preprocessed
"company revenue report Q4"
```

Benefits:
- Better cache hit rates (variations match)
- Improved semantic search
- Reduced noise in embeddings

### Edge Cases

**Single High-Quality Document:**
- If only ONE document above threshold with multiple low-scoring documents
- Returns ONLY the high-quality document
- Does NOT increase top-k (prevents diluting quality)

**No Quality Results:**
- No relevant documents found (after filtering by threshold)
- Reranker also fails to find quality results
- Returns empty context with error: "No relevant documents found"
- Rationale: Better to return nothing than false positives

**Reranker Failure:**
- Falls back to incremental top-k scaling
- Uses only vector similarity scores
- Logs error and continues

## Security Filtering

Security filtering is applied AFTER quality checks but BEFORE returning:

```python
# 1. Retrieve documents with scores
results = vector_store.query(query, k=MAX_K)

# 2. Check quality
quality_docs = [doc for doc, score in results if score >= threshold]

# 3. Apply security filtering
accessible_docs = [
    doc for doc in quality_docs
    if user_can_access(doc, user_clearance, user_dept)
]

# 4. Return accessible, high-quality documents
return accessible_docs
```

### Security Levels

Documents are filtered based on:
1. **User org-wide clearance** (1=GENERAL to 4=TOP_SECRET)
2. **User department membership** (for dept-only documents)
3. **User department clearance** (for dept-specific security)

```python
def user_can_access(doc: Document, user: User) -> bool:
    # Check department access
    if doc.is_department_only:
        if user.department_id != doc.department_id:
            return False
    
    # Check security clearance
    if doc.security_level > user.effective_clearance:
        return False
    
    return True
```

## Fallback Strategies

### 1. Reranking Fallback

```
Initial retrieval (k=3) → Low quality
    ↓
Retrieve more (k=10) + Rerank
    ↓
If success → Return reranked results
If fail → Continue to Fallback 2
```

### 2. Incremental Top-K Fallback

```
Try k=3 → Low quality
    ↓
Try k=5 → Low quality
    ↓
Try k=7 → Low quality
    ↓
Try k=9 → Low quality
    ↓
Try k=10 → If still low quality, return empty
```

### 3. Empty Result Fallback

When all strategies fail:

```python
return {
    "success": False,
    "error": "low_quality_results",
    "message": "No relevant documents found for your query. "
               "The available documents do not match your request well enough.",
    "count": 0
}
```

LLM can then respond appropriately: "I don't have enough information to answer that question."

## Return Formats

### Success Case

```python
{
    "success": True,
    "context": [Document, Document, ...],
    "count": 2,
    "max_security_level": 3,
    "cached": False  # True if from cache
}
```

### Quality Failure

```python
{
    "success": False,
    "error": "low_quality_results",
    "message": "No relevant documents found for your query.",
    "count": 0
}
```

### Security Failure

```python
{
    "success": False,
    "error": "insufficient_clearance",
    "message": "You do not have sufficient clearance to access the retrieved documents.",
    "count": 0,
    "max_security_level": 4
}
```

### Cache Hit

```python
{
    "success": True,
    "context": [Document, Document, ...],
    "count": 3,
    "max_security_level": 2,
    "cached": True,
    "cache_key": "hash_of_security_context"
}
```

## Benefits

1. **Resource Efficiency** - Start small, only retrieve more if needed
2. **Quality Assurance** - Two-stage filtering (vector similarity + cross-encoder)
3. **False Positive Prevention** - Better to return nothing than irrelevant context
4. **Token Optimization** - Don't waste LLM tokens on low-quality context
5. **Response Quality** - LLM gets better results with quality-filtered, reranked context
6. **Semantic Accuracy** - Cross-encoder reranking more accurate than embeddings alone
7. **Adaptive Strategy** - Combines fast vector search with accurate reranking
8. **Security Guarantees** - No clearance leakage through caching
9. **Cache Performance** - 95% hit rate for repeated queries

## Testing

### Test Coverage

✅ Query preprocessing (stop word removal)
✅ Cache key generation (security context included)
✅ Cache hit optimization (vector store not called)
✅ Cache miss retrieval (vector store called)
✅ Security-aware caching (no cross-clearance sharing)
✅ Adaptive retrieval (quality-based scaling)
✅ Reranking fallback (cross-encoder integration)
✅ Edge cases (single high-quality doc, no results)
✅ Async operations (Redis compatibility)

### Example Test

```python
async def test_adaptive_retrieval():
    retriever = RetrieverService()
    
    # First retrieval: low quality → triggers reranking
    result = await retriever.query(
        query_text="company revenue",
        user_security_level=2,
        user_department_id=None
    )
    
    assert result["success"] == True
    assert len(result["context"]) <= TOP_K
    assert all(doc.score >= RERANKER_SCORE_THRESHOLD for doc in result["context"])
```

## Migration from Old System

### Configuration Changes

**Before:**
```env
TOP_K_RESULTS=5
```

**After:**
```env
TOP_K=5
MAX_K=15
RETRIEVAL_SCORE_THRESHOLD=0.5
ENABLE_RERANKER=True
RERANKER_SCORE_THRESHOLD=0.3
```

### Code Changes

**Before:**
```python
# Always retrieved exactly 5 documents
result = retriever.query(query_text, top_k=5)
```

**After:**
```python
# Adaptively retrieves 3-10 documents based on quality
result = await retriever.query(query_text)  # Uses TOP_K by default
```

## File Structure

```
app/services/
├── retriever_service.py       # RetrieverService (all retrieval logic)
├── conversation_service.py    # ConversationResponseService (orchestration)
└── reranker.py               # Cross-encoder reranking

app/core/
└── cache.py                  # Redis cache integration

tests/
├── test_retriever.py         # Retrieval tests
└── test_cache.py             # Cache security tests
```

## Performance Characteristics

| Scenario | Vector Store Calls | Reranker Calls | Latency |
|----------|-------------------|----------------|---------|
| Cache hit | 0 | 0 | < 10ms |
| Quality results (k=3) | 1 | 0 | 100-500ms |
| Low quality → rerank | 1 | 1 | 500-2000ms |
| Low quality → scale | 2-3 | 0 | 200-1000ms |

## Logging

Enable debug logging:

```python
import logging

# Retriever logs
logging.getLogger('app.services.retriever_service').setLevel(logging.DEBUG)

# Cache logs
logging.getLogger('app.core.cache').setLevel(logging.DEBUG)

# Reranker logs
logging.getLogger('app.services.reranker').setLevel(logging.DEBUG)
```

## Troubleshooting

### High cache miss rate
- Check cache TTL (may be too short)
- Verify query preprocessing is consistent
- Ensure security context is properly passed

### Reranker not activating
- Verify `ENABLE_RERANKER=True`
- Check reranker model is loaded
- Ensure initial results are below threshold

### Slow retrieval
- Check vector store performance
- Verify cache is enabled and working
- Consider adjusting TOP_K and MAX_K based on your use case

### No results returned
- Check `RETRIEVAL_SCORE_THRESHOLD` (may be too high)
- Verify vector store has documents
- Check security filtering isn't removing all results

## Future Enhancements

- [ ] Hybrid search (keyword + semantic)
- [ ] Query expansion and reformulation
- [ ] Multiple reranker models based on query type
- [ ] Learning-to-rank integration
- [ ] Result diversity optimization
- [ ] Federated search across multiple sources
- [ ] Real-time feedback loop for relevance tuning

---

**Status:** ✅ Production Ready
