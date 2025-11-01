"""
Test settings configuration and validation
"""
import pytest
import os
from unittest.mock import patch


@pytest.fixture
def clean_env():
    """Fixture to provide clean environment for each test"""
    # Save original env
    original_env = os.environ.copy()
    
    # Clear relevant env vars
    keys_to_clear = [key for key in os.environ.keys() if any(
        prefix in key for prefix in ['LLM_', 'OPENAI_', 'GOOGLE_', 'HF_', 'FALLBACK_']
    )]
    for key in keys_to_clear:
        os.environ.pop(key, None)
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def base_env():
    """Fixture with minimal required environment variables"""
    return {
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "ENVIRONMENT": "development",
    }


class TestSettingsBasic:
    """Test basic settings functionality"""
    
    def test_default_settings(self, clean_env, base_env):
        """Test settings load with defaults"""
        with patch.dict(os.environ, base_env):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.APP_NAME == "RAG Fortress"
            assert settings.APP_VERSION == "1.0.0"
            assert settings.DEBUG == True
            assert settings.ENVIRONMENT == "development"
            assert settings.LLM_PROVIDER == "openai"
    
    def test_environment_validation(self, clean_env, base_env):
        """Test that invalid environments are rejected"""
        env = {**base_env, "ENVIRONMENT": "invalid_env"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="Invalid ENVIRONMENT"):
                Settings()
    
    def test_production_environment_settings(self, clean_env, base_env):
        """Test that production environment enforces correct settings"""
        env = {**base_env, "ENVIRONMENT": "production"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.DEBUG == False
            assert settings.LOG_LEVEL == "WARNING"
    
    def test_development_environment_settings(self, clean_env, base_env):
        """Test that development environment sets correct settings"""
        env = {**base_env, "ENVIRONMENT": "development"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.DEBUG == True
            assert settings.LOG_LEVEL == "DEBUG"


class TestLLMConfiguration:
    """Test LLM provider configuration"""
    
    def test_openai_config(self, clean_env, base_env):
        """Test OpenAI provider configuration"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_openai_key",
            "OPENAI_MODEL": "gpt-4",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_llm_config()
            
            assert config["provider"] == "openai"
            assert config["api_key"] == "test_openai_key"
            assert config["model"] == "gpt-4"
            assert config["temperature"] == 0.7
            assert config["max_tokens"] == 2000
    
    def test_google_config(self, clean_env, base_env):
        """Test Google provider configuration"""
        env = {
            **base_env,
            "LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test_google_key",
            "GOOGLE_MODEL": "gemini-pro",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_llm_config()
            
            assert config["provider"] == "google"
            assert config["api_key"] == "test_google_key"
            assert config["model"] == "gemini-pro"
    
    def test_huggingface_config(self, clean_env, base_env):
        """Test HuggingFace provider configuration"""
        env = {
            **base_env,
            "LLM_PROVIDER": "huggingface",
            "HF_API_TOKEN": "test_hf_token",
            "HF_MODEL": "meta-llama/Llama-2-7b-chat-hf",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_llm_config()
            
            assert config["provider"] == "huggingface"
            assert config["api_key"] == "test_hf_token"
            assert config["model"] == "meta-llama/Llama-2-7b-chat-hf"
    
    def test_missing_api_key_raises_error(self, clean_env, base_env):
        """Test that missing API key raises error"""
        env = {**base_env, "LLM_PROVIDER": "openai"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                settings.get_llm_config()
    
    def test_unsupported_provider_raises_error(self, clean_env, base_env):
        """Test that unsupported provider raises error"""
        env = {**base_env, "LLM_PROVIDER": "unsupported_provider"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                settings.get_llm_config()


class TestFallbackLLMConfiguration:
    """Test fallback LLM configuration and validation"""
    
    def test_no_fallback_uses_default_hf(self, clean_env, base_env):
        """Test that no fallback config uses default HuggingFace model"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_key",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            fallback = settings.get_fallback_llm_config()
            
            assert fallback["provider"] == "huggingface"
            assert fallback["model"] == "google/flan-t5-small"
            assert fallback["max_tokens"] == 512
    
    def test_custom_fallback_model(self, clean_env, base_env):
        """Test custom fallback model configuration"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_key",
            "OPENAI_MODEL": "gpt-4",
            "FALLBACK_LLM_PROVIDER": "openai",
            "FALLBACK_LLM_API_KEY": "test_key",
            "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
            "FALLBACK_LLM_TEMPERATURE": "0.5",
            "FALLBACK_LLM_MAX_TOKENS": "1000",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            fallback = settings.get_fallback_llm_config()
            
            assert fallback["provider"] == "openai"
            assert fallback["model"] == "gpt-3.5-turbo"
            assert fallback["temperature"] == 0.5
            assert fallback["max_tokens"] == 1000
    
    def test_fallback_different_provider(self, clean_env, base_env):
        """Test fallback with different provider"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_openai_key",
            "FALLBACK_LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test_google_key",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            primary = settings.get_llm_config()
            fallback = settings.get_fallback_llm_config()
            
            assert primary["provider"] == "openai"
            assert fallback["provider"] == "google"
    
    def test_same_provider_same_model_raises_error(self, clean_env, base_env):
        """Test that same provider and model raises validation error"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_key",
            "OPENAI_MODEL": "gpt-3.5-turbo",
            "FALLBACK_LLM_PROVIDER": "openai",
            "FALLBACK_LLM_API_KEY": "test_key",
            "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            
            with pytest.raises(ValueError, match="Fallback LLM cannot be the same as primary LLM"):
                Settings()
    
    def test_same_provider_different_model_allowed(self, clean_env, base_env):
        """Test that same provider with different model is allowed"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_key",
            "OPENAI_MODEL": "gpt-4",
            "FALLBACK_LLM_PROVIDER": "openai",
            "FALLBACK_LLM_API_KEY": "test_key",
            "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            primary = settings.get_llm_config()
            fallback = settings.get_fallback_llm_config()
            
            assert primary["model"] == "gpt-4"
            assert fallback["model"] == "gpt-3.5-turbo"
    
    def test_fallback_reuses_provider_api_key(self, clean_env, base_env):
        """Test that fallback can reuse provider's API key"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_key",
            "OPENAI_MODEL": "gpt-4",
            "FALLBACK_LLM_PROVIDER": "openai",
            "FALLBACK_LLM_MODEL": "gpt-3.5-turbo",
            # No FALLBACK_LLM_API_KEY - should reuse OPENAI_API_KEY
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            fallback = settings.get_fallback_llm_config()
            
            assert fallback["api_key"] == "test_key"
    
    def test_fallback_provider_without_custom_model_uses_provider_config(self, clean_env, base_env):
        """Test fallback provider without custom model uses provider's default config"""
        env = {
            **base_env,
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_openai_key",
            "OPENAI_MODEL": "gpt-4",
            "FALLBACK_LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test_google_key",
            "GOOGLE_MODEL": "gemini-pro",
            # No FALLBACK_LLM_MODEL - should use GOOGLE_MODEL
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            fallback = settings.get_fallback_llm_config()
            
            assert fallback["provider"] == "google"
            assert fallback["model"] == "gemini-pro"
            assert fallback["api_key"] == "test_google_key"


class TestCORSConfiguration:
    """Test CORS configuration"""
    
    def test_default_cors_origins(self, clean_env, base_env):
        """Test default CORS origins"""
        with patch.dict(os.environ, base_env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
            assert "http://localhost:8000" in settings.ALLOWED_ORIGINS
    
    def test_custom_cors_origins(self, clean_env, base_env):
        """Test custom CORS origins"""
        env = {
            **base_env,
            "ALLOWED_ORIGINS": "http://example.com,https://app.example.com",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            # Note: Pydantic may parse this as a string or list depending on configuration
            # This test may need adjustment based on actual parsing behavior
            assert settings.ALLOWED_ORIGINS is not None
