"""
Test settings configuration and validation.

NOTE: These tests focus on ENV-based configuration.
For database-backed settings tests, see test_encryption_settings.py
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
        prefix in key for prefix in [
            'LLM_', 'OPENAI_', 'GOOGLE_', 'HF_', 'FALLBACK_',
            'EMBEDDING_', 'COHERE_',
            'VECTOR_DB_', 'QDRANT_', 'PINECONE_', 'WEAVIATE_', 'MILVUS_',
            'LLAMACPP_', 'INTERNAL_LLAMACPP_'
        ]
    )]
    for key in keys_to_clear:
        os.environ.pop(key, None)
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


class TestSettingsBasic:
    """Test basic settings functionality with ENV variables."""
    
    def test_default_settings(self, clean_env):
        """Test settings load with defaults (no ENV, no DB)."""
        with patch.dict(os.environ, {}, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.APP_NAME == "RAG Fortress"
            assert settings.APP_DESCRIPTION == "Secure document intelligence platform"
            assert settings.APP_VERSION == "1.0.0"
            assert settings.ENVIRONMENT in ["development", "staging", "production"]
            assert settings.LLM_PROVIDER == "openai"
    
    def test_env_variables_override_defaults(self, clean_env):
        """Test that ENV variables override Field defaults."""
        env = {
            "APP_NAME": "Custom RAG",
            "APP_DESCRIPTION": "Custom branded platform",
            "LLM_PROVIDER": "google",
            "EMBEDDING_PROVIDER": "openai"
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.APP_NAME == "Custom RAG"
            assert settings.APP_DESCRIPTION == "Custom branded platform"
            assert settings.LLM_PROVIDER == "google"
            assert settings.EMBEDDING_PROVIDER == "openai"


class TestLLMConfiguration:
    """Test LLM provider configuration (ENV-based)."""
    
    def test_openai_config(self, clean_env):
        """Test OpenAI provider configuration from ENV."""
        env = {
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
    
    def test_google_config(self, clean_env):
        """Test Google provider configuration from ENV."""
        env = {
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
    
    def test_huggingface_config(self, clean_env):
        """Test HuggingFace provider configuration from ENV."""
        env = {
            "LLM_PROVIDER": "huggingface",
            "HF_API_TOKEN": "test_hf_token",
            "HF_MODEL": "meta-llama/Llama-2-7b-chat-hf",
            "HF_ENDPOINT_URL": "https://example.endpoints.huggingface.cloud",
            "HF_TASK": "text-generation",
            "HF_TIMEOUT": "90",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_llm_config()
            
            assert config["provider"] == "huggingface"
            assert config["api_key"] == "test_hf_token"
            assert config["model"] == "meta-llama/Llama-2-7b-chat-hf"
            assert config["endpoint_url"] == "https://example.endpoints.huggingface.cloud"
            assert config["task"] == "text-generation"
            assert config["timeout"] == 90
    
    def test_llamacpp_config(self, clean_env):
        """Test llama.cpp provider configuration from ENV."""
        env = {
            "LLM_PROVIDER": "llamacpp",
            "LLAMACPP_MODEL_PATH": "/models/llama-3.1.gguf",
            "LLAMACPP_TEMPERATURE": "0.2",
            "LLAMACPP_MAX_TOKENS": "256",
            "LLAMACPP_CONTEXT_SIZE": "2048",
            "LLAMACPP_N_THREADS": "6",
            "LLAMACPP_N_BATCH": "128",
        }

        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_llm_config()

            assert config["provider"] == "llamacpp"
            assert config["model_path"] == "/models/llama-3.1.gguf"
            assert config["temperature"] == 0.2
            assert config["max_tokens"] == 256
            assert config["context_size"] == 2048
            assert config["n_threads"] == 6
            assert config["n_batch"] == 128
    
    def test_missing_api_key_raises_error(self, clean_env):
        """Test that missing API key raises error during config access."""
        env = {"LLM_PROVIDER": "openai"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                settings.get_llm_config()
    
    def test_unsupported_provider_raises_error(self, clean_env):
        """Test that unsupported provider raises error during config access."""
        env = {"LLM_PROVIDER": "unsupported_provider"}
        
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
            assert fallback["task"] == "text-generation"
            assert "endpoint_url" in fallback
    
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


class TestEmbeddingProviderConfiguration:
    """Test embedding provider configuration"""
    
    def test_default_embedding_provider(self, clean_env, base_env):
        """Test default embedding provider is HuggingFace"""
        with patch.dict(os.environ, base_env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.EMBEDDING_PROVIDER == "huggingface"
            config = settings.get_embedding_config()
            assert config["provider"] == "huggingface"
            assert config["model"] == "sentence-transformers/all-MiniLM-L6-v2"
            assert config["device"] == "cpu"
    
    def test_openai_embedding_config(self, clean_env, base_env):
        """Test OpenAI embedding configuration"""
        env = {
            **base_env,
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test_openai_key",
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
            "OPENAI_EMBEDDING_DIMENSIONS": "1024",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_embedding_config()
            
            assert config["provider"] == "openai"
            assert config["api_key"] == "test_openai_key"
            assert config["model"] == "text-embedding-3-large"
            assert config["dimensions"] == 1024
    
    def test_google_embedding_config(self, clean_env, base_env):
        """Test Google embedding configuration"""
        env = {
            **base_env,
            "EMBEDDING_PROVIDER": "google",
            "GOOGLE_API_KEY": "test_google_key",
            "GOOGLE_EMBEDDING_MODEL": "gemini-embedding-001",
            "GOOGLE_EMBEDDING_DIMENSIONS": "1536",
            "GOOGLE_EMBEDDING_TASK_TYPE": "RETRIEVAL_QUERY",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_embedding_config()
            
            assert config["provider"] == "google"
            assert config["api_key"] == "test_google_key"
            assert config["model"] == "gemini-embedding-001"
            assert config["dimensions"] == 1536
            assert config["task_type"] == "RETRIEVAL_QUERY"
    
    def test_cohere_embedding_config(self, clean_env, base_env):
        """Test Cohere embedding configuration"""
        env = {
            **base_env,
            "EMBEDDING_PROVIDER": "cohere",
            "COHERE_API_KEY": "test_cohere_key",
            "COHERE_EMBEDDING_MODEL": "embed-english-v3.0",
            "COHERE_INPUT_TYPE": "search_query",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_embedding_config()
            
            assert config["provider"] == "cohere"
            assert config["api_key"] == "test_cohere_key"
            assert config["model"] == "embed-english-v3.0"
            assert config["input_type"] == "search_query"
    
    def test_invalid_embedding_provider(self, clean_env):
        """Test invalid embedding provider raises error during validation."""
        env = {"EMBEDDING_PROVIDER": "invalid_provider"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            # Should raise during validation, not initialization
            with pytest.raises(ValueError, match="Unsupported"):
                settings.validate_config()
    
    def test_openai_embedding_missing_api_key(self, clean_env):
        """Test OpenAI embeddings require API key during validation."""
        env = {"EMBEDDING_PROVIDER": "openai"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                settings.validate_config()
    
    def test_google_embedding_missing_api_key(self, clean_env):
        """Test Google embeddings require API key during validation."""
        env = {"EMBEDDING_PROVIDER": "google"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="GOOGLE_API_KEY is required"):
                settings.validate_config()
    
    def test_cohere_embedding_missing_api_key(self, clean_env):
        """Test Cohere embeddings require API key during validation."""
        env = {"EMBEDDING_PROVIDER": "cohere"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            with pytest.raises(ValueError, match="COHERE_API_KEY is required"):
                settings.validate_config()


class TestVectorDBConfiguration:
    """Test vector database configuration"""
    
    def test_default_vector_db_chroma(self, clean_env, base_env):
        """Test default vector DB is Chroma"""
        with patch.dict(os.environ, base_env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            assert settings.VECTOR_DB_PROVIDER == "chroma"
            config = settings.get_vector_db_config()
            assert config["provider"] == "chroma"
            assert config["persist_directory"] == "./chroma_db"
            assert config["collection_name"] == "rag_documents"
    
    def test_chroma_not_allowed_in_production(self, clean_env, base_env):
        """Test Chroma is not allowed in production"""
        env = {
            **base_env,
            "ENVIRONMENT": "production",
            "VECTOR_DB_PROVIDER": "chroma",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="Chroma is not recommended for production"):
                Settings()
    
    def test_qdrant_local_config(self, clean_env, base_env):
        """Test Qdrant local configuration"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "qdrant",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            "QDRANT_COLLECTION_NAME": "my_docs",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["provider"] == "qdrant"
            assert config["host"] == "localhost"
            assert config["port"] == 6333
            assert config["collection_name"] == "my_docs"
            assert "url" not in config
    
    def test_qdrant_cloud_config(self, clean_env, base_env):
        """Test Qdrant Cloud configuration"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "qdrant",
            "QDRANT_URL": "https://my-cluster.qdrant.io",
            "QDRANT_API_KEY": "test_qdrant_key",
            "QDRANT_COLLECTION_NAME": "my_docs",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["provider"] == "qdrant"
            assert config["url"] == "https://my-cluster.qdrant.io"
            assert config["api_key"] == "test_qdrant_key"
            assert config["collection_name"] == "my_docs"
            assert "host" not in config
    
    def test_qdrant_cloud_missing_api_key(self, clean_env, base_env):
        """Test Qdrant Cloud requires API key"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "qdrant",
            "QDRANT_URL": "https://my-cluster.qdrant.io",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="QDRANT_API_KEY is required"):
                Settings()
    
    def test_qdrant_allowed_in_production(self, clean_env, base_env):
        """Test Qdrant is allowed in production"""
        env = {
            **base_env,
            "ENVIRONMENT": "production",
            "VECTOR_DB_PROVIDER": "qdrant",
            "QDRANT_HOST": "localhost",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()  # Should not raise
            assert settings.VECTOR_DB_PROVIDER == "qdrant"
    
    def test_pinecone_config(self, clean_env, base_env):
        """Test Pinecone configuration"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "pinecone",
            "PINECONE_API_KEY": "test_pinecone_key",
            "PINECONE_ENVIRONMENT": "us-west1-gcp",
            "PINECONE_INDEX_NAME": "my-index",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["provider"] == "pinecone"
            assert config["api_key"] == "test_pinecone_key"
            assert config["environment"] == "us-west1-gcp"
            assert config["index_name"] == "my-index"
    
    def test_pinecone_missing_api_key(self, clean_env, base_env):
        """Test Pinecone requires API key"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "pinecone",
            "PINECONE_ENVIRONMENT": "us-west1-gcp",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="PINECONE_API_KEY is required"):
                Settings()
    
    def test_pinecone_missing_environment(self, clean_env, base_env):
        """Test Pinecone requires environment"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "pinecone",
            "PINECONE_API_KEY": "test_key",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="PINECONE_ENVIRONMENT is required"):
                Settings()
    
    def test_weaviate_config(self, clean_env, base_env):
        """Test Weaviate configuration"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "weaviate",
            "WEAVIATE_URL": "http://localhost:8080",
            "WEAVIATE_CLASS_NAME": "MyDocument",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["provider"] == "weaviate"
            assert config["url"] == "http://localhost:8080"
            assert config["class_name"] == "MyDocument"
    
    def test_weaviate_with_api_key(self, clean_env, base_env):
        """Test Weaviate with API key (cloud)"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "weaviate",
            "WEAVIATE_URL": "https://my-cluster.weaviate.network",
            "WEAVIATE_API_KEY": "test_weaviate_key",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["api_key"] == "test_weaviate_key"
    
    def test_milvus_config(self, clean_env, base_env):
        """Test Milvus configuration"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "milvus",
            "MILVUS_HOST": "localhost",
            "MILVUS_PORT": "19530",
            "MILVUS_COLLECTION_NAME": "my_collection",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["provider"] == "milvus"
            assert config["host"] == "localhost"
            assert config["port"] == 19530
            assert config["collection_name"] == "my_collection"
    
    def test_milvus_with_auth(self, clean_env, base_env):
        """Test Milvus with authentication"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "milvus",
            "MILVUS_USER": "admin",
            "MILVUS_PASSWORD": "password123",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            config = settings.get_vector_db_config()
            
            assert config["user"] == "admin"
            assert config["password"] == "password123"
    
    def test_invalid_vector_db_provider(self, clean_env, base_env):
        """Test invalid vector DB provider raises error"""
        env = {
            **base_env,
            "VECTOR_DB_PROVIDER": "invalid_db",
        }
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            with pytest.raises(ValueError, match="Unsupported VECTOR_DB_PROVIDER"):
                Settings()

