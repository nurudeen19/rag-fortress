"""
Quick test to verify settings configuration
"""
import sys
sys.path.insert(0, '/media/nurudeen/Storage/workspace/rag-fortress/backend')

try:
    from app.config import settings
    
    print("✓ Settings loaded successfully!")
    print(f"  App Name: {settings.APP_NAME}")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  LLM Provider: {settings.LLM_PROVIDER}")
    
    # Test get_llm_config() - will fail if API key not set, which is expected
    try:
        llm_config = settings.get_llm_config()
        print(f"\n✓ LLM Config retrieved:")
        print(f"  Model: {llm_config['model']}")
        print(f"  Temperature: {llm_config['temperature']}")
        print(f"  Max Tokens: {llm_config['max_tokens']}")
    except ValueError as e:
        print(f"\n⚠ LLM Config validation (expected if API key not set): {e}")
    
    print("\n✓ All settings validated successfully!")
    
except Exception as e:
    print(f"✗ Error loading settings: {e}")
    import traceback
    traceback.print_exc()
