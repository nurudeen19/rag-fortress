# Semantic Cache Guide

## Overview

Semantic caching uses **Redis VL (Vector Library)** to match semantically similar queries instead of requiring exact string matches. The system implements **two independent cache tiers** to optimize both retrieval and response generation.

## Why Semantic Caching?

**Traditional caching problems:**
- Requires exact query match (low hit rate)
- Users phrase questions differently
- "What is our refund policy?" ≠ "Tell me about refunds"

**Semantic cache solution:**
- Uses vector similarity matching (cosine similarity)
- Matches semantically similar queries
- Two-tier architecture for flexibility
- Security-aware (clearance + department validation)

## Architecture

### Two-Tier System

**1. Response Cache** (caches final LLM responses)
- Lower similarity threshold (0.90) - matches more variations
- Shorter TTL (60 minutes) - fresher responses
- More variations per cluster (10 max) - response diversity
- Check: Before entire RAG pipeline
- Set: After LLM generation

**2. Context Cache** (caches retrieved documents)
- Higher similarity threshold (0.95) - stricter matching
- Longer TTL (120 minutes) - stable context
- Fewer variations per cluster (5 max) - focused results
- Check: Before vector search
- Set: After document retrieval

**Each tier works independently** - enable one, both, or neither.

### Semantic Clustering

Each cluster stores **multiple variations** of responses/context for the same semantic query:

```python
{
    "query": "What is our refund policy?",
    "is_encrypted": false,
    "min_security_level": 2,
    "is_department_only": false,
    "min_department_security_level": null,
    "variations": [
        {"text": "Our refund policy allows..."},
        {"text": "We offer refunds within..."},
        {"text": "You can request a refund..."}
    ]
}
```

**Key Design Points:**
- Security metadata at **root level** (applies to all variations)
- Encryption flag at **root level** (all variations encrypted/decrypted together)
- Variations contain **only the text/data**
- Single security check - no iteration needed
- Cache returns a **random variation** to avoid repetition

## Configuration

Add to `.env`:

```bash
# Global settings
SEMANTIC_CACHE_INDEX_NAME=semantic_cache
SEMANTIC_CACHE_VECTOR_DIM=1536  # Match your embedding model

# Response cache (LLM responses)
ENABLE_RESPONSE_CACHE=true
RESPONSE_CACHE_TTL_MINUTES=60
RESPONSE_CACHE_MAX_ENTRIES=10
RESPONSE_CACHE_SIMILARITY_THRESHOLD=0.1 # 0 - 2 lower for higher relevance
RESPONSE_CACHE_ENCRYPT=false

# Context cache (retrieved documents)
ENABLE_CONTEXT_CACHE=true
CONTEXT_CACHE_TTL_MINUTES=120
CONTEXT_CACHE_MAX_ENTRIES=5
CONTEXT_CACHE_SIMILARITY_THRESHOLD=0.05 # 0 - 2 lower for higher relevance
CONTEXT_CACHE_ENCRYPT=false
```

**Vector dimensions** (must match embedding model):
- OpenAI `text-embedding-ada-002`: 1536
- OpenAI `text-embedding-3-small`: 1536
- OpenAI `text-embedding-3-large`: 3072
- HuggingFace `all-MiniLM-L6-v2`: 384

## Usage

### Automatic Integration

Both cache tiers are automatically integrated - no code changes needed.

**Response Cache Flow:**
1. User query arrives at response service
2. Check response cache (semantic similarity)
3. If hit AND cluster at capacity → return cached response
4. If hit AND cluster below capacity → return cached + continue pipeline to add variation
5. If miss → run full pipeline → cache new response

**Context Cache Flow:**
1. Query arrives at retriever
2. Check context cache (semantic similarity)
3. If hit AND cluster at capacity → return cached documents
4. If hit AND cluster below capacity → return cached + continue retrieval to add variation
5. If miss → perform retrieval → cache documents

### Capacity Management

When cluster reaches `max_entries`, it stops accepting new variations but continues returning random entries. This builds up response diversity while preventing unlimited growth.

## Security

### Security Level Validation

Cache validates user clearance against cached entry requirements:

**Departmental entries** → Validated against `dept_security_level`  
**Organization entries** → Validated against `org_security_level`

```python
# Get from cache with security check
result, access_denied = await semantic_cache.get(
    cache_type="response",
    query="Q4 financial data",
    org_security_level=2,  # User's org clearance
    dept_security_level=3   # User's dept clearance (if applicable)
)

if access_denied:
    # Cache hit but insufficient clearance
    # Returns: {"access_denied": True, "is_departmental": False/True}
    if access_denied["is_departmental"]:
        return "Department-restricted content"
    else:
        return "Insufficient clearance"

if result:
    # Cache hit with access granted
    text, at_capacity = result
    if at_capacity:
        return text  # Don't generate new variation
    # else: continue to generate and add variation
```

### Storing in Cache

```python
# Set cache entry with security metadata
await semantic_cache.set(
    cache_type="response",
    query="What is our refund policy?",
    entry=response_text,
    org_security_level=2,  # CONFIDENTIAL required
    is_department_only=False,  # Organization-wide
    dept_security_level=None  # Not department-restricted
)

# Department-only cache entry
await semantic_cache.set(
    cache_type="context",
    query="Engineering specs",
    entry=formatted_context,
    org_security_level=3,  # SECRET required
    is_department_only=True,  # Department-only
    dept_security_level=3  # Department clearance required
)
```

**Key Points:**
- Security metadata stored at root level (applies to all variations)
- Automatically adds to variations until `max_entries` reached
- Encryption controlled by config (applies to all variations)

### Encryption

Enable per-tier encryption for sensitive data:

```bash
RESPONSE_CACHE_ENCRYPT=true
CONTEXT_CACHE_ENCRYPT=true
```

Uses Fernet symmetric encryption with key from `FERNET_SECRET_KEY`.

## Configuration Examples

**Context-only** (optimize retrieval):
```bash
ENABLE_RESPONSE_CACHE=false
ENABLE_CONTEXT_CACHE=true
```

**Response-only** (reduce LLM costs):
```bash
ENABLE_RESPONSE_CACHE=true
ENABLE_CONTEXT_CACHE=false
```

**Both tiers** (maximum performance):
```bash
ENABLE_RESPONSE_CACHE=true
ENABLE_CONTEXT_CACHE=true
```

**Adjust thresholds:**
```bash
# Strict matching (high precision)
RESPONSE_CACHE_SIMILARITY_THRESHOLD=0.95
CONTEXT_CACHE_SIMILARITY_THRESHOLD=0.97

# Lenient matching (high recall)
RESPONSE_CACHE_SIMILARITY_THRESHOLD=0.85
CONTEXT_CACHE_SIMILARITY_THRESHOLD=0.90
```

## Redis Requirements

Requires **Redis Stack** or **Redis with RediSearch module**:

```bash
# Docker (recommended)
docker run -d -p 6379:6379 redis/redis-stack:latest

# Or Redis with RediSearch
docker run -d -p 6379:6379 redislabs/redisearch:latest
```

Verify RediSearch module:
```bash
redis-cli MODULE LIST
# Should show "search" module
```

**Important:** The application automatically detects RediSearch support at startup. If the module is not available, semantic cache will be gracefully disabled without blocking the application. Check startup logs for:

```
✓ Redis VL supported (RediSearch module detected)
✓ Semantic Cache ENABLED: Response (...), Context (...)
```

or

```
✗ RediSearch module not loaded. Semantic cache disabled.
○ Semantic Cache DISABLED
```

## Troubleshooting

**Cache not initializing:**
- Verify Redis is running: `redis-cli ping`
- Check RediSearch module: `redis-cli MODULE LIST`
- Verify `CACHE_REDIS_URL` in `.env`
- Enable at least one tier

**Low hit rate:**
- Lower similarity threshold (0.90 or 0.85)
- Verify vector dimension matches embedding model
- Check logs for "MISS" patterns

**Vector dimension mismatch:**
- Set `SEMANTIC_CACHE_VECTOR_DIM` to match embedding model
- Clear cache: Delete and recreate Redis index

**High memory:**
- Reduce `max_entries` per tier
- Reduce TTL
- Enable Redis `maxmemory-policy allkeys-lru`
