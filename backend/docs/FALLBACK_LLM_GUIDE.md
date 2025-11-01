# Fallback LLM Configuration Guide

## Overview

The RAG Fortress settings support a robust fallback LLM system that ensures your application remains operational even if the primary LLM provider fails. The system validates that fallback configuration differs from the primary to prevent redundant failures.

## Configuration Options

### Option 1: Custom Fallback Model (Recommended)

Provides full control over the fallback provider and model:

```bash
# Primary LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4

# Custom Fallback
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_API_KEY=your_openai_key  # Can reuse same key
FALLBACK_LLM_MODEL=gpt-3.5-turbo      # Must be different model
FALLBACK_LLM_TEMPERATURE=0.5
FALLBACK_LLM_MAX_TOKENS=1000
```

**Benefits:**
- Full control over fallback model selection
- Can use cheaper/faster models for fallback
- Customize temperature and token limits

### Option 2: Provider Default Config

Uses the provider's default configuration from standard fields:

```bash
# Primary LLM
LLM_PROVIDER=openai

# Fallback using Google's config
FALLBACK_LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_key
GOOGLE_MODEL=gemini-pro
```

**Benefits:**
- Simpler configuration
- Reuses existing provider configs
- Good for switching between providers

### Option 3: Default HuggingFace Small Model

If no fallback is configured, automatically uses a small HuggingFace model:

```bash
# Primary LLM only
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key

# No FALLBACK_* fields = automatic HuggingFace fallback
```

**Default Fallback:**
- Model: `google/flan-t5-small`
- Max Tokens: 512
- Temperature: 0.7
- Can work with HuggingFace Inference API (often free)

## Validation Rules

### Automatic Checks

The system validates configuration on startup:

1. **Different Provider/Model Check**: Ensures fallback is not identical to primary
   ```python
   # ✗ INVALID - Same provider and model
   LLM_PROVIDER=openai
   OPENAI_MODEL=gpt-3.5-turbo
   FALLBACK_LLM_PROVIDER=openai
   FALLBACK_LLM_MODEL=gpt-3.5-turbo
   
   # ✓ VALID - Same provider, different model
   LLM_PROVIDER=openai
   OPENAI_MODEL=gpt-4
   FALLBACK_LLM_PROVIDER=openai
   FALLBACK_LLM_MODEL=gpt-3.5-turbo
   
   # ✓ VALID - Different providers
   LLM_PROVIDER=openai
   FALLBACK_LLM_PROVIDER=google
   ```

2. **API Key Check**: Validates required API keys are present

## Usage in Code

### Basic Usage

```python
from app.config import settings

def generate_with_fallback(prompt: str):
    """Generate response with automatic fallback"""
    
    # Try primary LLM
    try:
        config = settings.get_llm_config()
        response = call_llm(prompt, config)
        return response
    except Exception as e:
        logger.warning(f"Primary LLM failed: {e}, using fallback...")
        
        # Use fallback LLM
        fallback_config = settings.get_fallback_llm_config()
        response = call_llm(prompt, fallback_config)
        return response
```

### Advanced Usage with Retry Logic

```python
from app.config import settings
import time

def generate_with_retry(prompt: str, max_retries=2):
    """Generate with retry on primary, then fallback"""
    
    # Try primary LLM with retries
    config = settings.get_llm_config()
    for attempt in range(max_retries):
        try:
            return call_llm(prompt, config)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            logger.error(f"Primary LLM failed after {max_retries} attempts")
            break
    
    # Fallback LLM
    try:
        fallback_config = settings.get_fallback_llm_config()
        logger.info(f"Using fallback: {fallback_config['provider']}/{fallback_config['model']}")
        return call_llm(prompt, fallback_config)
    except Exception as e:
        logger.error(f"Fallback LLM also failed: {e}")
        raise
```

### Checking Fallback Configuration

```python
from app.config import settings

# Get info about fallback
fallback = settings.get_fallback_llm_config()
print(f"Fallback Provider: {fallback['provider']}")
print(f"Fallback Model: {fallback['model']}")
print(f"Fallback Max Tokens: {fallback['max_tokens']}")

# Check if using default fallback
if settings.FALLBACK_LLM_PROVIDER:
    print(f"Custom fallback: {settings.FALLBACK_LLM_PROVIDER}")
else:
    print("Using default HuggingFace small model fallback")
```

## Configuration Examples

### Example 1: OpenAI Primary, Google Fallback

```bash
# Primary
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Fallback
FALLBACK_LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_key
GOOGLE_MODEL=gemini-pro
```

### Example 2: OpenAI GPT-4 Primary, OpenAI GPT-3.5 Fallback

```bash
# Primary - Expensive model
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# Fallback - Cheaper, faster model
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_API_KEY=sk-xxx  # Can reuse same key
FALLBACK_LLM_MODEL=gpt-3.5-turbo
FALLBACK_LLM_TEMPERATURE=0.5
FALLBACK_LLM_MAX_TOKENS=1000  # Lower for cost savings
```

### Example 3: Google Primary, Default HF Fallback

```bash
# Primary
LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_key
GOOGLE_MODEL=gemini-pro

# No fallback config = automatic free HuggingFace fallback
```

## Best Practices

1. **Different Models**: Always use a different model for fallback to avoid the same failure point

2. **Cost Optimization**: Use cheaper/faster models for fallback (e.g., GPT-4 → GPT-3.5-turbo)

3. **Lower Token Limits**: Set lower `max_tokens` for fallback to control costs

4. **Monitor Fallback Usage**: Log when fallback is triggered to identify reliability issues

5. **Test Fallback Regularly**: Ensure your fallback configuration works before you need it

## Troubleshooting

### Error: "Fallback LLM cannot be the same as primary LLM"

**Cause**: Both primary and fallback are using the same provider and model

**Solution**: Change either the provider or model for fallback:
```bash
# Change model
FALLBACK_LLM_MODEL=different-model

# Or change provider
FALLBACK_LLM_PROVIDER=different-provider
```

### Error: "API_KEY is required for fallback provider"

**Cause**: Fallback provider needs an API key that wasn't provided

**Solution**: Set the appropriate API key:
```bash
FALLBACK_LLM_API_KEY=your_key
# or
GOOGLE_API_KEY=your_key  # For google provider
```

### Fallback Always Triggers

**Possible Causes**:
1. Primary API key is invalid
2. Primary model name is wrong
3. Network/API issues

**Debug Steps**:
```python
# Test primary config
config = settings.get_llm_config()
print(config)  # Verify all fields are correct
```

## Summary

The fallback LLM system provides:
- ✅ Automatic validation to prevent misconfiguration
- ✅ Flexible configuration (custom, provider-default, or automatic)
- ✅ Cost optimization through smaller fallback models
- ✅ Improved reliability and uptime
- ✅ Simple API for implementation
