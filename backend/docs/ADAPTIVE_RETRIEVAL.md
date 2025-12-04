# Adaptive Retrieval System

## Overview

The retrieval system uses adaptive top-k adjustment with quality-based scoring to ensure high-quality document retrieval while preventing false positives.

## How It Works

### 1. Quality-Based Retrieval with Reranking

Instead of retrieving a fixed number of documents, the system uses a multi-stage approach:

1. **Starts small**: Begins with `MIN_TOP_K` documents (default: 3)
2. **Checks quality**: Evaluates if retrieved documents meet the `RETRIEVAL_SCORE_THRESHOLD` (default: 0.5)
3. **Reranking fallback**: If initial results are poor quality AND reranker is enabled:
   - Retrieves `MAX_TOP_K` documents (default: 10)
   - Uses cross-encoder model to rerank based on semantic relevance
   - Returns top `RERANKER_TOP_K` documents (default: 3) that meet `RERANKER_SCORE_THRESHOLD` (default: 0.3)
4. **Adaptive scaling**: If reranker disabled or unavailable, increases top-k incrementally (by 2)
5. **Returns intelligently**: 
   - If high-quality results found: returns them
   - If only one good result among many poor ones: returns just that one
   - If no quality results after all attempts: returns empty context with clear error message

### 2. Reranker Integration

**When Reranking Activates**
- Initial `MIN_TOP_K` retrieval yields poor quality scores
- Reranker is enabled (`ENABLE_RERANKER=True`)
- System immediately retrieves `MAX_TOP_K` documents and applies reranking

**Reranking Process**
- Uses cross-encoder model (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Evaluates semantic relevance between query and each document
- Returns top `RERANKER_TOP_K` documents with scores above `RERANKER_SCORE_THRESHOLD`
- More accurate than vector similarity alone for relevance ranking

**Why Cross-Encoder?**
- Bi-encoders (embeddings): Fast but less accurate, good for initial retrieval
- Cross-encoders: Slower but more accurate, perfect for reranking small sets
- Cross-encoders see query + document together, better understanding of relevance

### 3. Edge Cases

**Single High-Quality Document**
- If retrieval finds only ONE document above threshold with multiple low-scoring documents
- System returns ONLY the high-quality document
- Does NOT increase top-k (prevents diluting quality with noise)

**No Quality Results**
- If system reaches MAX_TOP_K without finding quality documents
- If reranker also fails to find quality results
- Returns empty context with error: "No relevant documents found for your query"
- Rationale: Better to return nothing than false positives that waste tokens and confuse the LLM

**Reranker Disabled**
- Falls back to incremental top-k scaling (3 → 5 → 7 → 9 → 10)
- Uses only vector similarity scores for quality checks

### 4. Security Filtering

Security filtering is applied AFTER quality checks but BEFORE reranking:
1. Retrieve documents with scores
2. Apply user security clearance filtering (remove inaccessible documents)
3. Check quality or apply reranking on accessible documents only
4. Return accessible, high-quality documents

## Configuration

### Environment Variables

```bash
# Adaptive Retrieval Settings
MIN_TOP_K=3                     # Initial number of documents to retrieve
MAX_TOP_K=10                    # Maximum documents when increasing
RETRIEVAL_SCORE_THRESHOLD=0.5   # Minimum quality score (0.0-1.0)

# Reranker Settings
ENABLE_RERANKER=True            # Enable reranking for poor quality results
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2  # Cross-encoder model
RERANKER_TOP_K=3                # Documents to return after reranking
RERANKER_SCORE_THRESHOLD=0.3    # Minimum reranker score (0.0-1.0)
```

### Database Settings

Add these to application_settings via seeder or admin UI:

**Adaptive Retrieval:**
- `min_top_k` (integer): Minimum initial retrieval size
- `max_top_k` (integer): Maximum retrieval size
- `retrieval_score_threshold` (float): Quality threshold

**Reranker:**
- `enable_reranker` (boolean): Enable/disable reranking
- `reranker_model` (string): Cross-encoder model name
- `reranker_top_k` (integer): Documents to return after reranking
- `reranker_score_threshold` (float): Minimum reranker quality score

### Validation

- `MIN_TOP_K` must be >= 1
- `MAX_TOP_K` must be >= MIN_TOP_K
- `RETRIEVAL_SCORE_THRESHOLD` must be between 0.0 and 1.0

## Implementation Details

### Core Method: `RetrieverService.query()`

```python
def query(
    self,
    query_text: str,
    top_k: Optional[int] = None,  # Overrides MIN_TOP_K if provided
    user_security_level: Optional[int] = None,
    user_department_id: Optional[int] = None
) -> Dict[str, Any]:
    """Adaptive retrieval with quality checks."""
```

### Retrieval Flow

```
1. Start with current_k = MIN_TOP_K
2. Retrieve documents with scores
3. Apply security filtering
4. Check if any documents meet threshold
5. If yes:
   - Check for single high-quality doc edge case
   - Return quality results
6. If no quality results:
   - If reranker enabled and first iteration:
     a. Retrieve MAX_TOP_K documents
     b. Apply security filtering
     c. Rerank documents using cross-encoder
     d. Return top RERANKER_TOP_K if above threshold
     e. If no quality results: return empty with error
   - Else if current_k < MAX_TOP_K: increase by 2 and retry
   - Else: return empty with error
```

### Return Format

Success case:
```python
{
    "success": True,
    "context": [Document, Document, ...],
    "count": 2,
    "max_security_level": 3
}
```

Quality failure case:
```python
{
    "success": False,
    "error": "low_quality_results",
    "message": "No relevant documents found for your query. The available documents do not match your request well enough.",
    "count": 0
}
```

Security failure case:
```python
{
    "success": False,
    "error": "insufficient_clearance",
    "message": "You do not have sufficient clearance to access the retrieved documents.",
    "count": 0,
    "max_security_level": 4
}
```

## Benefits

1. **Resource Efficiency**: Start small, only retrieve more if needed
2. **Quality Assurance**: Two-stage filtering (vector similarity + cross-encoder reranking)
3. **False Positive Prevention**: Better to return nothing than irrelevant context
4. **Token Optimization**: Don't waste LLM tokens on low-quality context
5. **Response Quality**: LLM gets better results with quality-filtered, reranked context
6. **Semantic Accuracy**: Cross-encoder reranking provides more accurate relevance scoring than embeddings alone
7. **Adaptive Strategy**: Combines fast vector search with accurate cross-encoder reranking

## Removed Features

### Old `query_with_scores()` Method

The separate `query_with_scores()` method has been removed. The standard `query()` method now:
- Always uses scores internally for quality checks
- Returns documents (not document-score tuples) for cleaner API
- Handles score-based quality filtering automatically

### Old Static TOP_K

Replaced `TOP_K_RESULTS=5` with adaptive range:
- `MIN_TOP_K=3` (starting point)
- `MAX_TOP_K=10` (upper limit)

## Migration Notes

### Configuration Changes

**Before:**
```bash
TOP_K_RESULTS=5
```

**After:**
```bash
MIN_TOP_K=3
MAX_TOP_K=10
RETRIEVAL_SCORE_THRESHOLD=0.5
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
result = retriever.query(query_text)  # Uses MIN_TOP_K by default
```

### Seeder Updates

Run the application settings seeder to add new config keys:
```bash
python backend/run_seeders.py --seed application_settings
```

## Fallback Behavior

If vector store doesn't support similarity scores:
- Falls back to basic retrieval without quality checks
- Uses `MIN_TOP_K` as static retrieval size
- Still applies security filtering
- Logs warning about missing score support

If reranker model fails to load or errors occur:
- Falls back to incremental top-k scaling
- Uses only vector similarity scores
- Logs error and continues without reranking
