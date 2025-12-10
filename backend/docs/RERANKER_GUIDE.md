# Reranker Guide

Comprehensive guide to cross-encoder reranking for improved retrieval accuracy in RAG Fortress.

## Overview

The reranker system uses cross-encoder models to improve retrieval quality when initial vector similarity search yields poor results. It provides semantic relevance scoring that's more accurate than bi-encoder similarity alone.

## How It Works

### Reranker Service

The `RerankerService` in `app/services/vector_store/reranker.py` provides:
- Cross-encoder model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Lazy loading for efficient memory usage
- Singleton pattern for service management
- Top-k document selection with relevance scores

### Integration with Retrieval

Reranking is integrated into the adaptive retrieval flow in `app/services/vector_store/retriever.py`:
- Triggers when initial MIN_TOP_K results have poor quality scores
- Retrieves expanded MAX_TOP_K documents from vector store
- Applies cross-encoder reranking for semantic relevance
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

### Default Settings

```bash
ENABLE_RERANKER=True
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=3
RERANKER_SCORE_THRESHOLD=0.3
```

### When to Adjust

**ENABLE_RERANKER**
- Set to `False` if reranking adds too much latency
- Set to `False` for very large-scale deployments where speed is critical

**RERANKER_TOP_K**
- Increase to 5-7 for broader context
- Decrease to 1-2 for very focused responses

**RERANKER_SCORE_THRESHOLD**
- Increase (0.4-0.5) for stricter quality requirements
- Decrease (0.2-0.25) for more permissive retrieval

## Why Cross-Encoder?

### Bi-Encoder (Embeddings)
- Encodes query and documents separately
- Fast similarity computation (dot product)
- Good for initial retrieval from large corpus
- Less accurate for subtle relevance differences

### Cross-Encoder (Reranker)
- Processes query + document together
- Sees full interaction between query and text
- More accurate relevance scoring
- Slower but perfect for small reranking sets

### Hybrid Strategy
1. **First pass**: Bi-encoder retrieves candidates quickly (MIN_TOP_K)
2. **Quality check**: Fast threshold check on similarity scores
3. **Second pass**: If needed, cross-encoder reranks larger set (MAX_TOP_K)
4. **Result**: Best of both worlds - speed + accuracy

## Performance Considerations

### Memory
- Cross-encoder model: ~50MB (ms-marco-MiniLM-L-6-v2)
- Lazy loading: Only loads when first needed
- Singleton pattern: One instance per application

### Latency
- Initial retrieval (MIN_TOP_K): ~10-50ms
- Vector similarity check: <1ms
- Reranking (MAX_TOP_K=10): ~50-200ms
- Total worst case: ~250-300ms (with reranking)
- Best case: ~10-50ms (quality results without reranking)

### Throughput
- Reranking is CPU-bound
- Consider GPU deployment for high-traffic scenarios
- Model supports batch processing for efficiency

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

Already in requirements.txt:
```
sentence-transformers>=5.1.2
```

This provides:
- CrossEncoder class
- Pre-trained cross-encoder models
- Efficient inference on CPU/GPU

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

## Future Enhancements

### Potential Improvements
1. **Model Selection**: Support multiple reranker models
2. **GPU Acceleration**: Enable CUDA for faster reranking
3. **Batch Reranking**: Process multiple queries together
4. **Hybrid Scoring**: Combine vector similarity + reranker scores
5. **Async Reranking**: Non-blocking reranking for better UX
6. **Cache Results**: Cache reranking results for repeated queries

### Alternative Models
- `cross-encoder/ms-marco-MiniLM-L-12-v2` (larger, more accurate)
- `cross-encoder/ms-marco-TinyBERT-L-2-v2` (smaller, faster)
- Domain-specific models for specialized use cases
