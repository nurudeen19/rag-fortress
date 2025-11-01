"""
Example usage of LLM fallback configuration
"""

from app.config import settings

# Example 1: Get primary LLM config
try:
    primary_config = settings.get_llm_config()
    print(f"Primary LLM: {primary_config['provider']} - {primary_config['model']}")
except Exception as e:
    print(f"Primary LLM failed: {e}")
    
    # Fall back to fallback LLM
    try:
        fallback_config = settings.get_fallback_llm_config()
        print(f"Using Fallback LLM: {fallback_config['provider']} - {fallback_config['model']}")
    except Exception as e:
        print(f"Fallback LLM also failed: {e}")


# Example 2: Using in a service with automatic fallback
def generate_response(prompt: str):
    """Generate response with automatic fallback"""
    
    # Try primary LLM
    try:
        llm_config = settings.get_llm_config()
        # Use llm_config to call the LLM...
        print(f"Calling {llm_config['provider']} with model {llm_config['model']}")
        # response = call_llm(prompt, llm_config)
        # return response
    except Exception as e:
        print(f"Primary LLM failed: {e}, trying fallback...")
        
        # Fall back to backup LLM
        try:
            fallback_config = settings.get_fallback_llm_config()
            print(f"Calling fallback {fallback_config['provider']} with model {fallback_config['model']}")
            # response = call_llm(prompt, fallback_config)
            # return response
        except Exception as e:
            print(f"Fallback LLM also failed: {e}")
            raise


# Example 3: Check if fallback is configured
print(f"\nFallback Provider: {settings.FALLBACK_LLM_PROVIDER or 'Default (HuggingFace small model)'}")
fallback = settings.get_fallback_llm_config()
print(f"Fallback Model: {fallback['model']}")
print(f"Fallback Max Tokens: {fallback['max_tokens']}")
