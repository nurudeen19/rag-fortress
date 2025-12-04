# Adaptive Retrieval System

## Overview

The retrieval system uses adaptive top-k adjustment with quality-based scoring to ensure high-quality document retrieval while preventing false positives.

## How It Works

### 1. Quality-Based Retrieval

Instead of retrieving a fixed number of documents, the system:

1. **Starts small**: Begins with `MIN_TOP_K` documents (default: 3)
2. **Checks quality**: Evaluates if retrieved documents meet the `RETRIEVAL_SCORE_THRESHOLD` (default: 0.5)
3. **Adapts dynamically**: If quality is low, increases top-k incrementally (by 2) up to `MAX_TOP_K` (default: 10)
4. **Returns intelligently**: 
   - If high-quality results found: returns them
   - If only one good result among many poor ones: returns just that one
   - If no quality results after reaching MAX_TOP_K: returns empty context with clear error message

### 2. Edge Cases

**Single High-Quality Document**
- If retrieval finds only ONE document above threshold with multiple low-scoring documents
- System returns ONLY the high-quality document
- Does NOT increase top-k (prevents diluting quality with noise)

**No Quality Results**
- If system reaches MAX_TOP_K without finding quality documents
- Returns empty context with error: "No relevant documents found for your query"
- Rationale: Better to return nothing than false positives that waste tokens and confuse the LLM

### 3. Security Filtering

Security filtering is applied AFTER quality checks:
1. Retrieve documents with scores
2. Filter by quality (score threshold)
3. Apply user security clearance filtering
4. Return accessible, high-quality documents

## Configuration

### Environment Variables

```bash
# Adaptive Retrieval Settings
MIN_TOP_K=3                     # Initial number of documents to retrieve
MAX_TOP_K=10                    # Maximum documents when increasing
RETRIEVAL_SCORE_THRESHOLD=0.5   # Minimum quality score (0.0-1.0)
```

### Database Settings

Add these to application_settings via seeder or admin UI:
- `min_top_k` (integer): Minimum initial retrieval size
- `max_top_k` (integer): Maximum retrieval size
- `retrieval_score_threshold` (float): Quality threshold

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
6. If no:
   - If current_k < MAX_TOP_K: increase and retry
   - If current_k == MAX_TOP_K: return empty with error
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
2. **Quality Assurance**: Only return documents that meet quality threshold
3. **False Positive Prevention**: Better to return nothing than irrelevant context
4. **Token Optimization**: Don't waste LLM tokens on low-quality context
5. **Response Quality**: LLM gets better results with quality-filtered context

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
