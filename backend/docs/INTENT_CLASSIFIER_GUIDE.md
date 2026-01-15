# Intent Classifier Guide

Complete guide to the rule-based intent classification system for handling common pleasantries and simple queries without invoking the full RAG pipeline.

## Overview

The Intent Classifier is an intelligent interceptor that identifies common user intents (greetings, acknowledgements, goodbyes, etc.) and returns templated responses directly, bypassing the RAG pipeline for better performance and more appropriate responses.

### Benefits

- **Performance**: Instant responses for simple queries without LLM invocation
- **Cost Efficiency**: Reduces LLM API calls for non-knowledge queries
- **Better UX**: More natural responses to pleasantries
- **Resource Optimization**: Frees up RAG pipeline for actual knowledge queries

### Architecture

```
User Query
    ↓
Intent Classifier (Interceptor)
    ↓
    ├─→ [High Confidence Match] → Template Response → Stream to User
    │   (greeting, goodbye, thanks, etc.)
    │
    └─→ [Knowledge Query] → Full RAG Pipeline
        (low confidence or actual question)
```

## How It Works

### 1. Intent Classification

When a user query arrives at the conversation response service:

1. **Early Interception**: Query is analyzed before RAG pipeline
2. **Pattern Matching**: Rule-based patterns identify intent type
3. **Confidence Scoring**: Each match has a confidence score (0.0-1.0)
4. **Decision**: High confidence non-knowledge queries use templates

### 2. Supported Intent Types

| Intent | Description | Example Queries |
|--------|-------------|----------------|
| **GREETING** | User greetings and hellos | "hi", "hello", "good morning", "hey there" |
| **ACKNOWLEDGEMENT** | Confirmations and agreements | "ok", "got it", "understood", "yes", "alright" |
| **GOODBYE** | Farewells and sign-offs | "bye", "goodbye", "see you", "take care" |
| **GRATITUDE** | Thanks and appreciation | "thanks", "thank you", "appreciate it" |
| **HELP_REQUEST** | General help inquiries | "help", "what can you do", "how does this work" |
| **UNCLEAR** | Uninformative queries | "?", "huh", single letters |
| **KNOWLEDGE_QUERY** | Actual questions (uses RAG) | "What is the vacation policy?", "Show me sales data" |

### 3. Confidence Levels

The classifier assigns confidence scores to matches:

- **0.9-1.0**: Strong match (exact phrases, very specific patterns)
- **0.7-0.89**: Good match (clear patterns with some variation)
- **0.5-0.69**: Moderate match (fuzzy or partial match)
- **0.0-0.49**: Weak match (defaults to knowledge query)

Only matches above the configured threshold use template responses.

## Configuration

### Configuration

The heuristic intent classifier is **always enabled** as the default fast classifier. It cannot be disabled and has no configuration options.

For advanced intent classification with LLM-based approaches, see the separate `ENABLE_LLM_CLASSIFIER` feature.
- **Recommended**: 0.7 provides good balance

## Template Responses

### Response Variety

Each intent type has multiple template responses to provide natural variety:

```python
# Example: GREETING intent has 6 different responses
templates = [
    "Hello! How can I assist you today?",
    "Hi there! What can I help you with?",
    "Hey! I'm here to help. What would you like to know?",
    # ... more variations
]
```

Responses are randomly selected to avoid repetitiveness.

### Customizing Templates

Edit `app/config/response_templates.py`:

```python
class ResponseTemplates:
    TEMPLATES: Dict[IntentType, List[str]] = {
        IntentType.GREETING: [
            "Your custom greeting here",
            "Another greeting variation",
            # Add more...
        ],
        # ... other intents
    }
```

## Integration Flow

### In ConversationResponseService

```python
async def generate_response(self, conversation_id, user_id, user_query, stream=True):
    """Generate AI response with intent classification interceptor."""
    
    # Step 0: Intent Classification Interceptor
    if self.intent_classifier:
        intent_result = self.intent_classifier.classify(user_query)
        
        if self.intent_classifier.should_use_template(intent_result):
            # High confidence non-knowledge query - use template
            return template_response_with_streaming(intent_result.intent)
    
    # Step 1+: Continue with full RAG pipeline for knowledge queries
    # ... (existing RAG flow)
```

### Streaming Support

Template responses are streamed character-by-character to maintain consistent UX with LLM responses:

```python
async def _stream_template_response(self, intent, ...):
    """Stream template response to simulate LLM streaming."""
    template = get_template_response(intent)
    
    for char in template:
        yield {"type": "token", "content": char}
        await asyncio.sleep(0.01)  # Natural streaming delay
```

## Usage Examples

### Example 1: Greeting Flow

```
User: "hi"
  ↓
Classifier: GREETING (confidence=0.95)
  ↓
Decision: Use template (0.95 >= 0.7)
  ↓
Response: "Hello! How can I assist you today?"
  ↓
Result: No RAG pipeline invocation, instant response
```

### Example 2: Knowledge Query Flow

```
User: "What is the company vacation policy?"
  ↓
Classifier: KNOWLEDGE_QUERY (confidence=0.0)
  ↓
Decision: Use RAG pipeline
  ↓
Response: [Full RAG pipeline with context retrieval]
  ↓
Result: Normal LLM-generated response with sources
```

### Example 3: Mixed Intent (Low Confidence)

```
User: "hi, can you show me the sales report?"
  ↓
Classifier: KNOWLEDGE_QUERY (greeting detected but low confidence)
  ↓
Decision: Use RAG pipeline (safer for ambiguous queries)
  ↓
Response: [Full RAG pipeline]
```

## Pattern Matching

### Pattern Structure

Each pattern is a tuple of (regex, confidence):

```python
PATTERNS = {
    IntentType.GREETING: [
        # High confidence - exact greetings
        (r"^(hi|hey|hello)[\s!.?]*$", 0.95),
        
        # Medium confidence - greetings with additions
        (r"^(hi|hey)\s+(there|again)[\s!.?]*$", 0.85),
    ],
}
```

### Adding Custom Patterns

Edit `app/utils/intent_classifier.py`:

```python
class IntentClassifier:
    PATTERNS = {
        IntentType.GREETING: [
            # Add your custom pattern
            (r"^(howdy partner)[\s!.?]*$", 0.95),
            # ... existing patterns
        ],
    }
```

### Pattern Design Tips

1. **Be Specific**: Exact matches get higher confidence
2. **Anchor Patterns**: Use `^` and `$` for whole-message matches
3. **Case Insensitive**: All matching is case-insensitive
4. **Test Thoroughly**: Avoid intercepting knowledge queries

## Monitoring and Debugging

### Logging

The classifier logs classification decisions:

```python
logger.info(
    f"Intent intercepted: {intent_result.intent.value} "
    f"(confidence={intent_result.confidence:.2f})"
)

logger.debug(
    f"Intent classified: {intent.value} "
    f"(confidence={confidence:.2f}, pattern='{pattern[:50]}')"
)
```

### Message Metadata

Template responses are tagged in the database:

```python
meta = {
    "intent": intent.value,
    "template_response": True
}
```

Query conversation history to analyze template usage:

```sql
SELECT 
    COUNT(*) as template_count,
    meta->>'intent' as intent_type
FROM messages
WHERE meta->>'template_response' = 'true'
GROUP BY intent_type;
```

## Testing

### Running Tests

```bash
# Run all intent classifier tests
pytest tests/test_intent_classifier.py -v

# Run specific test class
pytest tests/test_intent_classifier.py::TestIntentClassifier -v

# Run with coverage
pytest tests/test_intent_classifier.py --cov=app.utils.intent_classifier
```

### Test Coverage

The test suite includes:

- ✓ Greeting pattern recognition
- ✓ Acknowledgement detection
- ✓ Goodbye identification
- ✓ Gratitude matching
- ✓ Help request handling
- ✓ Knowledge query bypass (important!)
- ✓ Confidence threshold behavior
- ✓ Template variety and randomization
- ✓ Edge cases (empty, punctuation, mixed case)

### Manual Testing

Test the classifier directly:

```python
from app.utils.intent_classifier import get_intent_classifier
from app.config.response_templates import get_template_response

classifier = get_intent_classifier(confidence_threshold=0.7)

# Test a query
result = classifier.classify("hello")
print(f"Intent: {result.intent.value}")
print(f"Confidence: {result.confidence:.2f}")

if classifier.should_use_template(result):
    template = get_template_response(result.intent)
    print(f"Template: {template}")
```

## Performance Impact

### Metrics

Based on typical usage patterns:

- **Template Response Time**: <10ms (vs 500-2000ms for RAG)
- **API Cost Reduction**: 20-30% fewer LLM calls
- **User Experience**: Instant responses for common queries

### Expected Interception Rate

Typical conversation patterns:

- Greetings: 5-10% of messages
- Acknowledgements: 8-15% of messages
- Goodbyes: 3-5% of messages
- Knowledge queries: 70-80% of messages (use RAG)

## Best Practices

### 1. Conservative Patterns

```python
# Good - specific and unambiguous
(r"^(hi|hello)[\s!.?]*$", 0.95)

# Risky - might match knowledge queries
(r".*(hi|hello).*", 0.50)  # Too broad!
```

### 2. Knowledge Query Priority

When in doubt, let the RAG pipeline handle it:

```python
# Ambiguous query - default to knowledge query
"hi, what's the vacation policy?"  # → RAG pipeline
```

### 3. Test Extensively

Always test new patterns against real knowledge queries:

```python
test_queries = [
    "What is the policy?",
    "Show me reports",
    "Explain the procedure",
]

for query in test_queries:
    result = classifier.classify(query)
    assert result.intent == IntentType.KNOWLEDGE_QUERY
```

### 4. Monitor False Positives

Track cases where knowledge queries are incorrectly intercepted:

```python
# Add logging for borderline cases
if 0.65 <= confidence < threshold:
    logger.warning(f"Borderline classification: '{query}' → {intent}")
```

## Architecture Notes

The heuristic classifier is always active as a fast, lightweight fallback. When `ENABLE_LLM_CLASSIFIER` is enabled, it provides an alternative classification method but doesn't replace the heuristic classifier.

## Troubleshooting

### Issue: Knowledge Queries Being Intercepted

**Symptom**: Actual questions get template responses

**Solution**: 
1. Check pattern specificity
2. Increase confidence threshold
3. Review logs for false positives
4. Adjust or remove problematic patterns

### Issue: Greetings Not Being Intercepted

**Symptom**: Simple greetings go through RAG pipeline

**Solution**:
1. Check confidence threshold (try lowering to 0.6)
2. Add more greeting patterns if needed
3. Check logs to see classification results
4. Review pattern matching rules in `intent_classifier.py`

### Issue: Inconsistent Template Responses

**Symptom**: Same query gets different responses

**Solution**: This is intentional for variety. To disable:

```python
# Modify response_templates.py
@classmethod
def get_response(cls, intent: IntentType) -> str:
    templates = cls.TEMPLATES.get(intent)
    return templates[0]  # Always return first template
```

## Future Enhancements

Potential improvements:

- [ ] Machine learning-based classification
- [ ] Context-aware intent detection (conversation history)
- [ ] User-specific customization
- [ ] A/B testing different templates
- [ ] Intent confidence learning from user feedback
- [ ] Multi-intent detection (e.g., "thanks, bye")

## API Reference

### IntentClassifier

```python
class IntentClassifier:
    def __init__(self, confidence_threshold: float = 0.7)
    def classify(self, query: str) -> IntentResult
    def should_use_template(self, result: IntentResult) -> bool
```

### IntentResult

```python
@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    matched_pattern: Optional[str]
```

### ResponseTemplates

```python
class ResponseTemplates:
    @classmethod
    def get_response(cls, intent: IntentType) -> str
    
    @classmethod
    def get_all_responses(cls, intent: IntentType) -> List[str]
```

**Status:** ✅ Production Ready
**Version:** 1.0
**Last Updated:** December 2025
