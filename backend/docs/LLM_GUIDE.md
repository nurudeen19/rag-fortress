# LLM Configuration Guide

## Overview

RAG Fortress uses three types of LLMs:

1. **Primary LLM** - Default LLM for all queries
2. **Internal LLM** - Local/secure LLM for highly sensitive documents (optional)
3. **Fallback LLM** - Backup LLM when primary fails (optional)

The system automatically routes queries based on document security levels and handles failover.

---

## 1. Primary LLM

The main LLM used for all queries by default.

### Supported Providers

- `openai` - OpenAI GPT models
- `google` - Google Gemini models
- `huggingface` - HuggingFace hosted endpoints
- `llamacpp` - Local GGUF models or OpenAI-compatible API endpoints

### Consolidated Configuration

All providers use a unified set of configuration fields:

```env
# Select your provider
LLM_PROVIDER=openai

# Generic fields (all providers use these)
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Optional provider-specific fields (fill only when applicable)
LLM_ENDPOINT_URL=
LLM_MODEL_PATH=
LLM_MODE=api
LLM_TIMEOUT=120
LLM_TASK=text-generation
LLM_CONTEXT_SIZE=4096
LLM_N_THREADS=4
LLM_N_BATCH=512
```

### Provider Examples

**OpenAI:**
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

**Google:**
```env
LLM_PROVIDER=google
LLM_API_KEY=your_google_api_key
LLM_MODEL=gemini-2-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

**HuggingFace:**
```env
LLM_PROVIDER=huggingface
LLM_API_KEY=your_huggingface_token
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_ENDPOINT_URL=https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct
LLM_TASK=text-generation
LLM_TIMEOUT=120
```

**Llama.cpp (Local Mode):**
```env
LLM_PROVIDER=llamacpp
LLM_MODEL_PATH=./models/llama-7b-instruct-q4_0.gguf
LLM_MODE=local
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512
LLM_CONTEXT_SIZE=4096
LLM_N_THREADS=8
LLM_N_BATCH=512
```

**Llama.cpp (API Mode):**
```env
LLM_PROVIDER=llamacpp
LLM_ENDPOINT_URL=http://localhost:8080/v1
LLM_MODEL=llama-3.1-8b-instruct
LLM_MODE=api
LLM_TIMEOUT=120
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512
```

---

## 2. Internal LLM (Optional)

Optional secure LLM for highly sensitive documents. Prevents sending confidential data to external APIs.

### When Internal LLM is Used

The `LLMRouter` automatically selects the Internal LLM when:
- `USE_INTERNAL_LLM=true`
- Document security level ≥ `INTERNAL_LLM_MIN_SECURITY_LEVEL`

### Configuration

Internal LLM uses the same consolidated approach as the primary LLM:

```env
# Enable internal LLM
USE_INTERNAL_LLM=true
INTERNAL_LLM_PROVIDER=llamacpp
INTERNAL_LLM_MIN_SECURITY_LEVEL=4  # Security level threshold (4 = HIGHLY_CONFIDENTIAL)

# Generic fields (same as primary LLM)
INTERNAL_LLM_API_KEY=
INTERNAL_LLM_MODEL=llama-3.1-8b-instruct
INTERNAL_LLM_TEMPERATURE=0.7
INTERNAL_LLM_MAX_TOKENS=1000

# Provider-specific fields (fill only when applicable)
INTERNAL_LLM_ENDPOINT_URL=http://localhost:8080/v1
INTERNAL_LLM_MODE=api
INTERNAL_LLM_TIMEOUT=120
```

### Security Levels

The system uses these permission levels (from `PermissionLevel` enum):

| Level | Name | Value |
|-------|------|-------|
| 1 | GENERAL | Organization-wide |
| 2 | RESTRICTED | Managerial data access|
| 3 | CONFIDENTIAL | Limited access |
| 4 | HIGHLY_CONFIDENTIAL | Highly sensitive |

**Example:** If `INTERNAL_LLM_MIN_SECURITY_LEVEL=3`, documents with security levels >= 3 use the internal LLM.

### Routing Logic

```
Query → Retrieve Documents → Check max security level
  ↓
If max_security_level >= INTERNAL_LLM_MIN_SECURITY_LEVEL:
  → Use Internal LLM
Else:
  → Use Primary LLM
```

---

## 3. Fallback LLM (Optional)

Optional backup LLM used when the primary LLM fails (rate limits, API errors, timeouts). **Disabled by default** to prevent startup failures on incomplete configuration.

### Enabling Fallback LLM

Fallback LLM is disabled by default. To enable it, set:

```env
ENABLE_FALLBACK_LLM=true
```

When disabled (`ENABLE_FALLBACK_LLM=false` or not set), the system will not initialize the fallback LLM and will not attempt failover.

### Configuration

Fallback LLM must be explicitly configured with its own provider. It uses the same consolidated field structure as the primary LLM:

```env
ENABLE_FALLBACK_LLM=true
FALLBACK_LLM_PROVIDER=openai

# Generic fields (same as primary)
FALLBACK_LLM_API_KEY=sk-xxx
FALLBACK_LLM_MODEL=gpt-4o-mini
FALLBACK_LLM_TEMPERATURE=0.5
FALLBACK_LLM_MAX_TOKENS=1000

# Provider-specific fields (fill only when applicable)
FALLBACK_LLM_ENDPOINT_URL=
FALLBACK_LLM_MODEL_PATH=
FALLBACK_LLM_MODE=api
FALLBACK_LLM_TIMEOUT=120
FALLBACK_LLM_TASK=text-generation
```

**Supported providers:** `openai`, `google`, `huggingface`, `llamacpp` (same as primary LLM)

### Fallback Behavior

When **enabled**, the fallback LLM is triggered when:- Primary LLM returns rate limit errors (429)
- Primary LLM times out
- Primary LLM returns server errors (500+)

The system does NOT use fallback for:
- Authentication errors (401/403)
- Configuration errors
- Invalid request errors

When **disabled**, no fallback behavior occurs—the primary LLM error propagates directly.

---

## Configuration Examples

### Example 1: OpenAI Primary + Google Fallback

```env
# Primary
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Fallback
ENABLE_FALLBACK_LLM=true
FALLBACK_LLM_PROVIDER=google
FALLBACK_LLM_API_KEY=xxx
FALLBACK_LLM_MODEL=gemini-2-flash
```

### Example 2: OpenAI Primary + Internal Llama.cpp + Optional Fallback

```env
# Primary (external API)
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4

# Internal (local secure)
USE_INTERNAL_LLM=true
INTERNAL_LLM_PROVIDER=llamacpp
INTERNAL_LLM_MIN_SECURITY_LEVEL=4
INTERNAL_LLM_MODEL_PATH=./models/secure-model.gguf
INTERNAL_LLM_MODE=local

# Fallback (optional, cheaper model)
ENABLE_FALLBACK_LLM=true
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_API_KEY=sk-xxx
FALLBACK_LLM_MODEL=gpt-3.5-turbo
FALLBACK_LLM_MAX_TOKENS=1000
```

### Example 3: Local Llama.cpp Setup

```env
# Primary (local)
LLM_PROVIDER=llamacpp
LLM_MODEL_PATH=./models/llama-7b-instruct-q4_0.gguf
LLM_MODE=local
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512
LLM_CONTEXT_SIZE=4096
LLM_N_THREADS=8
LLM_N_BATCH=512

# Internal (same setup, different threshold)
USE_INTERNAL_LLM=false

# Fallback (optional, disabled)
ENABLE_FALLBACK_LLM=false
```

### Example 4: HuggingFace with Optional Fallback

```env
# Primary
LLM_PROVIDER=huggingface
LLM_API_KEY=hf_xxx
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_ENDPOINT_URL=https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct
LLM_TASK=text-generation
LLM_TIMEOUT=120

# Fallback (to OpenAI for reliability)
ENABLE_FALLBACK_LLM=true
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_API_KEY=sk-xxx
FALLBACK_LLM_MODEL=gpt-4o-mini
```

---

## How It Works

### LLM Router (`app/services/llm_router_service.py`)

The router decides which LLM to use:

```python
def select_llm(max_security_level: Optional[int]) -> Tuple[BaseLanguageModel, LLMType]:
    # 1. Check if internal LLM should be used
    if USE_INTERNAL_LLM and max_security_level >= INTERNAL_LLM_MIN_SECURITY_LEVEL:
        return internal_llm, "internal"
    
    # 2. Use primary LLM
    return primary_llm, "primary"
```

### Error Handling (`app/utils/llm_error_handler.py`)

When primary LLM fails:

```python
try:
    response = primary_llm.generate(query)
except RateLimitError:
    # Immediately try fallback
    response = fallback_llm.generate(query)
except AuthenticationError:
    # Don't use fallback - this is a config issue
    raise
```

### Factory Pattern (`app/core/llm_factory.py`)

LLMs are initialized once at startup and reused:

```python
# Global instances (singletons)
_llm_instance = None  # Primary
_internal_llm_instance = None  # Internal
_fallback_llm_instance = None  # Fallback

def get_llm_provider() -> BaseLanguageModel:
    if _llm_instance is None:
        _llm_instance = _create_llm_provider()
    return _llm_instance
```

---

## Troubleshooting

### Internal LLM Not Being Used

**Check:**
1. `USE_INTERNAL_LLM=true`
2. Document security level ≥ `INTERNAL_LLM_MIN_SECURITY_LEVEL`
3. Internal LLM provider is configured

**Debug:**
```python
from app.services.llm_router_service import get_llm_router

router = get_llm_router()
llm, llm_type = router.select_llm(max_security_level=5)
print(f"Selected LLM type: {llm_type}")  # Should be "internal"
```

### Fallback Not Triggering

**Check:**
1. `ENABLE_FALLBACK_LLM=true` in your `.env` file
2. Primary LLM is actually failing (check logs)
3. Error is a retryable error (rate limit, timeout, server error)
4. Fallback LLM provider is properly configured

**Debug:**
```python
from app.config.llm_settings import llm_settings

print(f"Fallback enabled: {llm_settings.ENABLE_FALLBACK_LLM}")
print(f"Fallback provider: {llm_settings.FALLBACK_LLM_PROVIDER}")
```

### LLM Initialization Fails

**Common Issues:**
- Missing API key: Check that `LLM_API_KEY` is set for your provider
- Invalid model name: Verify `LLM_MODEL` matches your provider's available models
- Wrong provider name: Must be one of: `openai`, `google`, `huggingface`, `llamacpp`
- Missing endpoint URL: Some providers require `LLM_ENDPOINT_URL` (e.g., HuggingFace, llamacpp API mode)
- Wrong mode for llamacpp: Set `LLM_MODE=local` for GGUF files, `LLM_MODE=api` for OpenAI-compatible endpoints

**Debug:**
```python
from app.config.llm_settings import llm_settings

# Check consolidated settings
config = llm_settings.get_llm_config()
print(f"Provider: {config['provider']}")
print(f"Model: {config.get('model')}")
print(f"API Key set: {bool(config.get('api_key'))}")
```

### Configuration Not Recognized

The system now uses consolidated fields with optional provider-specific fields. Make sure you're using:
- `LLM_API_KEY` (not `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `HF_API_TOKEN`, etc.)
- `LLM_MODEL` (not provider-specific variants)
- `LLM_ENDPOINT_URL` (for HuggingFace and llamacpp API mode)
- `LLM_MODEL_PATH` (for llamacpp local mode)
- `LLM_MODE` (for llamacpp: `local` or `api`)

---

## Best Practices

1. **Use Internal LLM for Sensitive Data**
   - Set `USE_INTERNAL_LLM=true` for organizations with confidential documents
   - Run llama.cpp locally or on a secure internal server

2. **Configure Fallback for Reliability (Optional)**
   - Only enable if you want automatic failover behavior
   - Use a different provider or cheaper model
   - Test fallback regularly by temporarily disabling primary LLM

3. **Monitor LLM Usage**
   - Check which LLM type is being used via logs
   - If fallback is enabled, track fallback frequency to identify primary LLM issues
   - Verify `ENABLE_FALLBACK_LLM` setting at startup in logs

4. **Cost Optimization**
   - Use cheaper models for fallback (e.g., GPT-4 → GPT-3.5-turbo)
   - Set lower `LLM_MAX_TOKENS` for fallback to reduce costs
   - Consider using local llama.cpp for non-sensitive queries

5. **Security**
   - Never send highly confidential documents to external APIs
   - Use `INTERNAL_LLM_MIN_SECURITY_LEVEL=4` or `5` for strict security
   - Store API keys securely in environment variables, never in code

---

## Related Documentation

- [Settings Guide](./SETTINGS_GUIDE.md) - Complete configuration reference
- [Permissions Guide](./PERMISSIONS_GUIDE.md) - Security levels and RBAC
- [Retrieval Guide](./RETRIEVAL_GUIDE.md) - Document retrieval and filtering
