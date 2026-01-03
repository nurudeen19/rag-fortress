# Reranker Guide

Comprehensive guide to reranking for improved retrieval accuracy in RAG Fortress.

## Overview

The reranker system supports multiple providers to improve retrieval quality by re-scoring documents for semantic relevance. It's integrated via LangChain wrappers for consistency and maintainability.

## How It Works

### Architecture

**Reranker Factory** (`app/core/reranker_factory.py`)
- Singleton pattern with global instance
- Provider-agnostic initialization
- Returns LangChain document compressor instances

**Reranker Service** (`app/services/vector_store/reranker.py`)
- Business logic for document reranking
- Uses `compress_documents()` interface (standard LangChain)
- Extracts relevance scores from document metadata
- Singleton pattern for resource efficiency

### Supported Providers

1. **HuggingFace** (Local)
   - Uses sentence-transformers CrossEncoder
   - No API key required
   - Fast local inference
   - Model: Configurable (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)

2. **Cohere** (Cloud)
   - Requires API key
   - Model: Configurable (default: recommend checking Cohere docs)
   - Uses LangChain `CohereRerank` wrapper

3. **Jina** (Cloud)
   - Requires API key
   - Default model: `jina-reranker-v1-base-en` (can be overridden)
   - Uses LangChain `JinaRerank` wrapper from langchain-community

### Integration with Retrieval

Reranking is integrated into the adaptive retrieval flow:
- Triggers when initial MIN_TOP_K results have poor quality scores
- Retrieves expanded MAX_TOP_K documents from vector store
- Applies selected reranker for semantic relevance
- Returns top RERANKER_TOP_K documents above score threshold

## Retrieval Flow

### Stage 1: Initial Retrieval
1. Retrieve MIN_TOP_K (3) documents
2. Check quality against RETRIEVAL_SCORE_THRESHOLD (0.5)
3. If quality is good → return results
4. If quality is poor → proceed to Stage 2

### Stage 2: Reranking (if enabled)
1. Retrieve MAX_TOP_K (10) documents
2. Apply security filtering
3. Use cross-encoder to rerank by semantic relevance
4. Return top RERANKER_TOP_K (3) documents above RERANKER_SCORE_THRESHOLD (0.3)
5. If no quality results → return empty with error

### Stage 3: Incremental Scaling (if reranker disabled/failed)
1. Increase k by 2 (3 → 5 → 7 → 9 → 10)
2. Retry retrieval at each increment
3. Check quality at each step
4. Return first quality results or empty at MAX_TOP_K

## Configuration

### Environment Variables

Located in `app/config/reranker_settings.py`:

```bash
# On/off switch (app-level)
ENABLE_RERANKER=True

# Provider selection
RERANKER_PROVIDER=huggingface  # huggingface | cohere | jina

# Provider-specific settings
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2  # Required for HuggingFace & Cohere, optional for Jina
RERANKER_API_KEY=                                       # Required for Cohere & Jina

# Behavior settings
RERANKER_TOP_K=3
RERANKER_SCORE_THRESHOLD=0.5
```

### Provider Selection Guide

**Use HuggingFace if:**
- You want local inference (no API calls)
- You need cost-effectiveness
- Latency is acceptable (~50-200ms)
- Data privacy is important

**Use Cohere if:**
- You want cloud-based quality
- You have API budget
- You need enterprise support
- You want to use state-of-the-art models

**Use Jina if:**
- You want specialized multilingual support
- You prefer Jina's API and models
- You need cloud-based reranking

### When to Adjust

**ENABLE_RERANKER**
- Set to `False` if reranking adds too much latency
- Set to `False` for very large-scale deployments where speed is critical

**RERANKER_PROVIDER**
- Change based on requirements (cost vs. quality vs. latency)
- Can be changed without code modifications

**RERANKER_MODEL**
- HuggingFace: Use larger models for better quality (ms-marco-MiniLM-L-12-v2)
- HuggingFace: Use smaller models for speed (ms-marco-TinyBERT-L-2-v2)
- Cohere: Check Cohere docs for available models
- Jina: Leave default or specify custom model

**RERANKER_TOP_K**
- Increase to 5-7 for broader context
- Decrease to 1-2 for very focused responses

**RERANKER_SCORE_THRESHOLD**
- Increase (0.4-0.5) for stricter quality requirements
- Decrease (0.2-0.25) for more permissive retrieval

## Reranking Strategy

### Bi-Encoder (Embeddings) vs. Reranker

**Bi-Encoder (Embeddings)**
- Encodes query and documents separately
- Fast similarity computation (dot product)
- Good for initial retrieval from large corpus
- Less accurate for subtle relevance differences

**Reranker (Cross-Encoder or API-based)**
- Processes query + document together
- Sees full interaction between query and text
- More accurate relevance scoring
- Slower but perfect for small reranking sets

### Hybrid Retrieval Flow

1. **First pass**: Bi-encoder retrieves candidates quickly (MIN_TOP_K)
2. **Quality check**: Fast threshold check on similarity scores
3. **Second pass**: If needed, reranker re-scores larger set (MAX_TOP_K)
4. **Result**: Best of both worlds - speed + accuracy

## Performance Considerations

### Memory

**HuggingFace (Local)**
- Cross-encoder model: ~50MB (ms-marco-MiniLM-L-6-v2)
- Lazy loading: Only loads when first needed
- Singleton pattern: One instance per application

**Cohere/Jina (Cloud)**
- Minimal local memory (API client only)
- Network latency overhead (~100-500ms)

### Latency

**HuggingFace (Local)**
- Initial retrieval (MIN_TOP_K): ~10-50ms
- Vector similarity check: <1ms
- Reranking (MAX_TOP_K=10): ~50-200ms
- Total worst case: ~250-300ms (with reranking)
- Best case: ~10-50ms (quality results without reranking)

**Cohere/Jina (Cloud)**
- API call + network: ~500-2000ms
- Recommended only for high-latency tolerance scenarios
- Batch reranking recommended for efficiency

### Throughput

**HuggingFace**
- CPU-bound
- Consider GPU deployment for high-traffic scenarios
- Supports batch processing

**Cohere/Jina**
- API rate limits apply
- Batch processing available
- Cost per API call applies

## Error Handling

### Model Loading Failure
- Logs error with installation instructions
- Raises exception to prevent silent failures
- User gets clear error message

### Reranking Failure
- Catches exceptions during reranking
- Falls back to incremental scaling
- Logs error for debugging
- Returns original documents without reranking

### Vector Store Score Support
- Detects if scores unavailable
- Falls back to basic retrieval
- Logs warning for monitoring

## Testing Recommendations

### Unit Tests
- Test reranker service initialization
- Test reranking with various document counts
- Test threshold filtering
- Test error handling and fallbacks

### Integration Tests
- Test full retrieval flow with poor initial results
- Test reranking activation conditions
- Test security filtering before reranking
- Test performance with various dataset sizes

### Load Tests
- Measure latency impact of reranking
- Test memory usage under load
- Verify singleton pattern efficiency

## Migration Notes

No breaking changes - reranker is additive:
- Existing retrieval flow still works
- Reranker adds quality improvement layer
- Can be disabled via configuration
- No database schema changes needed

## Dependencies

### Core Reranker Dependencies

**Always required:**
```
langchain-core>=1.1.3
langchain-community>=0.4.1
```

**HuggingFace provider:**
```
sentence-transformers>=5.1.2
```

**Cohere provider:**
```
langchain-cohere>=0.5.0
cohere>=5.5.8
```

**Jina provider:**
```
langchain-community>=0.4.1  # Already required, includes JinaRerank
```

All dependencies are in `pyproject.toml` and `requirements.txt`

## Monitoring

### Key Metrics
- Reranking activation rate (% of queries)
- Average reranking latency
- Quality improvement (before/after scores)
- Empty result rate (should decrease)

### Log Events
- "Reranking X documents (target: top Y)"
- "Reranker found X quality documents"
- "Reranker could not find quality documents"
- Model loading success/failure

## Implementation Details

### Factory Pattern

**Location**: `app/core/reranker_factory.py`

```python
from app.core.reranker_factory import get_reranker

reranker = get_reranker()  # Returns initialized instance or None if disabled
```

**Features:**
- Singleton pattern with global instance
- Lazy initialization on first call
- Returns None if reranker disabled
- Handles all provider initialization

### Service Integration

**Location**: `app/services/vector_store/reranker.py`

```python
from app.services.vector_store.reranker import RerankerService

service = RerankerService()
reranked_docs = service.rerank(documents, query)
```

**Provider-agnostic:**
- Uses `compress_documents()` interface (standard LangChain)
- Works with any LangChain document compressor
- Extracts relevance scores from metadata

## Future Enhancements

### Potential Improvements
1. **GPU Acceleration**: Enable CUDA for HuggingFace models
2. **Batch Reranking**: Process multiple queries together
3. **Hybrid Scoring**: Combine vector similarity + reranker scores
4. **Async Reranking**: Non-blocking reranking for better UX
5. **Cache Results**: Cache reranking results for repeated queries
6. **Multi-stage Reranking**: Chain multiple rerankers for quality

### Alternative HuggingFace Models
- `cross-encoder/ms-marco-MiniLM-L-12-v2` (larger, more accurate)
- `cross-encoder/ms-marco-TinyBERT-L-2-v2` (smaller, faster)
- Domain-specific models for specialized use cases
