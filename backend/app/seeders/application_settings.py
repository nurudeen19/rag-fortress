"""
Application settings seeder.

Seeds configurable application settings (non-critical) into the database.
Critical settings like database credentials remain in .env only.
"""

from sqlalchemy.orm import Session
from app.models.application_setting import ApplicationSetting
from app.core import get_logger


logger = get_logger(__name__)


def seed_application_settings(session: Session):
    """
    Seed configurable application settings.
    
    These settings can be modified through the admin UI without requiring
    application restart. Critical settings (database, security) remain
    in .env files only.
    """
    logger.info("Seeding application settings...")
    
    # Define settings to seed (key, value, data_type, description, category, is_mutable)
    settings_to_seed = [
        # LLM Settings
        ("llm_provider", "openai", "string", "Primary LLM provider (openai, google, huggingface)", "llm", True),
        ("openai_model", "gpt-4o-mini", "string", "OpenAI model name", "llm", True),
        ("openai_temperature", "0.7", "float", "OpenAI temperature (0.0-2.0)", "llm", True),
        ("openai_max_tokens", "1000", "integer", "OpenAI max tokens per response", "llm", True),
        ("google_model", "gemini-pro", "string", "Google Gemini model name", "llm", True),
        ("google_temperature", "0.7", "float", "Google temperature (0.0-2.0)", "llm", True),
        ("google_max_tokens", "1000", "integer", "Google max tokens per response", "llm", True),
        ("hf_model", "meta-llama/Llama-2-7b-chat-hf", "string", "HuggingFace model name", "llm", True),
        ("hf_temperature", "0.7", "float", "HuggingFace temperature (0.0-2.0)", "llm", True),
        ("hf_max_tokens", "1000", "integer", "HuggingFace max tokens per response", "llm", True),
        ("fallback_llm_provider", "", "string", "Fallback LLM provider (optional)", "llm", True),
        
        # Embedding Settings
        ("embedding_provider", "huggingface", "string", "Embedding provider (openai, google, huggingface, cohere)", "embedding", True),
        ("openai_embedding_model", "text-embedding-3-small", "string", "OpenAI embedding model", "embedding", True),
        ("google_embedding_model", "gemini-embedding-001", "string", "Google embedding model", "embedding", True),
        ("hf_embedding_model", "sentence-transformers/all-MiniLM-L6-v2", "string", "HuggingFace embedding model", "embedding", True),
        ("hf_embedding_device", "cpu", "string", "Device for HuggingFace embeddings (cpu, cuda)", "embedding", True),
        ("cohere_embedding_model", "embed-english-v3.0", "string", "Cohere embedding model", "embedding", True),
        
        # Vector Database Settings
        ("vector_db_provider", "qdrant", "string", "Vector database provider (chroma, qdrant, pinecone, weaviate, milvus)", "vector_db", True),
        ("vector_store_collection_name", "rag_documents", "string", "Vector store collection/index name", "vector_db", True),
        ("retriever_top_k", "5", "integer", "Number of documents to retrieve", "vector_db", True),
        ("qdrant_host", "localhost", "string", "Qdrant server host", "vector_db", True),
        ("qdrant_port", "6333", "integer", "Qdrant HTTP port", "vector_db", True),
        ("qdrant_collection_name", "rag_documents", "string", "Qdrant collection name", "vector_db", True),
        ("qdrant_prefer_grpc", "false", "boolean", "Use gRPC for Qdrant connections", "vector_db", True),
        
        # Cache Settings
        ("cache_enabled", "true", "boolean", "Enable caching", "cache", True),
        ("cache_backend", "memory", "string", "Cache backend (redis, memory)", "cache", True),
        ("cache_key_prefix", "rag_fortress", "string", "Prefix for all cache keys", "cache", True),
        ("cache_redis_host", "localhost", "string", "Redis server host", "cache", True),
        ("cache_redis_port", "6379", "integer", "Redis server port", "cache", True),
        ("cache_redis_db", "0", "integer", "Redis database number", "cache", True),
        ("cache_ttl_default", "300", "integer", "Default cache TTL in seconds (5 minutes)", "cache", True),
        ("cache_ttl_stats", "60", "integer", "Stats cache TTL in seconds (1 minute)", "cache", True),
        ("cache_ttl_config", "3600", "integer", "Config cache TTL in seconds (1 hour)", "cache", True),
        ("cache_ttl_user_data", "300", "integer", "User data cache TTL in seconds (5 minutes)", "cache", True),
        ("cache_ttl_session", "1800", "integer", "Session cache TTL in seconds (30 minutes)", "cache", True),
        
        # Document Processing Settings
        ("chunk_size", "1000", "integer", "Default chunk size for document splitting", "document_processing", True),
        ("chunk_overlap", "200", "integer", "Overlap between chunks", "document_processing", True),
        ("max_file_size_mb", "50", "integer", "Maximum file upload size in MB", "document_processing", True),
        ("batch_ingestion_size", "100", "integer", "Batch size for vector store ingestion", "document_processing", True),
        
        # Application Settings
        ("app_name", "RAG Fortress", "string", "Application display name", "application", True),
        ("app_environment", "development", "string", "Environment (development, staging, production)", "application", False),
        ("cors_allow_origins", '["http://localhost:5173","http://localhost:3000"]', "json", "CORS allowed origins", "application", True),
        ("debug_mode", "false", "boolean", "Enable debug mode", "application", True),
        ("log_level", "INFO", "string", "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", "application", True),
        
        # Job System Settings
        ("job_max_retries", "3", "integer", "Maximum retries for failed jobs", "jobs", True),
        ("job_retry_delay", "300", "integer", "Delay between job retries in seconds", "jobs", True),
        ("job_cleanup_days", "30", "integer", "Days to keep completed job records", "jobs", True),
        
        # Email Settings (non-sensitive)
        ("email_from_name", "RAG Fortress", "string", "Sender name for emails", "email", True),
        ("email_enabled", "false", "boolean", "Enable email notifications", "email", True),
        
        # Security Settings (non-sensitive)
        ("session_timeout_minutes", "30", "integer", "User session timeout in minutes", "security", True),
        ("max_login_attempts", "5", "integer", "Maximum failed login attempts before lockout", "security", True),
        ("password_min_length", "8", "integer", "Minimum password length", "security", True),
    ]
    
    count = 0
    skipped = 0
    
    for key, value, data_type, description, category, is_mutable in settings_to_seed:
        # Check if setting already exists
        existing = session.query(ApplicationSetting).filter_by(key=key).first()
        
        if existing:
            logger.debug(f"Setting '{key}' already exists, skipping")
            skipped += 1
            continue
        
        # Create new setting
        setting = ApplicationSetting(
            key=key,
            value=value,
            data_type=data_type,
            description=description,
            category=category,
            is_mutable=is_mutable
        )
        session.add(setting)
        count += 1
        logger.debug(f"Created setting: {key} = {value}")
    
    try:
        session.commit()
        logger.info(f"✓ Seeded {count} application settings ({skipped} already existed)")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Failed to seed application settings: {e}")
        raise


def run_seeder():
    """Entry point for running seeder standalone."""
    from app.core.database_sync import get_sync_session
    
    logger.info("Starting application settings seeder...")
    
    session = get_sync_session()
    try:
        seed_application_settings(session)
        logger.info("Application settings seeder completed successfully")
    finally:
        session.close()


if __name__ == "__main__":
    run_seeder()

