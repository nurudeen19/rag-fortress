"""
Application Settings Seeder - Keys Only

Seeds setting keys (without values) into the database.
Users provide values through the admin UI or values fallback to ENV → defaults.

Only includes settings that are actually used in the system.
"""

from sqlalchemy.orm import Session
from app.models.application_setting import ApplicationSetting
from app.core import get_logger


logger = get_logger(__name__)


def seed_application_settings(session: Session):
    """
    Seed application setting keys (no values).
    
    Values are provided by users via admin UI. If not set, the system
    falls back to ENV variables, then to defaults in config classes.
    """
    logger.info("Seeding application setting keys...")
    
    # Define settings: (key, data_type, description, category, is_mutable, is_sensitive)
    settings_to_seed = [
        # LLM Settings
        ("llm_provider", "string", "Primary LLM provider (openai, google, huggingface, ollama)", "llm", True, False),
        ("llm_model", "string", "LLM model name for selected provider", "llm", True, False),
        ("llm_temperature", "float", "LLM temperature (0.0-2.0)", "llm", True, False),
        ("llm_max_tokens", "integer", "Maximum tokens per LLM response", "llm", True, False),
        ("llm_timeout", "integer", "LLM request timeout in seconds", "llm", True, False),
        ("llm_enable_fallback", "boolean", "Enable fallback LLM on primary failure", "llm", True, False),
        
        # LLM Provider-Specific (API Keys are sensitive)
        ("openai_api_key", "string", "OpenAI API key (encrypted)", "llm", True, True),
        ("openai_model", "string", "OpenAI model name", "llm", True, False),
        ("openai_temperature", "float", "OpenAI temperature", "llm", True, False),
        ("openai_max_tokens", "integer", "OpenAI max tokens", "llm", True, False),
        
        ("google_api_key", "string", "Google Gemini API key (encrypted)", "llm", True, True),
        ("google_model", "string", "Google Gemini model name", "llm", True, False),
        ("google_temperature", "float", "Google temperature", "llm", True, False),
        ("google_max_tokens", "integer", "Google max tokens", "llm", True, False),
        
        ("hf_api_token", "string", "HuggingFace API token (encrypted)", "llm", True, True),
        ("hf_model", "string", "HuggingFace model name", "llm", True, False),
        ("hf_temperature", "float", "HuggingFace temperature", "llm", True, False),
        ("hf_max_tokens", "integer", "HuggingFace max tokens", "llm", True, False),
        
        # Fallback LLM
        ("fallback_llm_provider", "string", "Fallback LLM provider", "llm", True, False),
        ("fallback_llm_api_key", "string", "Fallback LLM API key (encrypted)", "llm", True, True),
        ("fallback_llm_model", "string", "Fallback LLM model", "llm", True, False),
        
        # Embedding Settings
        ("embedding_provider", "string", "Embedding provider (openai, google, huggingface, cohere, ollama)", "embedding", True, False),
        ("embedding_model", "string", "Embedding model name", "embedding", True, False),
        ("embedding_dimensions", "integer", "Embedding vector dimensions", "embedding", True, False),
        
        # Embedding Provider-Specific (API Keys are sensitive)
        ("openai_embedding_model", "string", "OpenAI embedding model", "embedding", True, False),
        ("google_embedding_model", "string", "Google embedding model", "embedding", True, False),
        ("hf_embedding_model", "string", "HuggingFace embedding model", "embedding", True, False),
        ("hf_embedding_device", "string", "HuggingFace device (cpu/cuda)", "embedding", True, False),
        ("cohere_api_key", "string", "Cohere API key (encrypted)", "embedding", True, True),
        ("cohere_embedding_model", "string", "Cohere embedding model", "embedding", True, False),
        
        # Vector Database Settings
        ("vector_db_provider", "string", "Vector DB provider (chroma, qdrant, pinecone, weaviate, milvus)", "vector_db", True, False),
        ("vector_store_collection_name", "string", "Vector store collection/index name", "vector_db", True, False),
        ("retriever_top_k", "integer", "Number of documents to retrieve", "vector_db", True, False),
        ("retriever_similarity_threshold", "float", "Minimum similarity threshold (0.0-1.0)", "vector_db", True, False),
        
        # Qdrant-specific
        ("qdrant_host", "string", "Qdrant server host", "vector_db", True, False),
        ("qdrant_port", "integer", "Qdrant HTTP port", "vector_db", True, False),
        ("qdrant_api_key", "string", "Qdrant API key (encrypted)", "vector_db", True, True),
        ("qdrant_prefer_grpc", "boolean", "Use gRPC for Qdrant", "vector_db", True, False),
        
        # Pinecone-specific
        ("pinecone_api_key", "string", "Pinecone API key (encrypted)", "vector_db", True, True),
        ("pinecone_environment", "string", "Pinecone environment", "vector_db", True, False),
        ("pinecone_index_name", "string", "Pinecone index name", "vector_db", True, False),
        
        # Cache Settings
        ("cache_enabled", "boolean", "Enable caching", "cache", True, False),
        ("cache_backend", "string", "Cache backend (redis, memory)", "cache", True, False),
        ("cache_key_prefix", "string", "Prefix for cache keys", "cache", True, False),
        ("cache_redis_host", "string", "Redis server host", "cache", True, False),
        ("cache_redis_port", "integer", "Redis server port", "cache", True, False),
        ("cache_redis_db", "integer", "Redis database number", "cache", True, False),
        ("cache_redis_password", "string", "Redis password (encrypted)", "cache", True, True),
        ("cache_ttl_default", "integer", "Default cache TTL (seconds)", "cache", True, False),
        ("cache_ttl_stats", "integer", "Stats cache TTL (seconds)", "cache", True, False),
        
        # Document Processing
        ("chunk_size", "integer", "Document chunk size", "document_processing", True, False),
        ("chunk_overlap", "integer", "Chunk overlap size", "document_processing", True, False),
        ("max_file_size_mb", "integer", "Max file upload size (MB)", "document_processing", True, False),
        ("batch_ingestion_size", "integer", "Batch size for ingestion", "document_processing", True, False),
        
        # Application Settings
        ("app_name", "string", "Application display name", "application", True, False),
        ("app_environment", "string", "Environment (dev/staging/prod)", "application", False, False),
        ("cors_allow_origins", "json", "CORS allowed origins", "application", True, False),
        ("debug_mode", "boolean", "Enable debug mode", "application", True, False),
        ("log_level", "string", "Log level (DEBUG/INFO/WARNING/ERROR)", "application", True, False),
        
        # Email Settings (SMTP)
        ("email_enabled", "boolean", "Enable email notifications", "email", True, False),
        ("smtp_server", "string", "SMTP server hostname", "email", True, False),
        ("smtp_port", "integer", "SMTP server port", "email", True, False),
        ("smtp_username", "string", "SMTP username", "email", True, False),
        ("smtp_password", "string", "SMTP password (encrypted)", "email", True, True),
        ("smtp_from_email", "string", "From email address", "email", True, False),
        ("smtp_from_name", "string", "From name", "email", True, False),
        ("smtp_use_tls", "boolean", "Use STARTTLS", "email", True, False),
        ("smtp_use_ssl", "boolean", "Use SSL/TLS", "email", True, False),
        
        # Email Token Expiry
        ("email_verification_token_expire_minutes", "integer", "Email verification token expiry (minutes)", "email", True, False),
        ("password_reset_token_expire_minutes", "integer", "Password reset token expiry (minutes)", "email", True, False),
        ("invite_token_expire_days", "integer", "Invite token expiry (days)", "email", True, False),
        
        # Email URLs
        ("frontend_url", "string", "Frontend base URL", "email", True, False),
        ("email_verification_url", "string", "Email verification URL", "email", True, False),
        ("password_reset_url", "string", "Password reset URL", "email", True, False),
        ("invite_url", "string", "Invite acceptance URL", "email", True, False),
        
        # Job System
        ("job_max_retries", "integer", "Max job retries", "jobs", True, False),
        ("job_retry_delay", "integer", "Job retry delay (seconds)", "jobs", True, False),
        ("job_cleanup_days", "integer", "Job record cleanup (days)", "jobs", True, False),
        
        # Security
        ("session_timeout_minutes", "integer", "Session timeout (minutes)", "security", True, False),
        ("max_login_attempts", "integer", "Max login attempts", "security", True, False),
        ("password_min_length", "integer", "Minimum password length", "security", True, False),
    ]
    
    count = 0
    skipped = 0
    
    for key, data_type, description, category, is_mutable, is_sensitive in settings_to_seed:
        existing = session.query(ApplicationSetting).filter_by(key=key).first()
        
        if existing:
            skipped += 1
            continue
        
        setting = ApplicationSetting(
            key=key,
            value=None,  # No default values - users provide via UI
            data_type=data_type,
            description=description,
            category=category,
            is_mutable=is_mutable
        )
        
        session.add(setting)
        count += 1
    
    session.commit()
    logger.info(f"✓ Seeded {count} setting keys ({skipped} already existed)")
    
    return count, skipped
