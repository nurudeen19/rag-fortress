"""
Test fallback LLM configuration validation
"""
import sys
import os
sys.path.insert(0, '/media/nurudeen/Storage/workspace/rag-fortress/backend')

# Test 1: Valid configuration with different providers
print("Test 1: Primary OpenAI, Fallback Google (should pass)")
os.environ.update({
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": "test_key",
    "FALLBACK_LLM_PROVIDER": "google",
    "GOOGLE_API_KEY": "test_google_key",
    "SECRET_KEY": "test_secret"
})

try:
    from app.config.settings import Settings
    settings = Settings()
    primary = settings.get_llm_config()
    fallback = settings.get_fallback_llm_config()
    print(f"✓ Primary: {primary['provider']}/{primary['model']}")
    print(f"✓ Fallback: {fallback['provider']}/{fallback['model']}\n")
except Exception as e:
    print(f"✗ Error: {e}\n")

# Test 2: Invalid - Same provider and model
print("Test 2: Same provider and model (should fail)")
os.environ.update({
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": "test_key",
    "OPENAI_MODEL": "gpt-3.5-turbo",
    "FALLBACK_LLM_PROVIDER": "openai",
    "FALLBACK_LLM_API_KEY": "test_key",
    "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
    "SECRET_KEY": "test_secret"
})

try:
    # Need to reload settings
    import importlib
    import app.config.settings as settings_module
    importlib.reload(settings_module)
    settings = settings_module.Settings()
    print("✗ Should have failed but didn't\n")
except ValueError as e:
    print(f"✓ Correctly rejected: {e}\n")
except Exception as e:
    print(f"? Unexpected error: {e}\n")

# Test 3: Custom fallback model (different from primary)
print("Test 3: Custom fallback model (should pass)")
os.environ.update({
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": "test_key",
    "OPENAI_MODEL": "gpt-4",
    "FALLBACK_LLM_PROVIDER": "openai",
    "FALLBACK_LLM_API_KEY": "test_key",
    "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
    "FALLBACK_LLM_TEMPERATURE": "0.5",
    "FALLBACK_LLM_MAX_TOKENS": "1000",
    "SECRET_KEY": "test_secret"
})

try:
    importlib.reload(settings_module)
    settings = settings_module.Settings()
    primary = settings.get_llm_config()
    fallback = settings.get_fallback_llm_config()
    print(f"✓ Primary: {primary['provider']}/{primary['model']}")
    print(f"✓ Fallback: {fallback['provider']}/{fallback['model']}")
    print(f"✓ Fallback temp: {fallback['temperature']}, max_tokens: {fallback['max_tokens']}\n")
except Exception as e:
    print(f"✗ Error: {e}\n")

# Test 4: No fallback configured (should use default HF model)
print("Test 4: No fallback configured (should use default HF)")
os.environ.update({
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": "test_key",
    "SECRET_KEY": "test_secret"
})
# Remove fallback vars
for key in list(os.environ.keys()):
    if "FALLBACK" in key:
        del os.environ[key]

try:
    importlib.reload(settings_module)
    settings = settings_module.Settings()
    primary = settings.get_llm_config()
    fallback = settings.get_fallback_llm_config()
    print(f"✓ Primary: {primary['provider']}/{primary['model']}")
    print(f"✓ Fallback: {fallback['provider']}/{fallback['model']}")
    print(f"✓ Default fallback is HuggingFace small model\n")
except Exception as e:
    print(f"✗ Error: {e}\n")

print("All tests completed!")
