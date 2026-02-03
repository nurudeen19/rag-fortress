"""
Application Settings Seeder - Keys Only

Seeds setting keys (without values) into the database.
Users provide values through the admin UI or values fallback to ENV → defaults.

Only includes settings that are actually used in the system.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application_setting import ApplicationSetting
from app.core import get_logger
from app.seeders.base import BaseSeed
from sqlalchemy import select


logger = get_logger(__name__)

class ApplicationSettingsSeeder(BaseSeed):
    """Seeder for application settings (keys only)."""
    """
    Seed application setting keys (no values).
    
    Values are provided by users via admin UI. If not set, the system
    falls back to ENV variables, then to defaults in config classes.
    """
    name = "application_settings"
    description = "Seed configurable application settings"
    required_tables = ["application_settings"]
    
    logger.info("Seeding application setting keys...")
    # Define settings: (key, data_type, description, category, is_mutable, is_sensitive)
   
    async def run(self, session: AsyncSession, **kwargs) -> None:
        """Run the seeder."""

        # Validate tables exist
        tables_exist, missing = await self.validate_tables_exist(session)
        if not tables_exist:
            return {
                "success": False,
                "message": f"Required tables missing: {', '.join(missing)}"
            }
        settings_to_seed = [
            # Primary LLM Settings (Consolidated)
            ("llm_provider", "string", "Primary LLM provider (openai, google, huggingface, llamacpp)", "llm", True, False),
            ("llm_api_key", "string", "LLM API key (encrypted)", "llm", True, True),
            ("llm_model", "string", "LLM model name", "llm", True, False),
            ("llm_temperature", "float", "LLM temperature (0.0-2.0)", "llm", True, False),
            ("llm_max_tokens", "integer", "Maximum tokens per LLM response", "llm", True, False),
            ("llm_timeout", "integer", "LLM request timeout in seconds", "llm", True, False),
            
            # LLM Provider-Specific Optional Fields (consolidated)
            ("llm_endpoint_url", "string", "LLM endpoint URL (HuggingFace/Llama.cpp)", "llm", True, False),
            ("llm_model_path", "string", "Path to local model file (Llama.cpp)", "llm", True, False),
            ("llm_mode", "string", "LLM mode (api or local) for Llama.cpp", "llm", True, False),
            ("llm_task", "string", "Task type (HuggingFace)", "llm", True, False),
            ("llm_context_size", "integer", "Context window size (Llama.cpp)", "llm", True, False),
            ("llm_n_threads", "integer", "CPU threads (Llama.cpp)", "llm", True, False),
            ("llm_n_batch", "integer", "Batch size (Llama.cpp)", "llm", True, False),
            
            # Fallback LLM Settings (Consolidated)
            ("fallback_llm_provider", "string", "Fallback LLM provider", "llm", True, False),
            ("fallback_llm_api_key", "string", "Fallback LLM API key (encrypted)", "llm", True, True),
            ("fallback_llm_model", "string", "Fallback LLM model", "llm", True, False),
            ("fallback_llm_temperature", "float", "Fallback LLM temperature", "llm", True, False),
            ("fallback_llm_max_tokens", "integer", "Fallback LLM max tokens", "llm", True, False),
            ("fallback_llm_endpoint_url", "string", "Fallback LLM endpoint URL", "llm", True, False),
            ("fallback_llm_timeout", "integer", "Fallback LLM timeout (seconds)", "llm", True, False),
            
            # Classifier LLM Settings (Consolidated)
            ("classifier_llm_provider", "string", "Classifier LLM provider", "llm", True, False),
            ("classifier_llm_api_key", "string", "Classifier LLM API key (encrypted)", "llm", True, True),
            ("classifier_llm_model", "string", "Classifier LLM model", "llm", True, False),
            ("classifier_llm_temperature", "float", "Classifier LLM temperature", "llm", True, False),
            ("classifier_llm_max_tokens", "integer", "Classifier LLM max tokens", "llm", True, False),
            ("classifier_llm_timeout", "integer", "Classifier LLM timeout (seconds)", "llm", True, False),
            
            # Embedding Settings (Consolidated)
            ("embedding_provider", "string", "Embedding provider (openai, google, huggingface, cohere)", "embedding", True, False),
            ("embedding_api_key", "string", "Embedding API key (encrypted)", "embedding", True, True),
            ("embedding_model", "string", "Embedding model name", "embedding", True, False),
            ("embedding_dimensions", "integer", "Embedding vector dimensions", "embedding", True, False),
            ("embedding_device", "string", "Embedding device (cpu/cuda) - HuggingFace only", "embedding", True, False),
            ("embedding_task_type", "string", "Embedding task type - Google only (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY)", "embedding", True, False),
            ("embedding_input_type", "string", "Embedding input type - Cohere only (search_document, search_query)", "embedding", True, False),
            
            # Vector Database Settings (Consolidated)
            ("vector_db_provider", "string", "Vector DB provider (faiss, chroma, qdrant, pinecone, weaviate, milvus)", "vector_db", True, False),
            ("vector_db_url", "string", "Vector DB connection URL", "vector_db", True, False),
            ("vector_db_host", "string", "Vector DB server host", "vector_db", True, False),
            ("vector_db_port", "integer", "Vector DB server port", "vector_db", True, False),
            ("vector_db_api_key", "string", "Vector DB API key (encrypted)", "vector_db", True, True),
            ("vector_db_username", "string", "Vector DB username", "vector_db", True, False),
            ("vector_db_password", "string", "Vector DB password (encrypted)", "vector_db", True, True),
            ("vector_db_grpc_port", "integer", "Vector DB gRPC port (Qdrant)", "vector_db", True, False),
            ("vector_db_prefer_grpc", "boolean", "Use gRPC for Vector DB (Qdrant)", "vector_db", True, False),
            ("vector_db_index_name", "string", "Vector DB index/collection name", "vector_db", True, False),
            ("vector_db_class_name", "string", "Vector DB class name (Weaviate)", "vector_db", True, False),
            ("vector_db_environment", "string", "Vector DB environment (Pinecone)", "vector_db", True, False),
            ("vector_store_collection_name", "string", "Vector store collection/index name", "vector_db", True, False),
            
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
            ("app_description", "string", "Application description used in branding", "application", True, False),
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
            
            # RAG System Prompts
            ("rag_system_prompt", "string", "System prompt for RAG responses - instructs the LLM on how to answer questions from the knowledge base", "prompts", True, False),
            ("retrieval_no_context_message", "string", "Response when no relevant documents found in knowledge base", "prompts", True, False),
        ]
    
        count = 0
        skipped = 0
        
        for key, data_type, description, category, is_mutable, is_sensitive in settings_to_seed:
            stmt = select(ApplicationSetting).where(ApplicationSetting.key == key)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                skipped += 1
                continue
            
            setting = ApplicationSetting(
                key=key,
                value=None,  # No default values - users provide via UI
                data_type=data_type,
                description=description,
                category=category,
                is_mutable=is_mutable,
                is_sensitive=is_sensitive,
            )
            
            session.add(setting)
            count += 1
        
        try:
            await session.commit()
            message = f"Seeded {count} application settings ({skipped} already existed)"
            logger.info(f"✓ {message}")
            return {"success": True, "message": message, "created": count, "skipped": skipped}
        except Exception as e:
            await session.rollback()
            error_msg = f"Failed to seed application settings: {e}"
            logger.error(f"✗ {error_msg}")
            return {"success": False, "message": error_msg}
        logger.info(f"✓ Seeded {count} setting keys ({skipped} already existed)")
        
        return count, skipped





