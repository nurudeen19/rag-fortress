# Semantic Cache Guide

## Overview

The **Semantic Cache** feature provides intelligent caching for vector store queries using Redis Vector Library (Redis VL). Unlike traditional caching that requires exact query matches, semantic caching uses vector similarity to find cached results for semantically similar queries, dramatically improving response times while reducing LLM and vector database calls.

## Why Semantic Caching?

### Problem with Traditional Caching

Traditional caching has limitations with RAG systems:

1. **Exact Match Required**: Cache only hits if query is identical character-for-character
2. **Document Serialization Issues**: `Document` objects from LangChain are not JSON serializable
3. **Low Cache Hit Rate**: Users phrase questions differently even when asking the same thing
4. **Missed Opportunities**: "What is our refund policy?" and "Tell me about refunds" should share cache

### Semantic Cache Solution

Semantic caching solves these problems by:

- **Vector Similarity Matching**: Uses embeddings to find similar queries (not exact matches)
- **Configurable Threshold**: Control how similar queries must be (default: 0.95 cosine similarity)
- **Security-Aware**: Respects user clearance levels and department access
- **Better Serialization**: Stores processed response dict instead of Document objects
- **Higher Hit Rate**: "What's the refund policy?" matches "Tell me about refunds"

## Architecture

### Components

```
User Query
    ↓
Query Embedding (OpenAI/HuggingFace/etc)
    ↓
Redis VL Vector Search (KNN)
    ↓
Security Validation (clearance + department)
    ↓
Cache Hit/Miss
    ↓
Return Cached Result OR Perform Retrieval
```

### Storage Format

Each cache entry stores:

```python
{
    "query": "What is our refund policy?",
    "query_embedding": [0.123, 0.456, ...],  # 1536-dim vector
    "response": {
        "success": True,
        "context": [Document(...)],
        "count": 5,
        "max_security_level": 2
    },
    "min_security_level": 2,  # Derived from max security of docs
    "has_department_only": False,
    "department_ids": [1, 2, 3],
    "timestamp": 1234567890.123
}
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Enable/disable semantic cache
ENABLE_SEMANTIC_CACHE=true

# Cache TTL in seconds (default: 1 hour)
SEMANTIC_CACHE_TTL=3600

# Maximum number of cached queries (LRU eviction)
SEMANTIC_CACHE_MAX_ENTRIES=1000

# Minimum similarity for cache hit (0.0-1.0, higher = stricter)
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.95

# Encrypt cached responses (for sensitive data)
SEMANTIC_CACHE_ENCRYPT_RESPONSES=false

# Redis index name
SEMANTIC_CACHE_INDEX_NAME=semantic_cache

# Vector dimension (must match your embedding model)
# OpenAI text-embedding-ada-002: 1536
# OpenAI text-embedding-3-small: 1536
# OpenAI text-embedding-3-large: 3072
# HuggingFace sentence-transformers/all-MiniLM-L6-v2: 384
SEMANTIC_CACHE_VECTOR_DIM=1536
```

### Cache Settings Class

Settings are managed in `app/config/cache_settings.py`:

```python
class CacheSettings(BaseSettings):
    # Semantic Cache
    ENABLE_SEMANTIC_CACHE: bool = False
    SEMANTIC_CACHE_TTL: int = 3600
    SEMANTIC_CACHE_MAX_ENTRIES: int = 1000
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = 0.95
    SEMANTIC_CACHE_ENCRYPT_RESPONSES: bool = False
    SEMANTIC_CACHE_INDEX_NAME: str = "semantic_cache"
    SEMANTIC_CACHE_VECTOR_DIM: int = 1536
```

## Usage

### Basic Usage

Semantic cache is automatically integrated into the retriever service. No code changes needed:

```python
from app.services.vector_store.retriever import RetrieverService

retriever = RetrieverService()

# First query - cache miss, performs retrieval
result = await retriever.query(
    query_text="What is our refund policy?",
    user_security_level=2,
    user_department_id=1
)

# Similar query - cache hit!
result = await retriever.query(
    query_text="Tell me about refunds",
    user_security_level=2,
    user_department_id=1
)
```

### Advanced Usage

Direct semantic cache access:

```python
from app.core.semantic_cache import get_semantic_cache

semantic_cache = get_semantic_cache()

# Check cache manually
cached_result = await semantic_cache.get(
    query="What is the refund policy?",
    user_security_level=2,
    user_department_id=1
)

if cached_result:
    print("Cache hit!")
    return cached_result

# Perform retrieval...
documents = [...]
response = {"success": True, "context": documents}

# Store in cache manually
await semantic_cache.set(
    query="What is the refund policy?",
    response=response,
    documents=documents  # For security metadata analysis
)
```

### Clear Cache

```python
semantic_cache = get_semantic_cache()
await semantic_cache.clear()
```

## Security Features

### Security Level Filtering

Cache respects user security clearance:

```python
# User with level 2 clearance
user_result = await retriever.query(
    query_text="Confidential project details",
    user_security_level=2  # Can access CONFIDENTIAL (level 2)
)

# Admin with level 3 clearance queries same thing
admin_result = await retriever.query(
    query_text="Confidential project details",
    user_security_level=3  # Can access SECRET (level 3)
)

# Cache miss for admin because original cache entry
# had min_security_level=2, not sufficient for level 3 docs
```

### Department-Only Access

Cache respects department restrictions:

```python
# Engineering department user
eng_result = await retriever.query(
    query_text="Engineering standards",
    user_security_level=2,
    user_department_id=1  # Engineering dept
)

# Marketing department user queries same thing
mkt_result = await retriever.query(
    query_text="Engineering standards",
    user_security_level=2,
    user_department_id=2  # Marketing dept
)

# Cache miss for marketing user because original cache
# had department_ids=[1], which doesn't include dept 2
```

### Security Metadata Analysis

When caching, semantic cache analyzes documents to extract security requirements:

```python
def _analyze_document_security(documents):
    """Extract security metadata from retrieved documents."""
    max_security_level = None
    has_department_only = False
    department_ids = set()
    
    for doc in documents:
        # Track highest security level
        if doc.metadata.get("security_level"):
            max_security_level = max(max_security_level, level)
        
        # Track department restrictions
        if doc.metadata.get("is_department_only"):
            has_department_only = True
            department_ids.add(doc.metadata.get("department_id"))
    
    return max_security_level, has_department_only, list(department_ids)
```

### Response Encryption

Enable encryption for sensitive cached responses:

```bash
SEMANTIC_CACHE_ENCRYPT_RESPONSES=true
```

Encryption uses Fernet symmetric encryption with the key from `FERNET_SECRET_KEY` environment variable.

## Performance Tuning

### Similarity Threshold

Controls strictness of cache hits:

```bash
# Strict (0.95-1.0): Only very similar queries match
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.95  # Default

# Moderate (0.85-0.94): Allow more variation
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90

# Lenient (0.70-0.84): Match broadly similar queries
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.80
```

**Recommendation**: Start with 0.95 and lower if cache hit rate is too low.

### Cache Size

Control memory usage:

```bash
# Small (100-500): Low memory, frequent evictions
SEMANTIC_CACHE_MAX_ENTRIES=500

# Medium (500-2000): Balanced
SEMANTIC_CACHE_MAX_ENTRIES=1000  # Default

# Large (2000+): High memory, rare evictions
SEMANTIC_CACHE_MAX_ENTRIES=5000
```

**Recommendation**: Monitor cache hit rate and adjust. If evictions are frequent and hit rate is high, increase size.

### TTL Configuration

Balance freshness vs performance:

```bash
# Short TTL (300-900s): Frequently updated content
SEMANTIC_CACHE_TTL=600  # 10 minutes

# Medium TTL (1800-3600s): Semi-static content
SEMANTIC_CACHE_TTL=3600  # 1 hour (default)

# Long TTL (7200+s): Rarely changing content
SEMANTIC_CACHE_TTL=86400  # 24 hours
```

**Recommendation**: Match TTL to content update frequency.

## Monitoring

### Cache Hit Rate

Track cache effectiveness in logs:

```
INFO - Semantic cache HIT for query: 'What is our refund policy...'
DEBUG - Semantic cache MISS for query: 'Tell me about shipping...'
```

Calculate hit rate:

```
Hit Rate = (Cache Hits) / (Total Queries) × 100%

Target: 30-50% hit rate for most applications
```

### Cache Size Management

Monitor cache evictions:

```
INFO - Removed 100 old cache entries (max=1000)
```

If seeing frequent evictions, consider:
- Increasing `SEMANTIC_CACHE_MAX_ENTRIES`
- Increasing `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` (fewer but better matches)
- Decreasing `SEMANTIC_CACHE_TTL` (natural expiration)

## Integration Flow

### Retriever Service Integration

The semantic cache is integrated into the main query flow:

```python
async def query(self, query_text: str, ...):
    # 1. Check semantic cache first (vector similarity)
    semantic_result = await self.semantic_cache.get(
        query_text,
        user_security_level,
        user_department_id
    )
    if semantic_result:
        return semantic_result
    
    # 2. Check legacy cache (exact match, deprecated)
    cache_key = self._generate_cache_key(...)
    cached_result = await self.cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # 3. Perform actual retrieval
    retrieval_result = await self._perform_retrieval(...)
    
    # 4. Cache successful results in semantic cache
    if retrieval_result["success"]:
        await self.semantic_cache.set(
            query_text,
            retrieval_result,
            retrieval_result["context"]  # Documents
        )
    
    return retrieval_result
```

## Redis Requirements

### Prerequisites

Semantic cache requires **Redis Stack** or **Redis with RediSearch module** for vector search capabilities.

#### Option 1: Redis Stack (Recommended)

```bash
# Docker
docker run -d -p 6379:6379 redis/redis-stack:latest

# Or install locally
https://redis.io/docs/stack/
```

#### Option 2: Redis with RediSearch

```bash
# Redis with RediSearch module
docker run -d -p 6379:6379 redislabs/redisearch:latest
```

### Verify Redis VL Support

```python
import redis

r = redis.Redis(host='localhost', port=6379)

# Check for RediSearch module
modules = r.module_list()
has_search = any(m[b'name'] == b'search' for m in modules)

if has_search:
    print("✓ Redis VL supported")
else:
    print("✗ RediSearch module not loaded")
```

## Troubleshooting

### Semantic Cache Not Initializing

**Symptom**: Logs show "semantic cache disabled"

**Solutions**:
1. Check Redis is running: `redis-cli ping` should return `PONG`
2. Verify RediSearch module: Run verification script above
3. Check Redis URL in `.env`: `CACHE_REDIS_URL=redis://localhost:6379/0`
4. Enable in settings: `ENABLE_SEMANTIC_CACHE=true`

### Low Cache Hit Rate

**Symptom**: Most queries miss cache even for similar questions

**Solutions**:
1. Lower similarity threshold: `SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90`
2. Check embedding model consistency (same model for cache and queries)
3. Review vector dimension: Must match embedding model output
4. Increase cache size: `SEMANTIC_CACHE_MAX_ENTRIES=2000`

### High Memory Usage

**Symptom**: Redis consuming too much memory

**Solutions**:
1. Reduce cache size: `SEMANTIC_CACHE_MAX_ENTRIES=500`
2. Reduce TTL: `SEMANTIC_CACHE_TTL=1800`
3. Enable Redis maxmemory policy: `maxmemory-policy allkeys-lru`
4. Monitor cache with `INFO memory` in redis-cli

### Vector Dimension Mismatch

**Symptom**: Error "dimension mismatch" or "invalid vector"

**Solutions**:
1. Check embedding model output dimension
2. Update setting to match: `SEMANTIC_CACHE_VECTOR_DIM=1536`
3. Clear cache and recreate index: `semantic_cache.clear()`

## Best Practices

### 1. Match Vector Dimension to Embedding Model

Always set `SEMANTIC_CACHE_VECTOR_DIM` to match your embedding model:

```bash
# OpenAI text-embedding-ada-002
SEMANTIC_CACHE_VECTOR_DIM=1536

# HuggingFace all-MiniLM-L6-v2
SEMANTIC_CACHE_VECTOR_DIM=384
```

### 2. Start with High Similarity Threshold

Begin with strict threshold (0.95) and lower if needed:

```bash
# Start here
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.95

# If hit rate < 20%, try
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90
```

### 3. Monitor and Adjust Cache Size

Watch for eviction frequency:

```bash
# If evictions are rare (< 1/hour), cache is too large
# If evictions are frequent (> 10/hour), cache is too small

# Adjust accordingly
SEMANTIC_CACHE_MAX_ENTRIES=2000  # Increase if frequent evictions
```

### 4. Use Encryption for Sensitive Data

If caching confidential information:

```bash
SEMANTIC_CACHE_ENCRYPT_RESPONSES=true
FERNET_SECRET_KEY=your-secret-key-here
```

### 5. Set TTL Based on Content Freshness

Match TTL to how often content updates:

```bash
# Frequently updated (news, prices, etc.)
SEMANTIC_CACHE_TTL=600  # 10 minutes

# Static content (documentation, policies)
SEMANTIC_CACHE_TTL=86400  # 24 hours
```

### 6. Combine with Traditional Cache

Keep both caches for different use cases:

- **Semantic Cache**: For natural language queries with variation
- **Traditional Cache**: For exact-match API calls, computations, etc.

```python
# Both caches work together in retriever service
# Semantic cache checked first, then legacy cache
```

## Examples

### Example 1: FAQ System

Perfect use case for semantic caching:

```python
# User 1
result = await retriever.query("How do I reset my password?")
# Cache miss → Performs retrieval

# User 2 (similar question)
result = await retriever.query("What's the password reset process?")
# Cache hit! (similarity > 0.95)

# User 3 (related but different)
result = await retriever.query("I forgot my login credentials")
# Cache hit if similarity > threshold, miss otherwise
```

### Example 2: Department-Specific Documents

```python
# Engineering team member queries
eng_result = await retriever.query(
    query_text="Server architecture best practices",
    user_security_level=2,
    user_department_id=1  # Engineering
)
# Cache miss → Retrieves eng-only docs → Caches with dept_ids=[1]

# Another engineering team member
eng_result2 = await retriever.query(
    query_text="Best practices for server architecture",
    user_security_level=2,
    user_department_id=1  # Engineering
)
# Cache hit! (similar query + same department)

# Marketing team member
mkt_result = await retriever.query(
    query_text="Server architecture best practices",
    user_security_level=2,
    user_department_id=2  # Marketing
)
# Cache miss (dept mismatch, even though query similar)
```

### Example 3: Security-Aware Caching

```python
# Regular user queries confidential docs
user_result = await retriever.query(
    query_text="Q4 financial projections",
    user_security_level=2  # CONFIDENTIAL clearance
)
# Cache miss → Retrieves CONFIDENTIAL docs → Caches with min_security=2

# Executive with higher clearance
exec_result = await retriever.query(
    query_text="Financial projections for Q4",
    user_security_level=3  # SECRET clearance
)
# Cache miss (would need to retrieve higher clearance docs)

# Another regular user with similar query
user2_result = await retriever.query(
    query_text="What are our Q4 financial projections?",
    user_security_level=2  # CONFIDENTIAL clearance
)
# Cache hit! (similar query + matching clearance)
```

## Migration Guide

### From Traditional Cache to Semantic Cache

#### Step 1: Install Redis Stack

```bash
docker run -d -p 6379:6379 --name redis-stack redis/redis-stack:latest
```

#### Step 2: Update Configuration

Add to `.env`:

```bash
ENABLE_SEMANTIC_CACHE=true
SEMANTIC_CACHE_TTL=3600
SEMANTIC_CACHE_MAX_ENTRIES=1000
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.95
SEMANTIC_CACHE_VECTOR_DIM=1536  # Match your embedding model
```

#### Step 3: Restart Application

```bash
# Restart backend
python run.py
```

#### Step 4: Monitor Performance

Watch logs for cache hits/misses:

```bash
tail -f logs/rag_fortress.log | grep "Semantic cache"
```

#### Step 5: Tune Settings

Adjust threshold based on hit rate:

```bash
# If hit rate < 20%
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90

# If hit rate > 60% and still getting good results
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.97
```

## Conclusion

Semantic caching dramatically improves RAG system performance by:

- **Reducing Latency**: Cache hits return instantly (< 10ms vs 500-2000ms for retrieval)
- **Lowering Costs**: Fewer embedding API calls and vector searches
- **Improving UX**: Faster responses for similar questions
- **Security-Aware**: Respects clearance levels and department access
- **Intelligent**: Matches semantically similar queries, not just exact strings

Enable semantic caching to make your RAG Fortress faster and more efficient!
