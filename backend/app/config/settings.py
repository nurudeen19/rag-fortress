from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import Field

class Settings(BaseSettings):
    # App
    APP_NAME: str = Field("RAG Fortress", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(True, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")

    # LLM Provider selection
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    
    # Fallback LLM configuration (optional, defaults to HuggingFace small model)
    FALLBACK_LLM_PROVIDER: Optional[str] = Field(None, env="FALLBACK_LLM_PROVIDER")
    FALLBACK_LLM_API_KEY: Optional[str] = Field(None, env="FALLBACK_LLM_API_KEY")
    FALLBACK_LLM_MODEL: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL")
    FALLBACK_LLM_TEMPERATURE: Optional[float] = Field(None, env="FALLBACK_LLM_TEMPERATURE")
    FALLBACK_LLM_MAX_TOKENS: Optional[int] = Field(None, env="FALLBACK_LLM_MAX_TOKENS")

    # OpenAI Provider
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(0.7, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(2000, env="OPENAI_MAX_TOKENS")

    # Google Provider
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    GOOGLE_MODEL: str = Field("gemini-pro", env="GOOGLE_MODEL")
    GOOGLE_TEMPERATURE: float = Field(0.7, env="GOOGLE_TEMPERATURE")
    GOOGLE_MAX_TOKENS: int = Field(2000, env="GOOGLE_MAX_TOKENS")

    # HuggingFace Provider
    HF_API_TOKEN: Optional[str] = Field(None, env="HF_API_TOKEN")
    HF_MODEL: str = Field("meta-llama/Llama-2-7b-chat-hf", env="HF_MODEL")
    HF_TEMPERATURE: float = Field(0.7, env="HF_TEMPERATURE")
    HF_MAX_TOKENS: int = Field(2000, env="HF_MAX_TOKENS")

    # Fallback HuggingFace Provider (small model for backup)
    FALLBACK_HF_API_TOKEN: Optional[str] = Field(None, env="FALLBACK_HF_API_TOKEN")
    FALLBACK_HF_MODEL: str = Field("google/flan-t5-small", env="FALLBACK_HF_MODEL")
    FALLBACK_HF_TEMPERATURE: float = Field(0.7, env="FALLBACK_HF_TEMPERATURE")
    FALLBACK_HF_MAX_TOKENS: int = Field(512, env="FALLBACK_HF_MAX_TOKENS")

    # Database
    DATABASE_URL: str = Field("sqlite:///./rag_fortress.db", env="DATABASE_URL")

    # Vector DB
    CHROMA_PERSIST_DIRECTORY: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    EMBEDDING_MODEL: str = Field("all-MiniLM-L6-v2", env="EMBEDDING_MODEL")

    # RAG
    CHUNK_SIZE: int = Field(1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(200, env="CHUNK_OVERLAP")
    TOP_K_RESULTS: int = Field(5, env="TOP_K_RESULTS")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(["http://localhost:3000", "http://localhost:8000"], env="ALLOWED_ORIGINS")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/app.log", env="LOG_FILE")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **values):
        super().__init__(**values)
        allowed_envs = {"development", "production", "staging"}
        if self.ENVIRONMENT not in allowed_envs:
            raise ValueError(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}. Allowed: {allowed_envs}")
        # Enforce debug level
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            self.LOG_LEVEL = "WARNING"
        elif self.ENVIRONMENT == "development":
            self.DEBUG = True
            self.LOG_LEVEL = "DEBUG"
        
        # Validate fallback provider is different from primary
        if self.FALLBACK_LLM_PROVIDER:
            self._validate_fallback_config()

    def get_llm_config(self):
        """Get LLM configuration for the selected provider"""
        provider = self.LLM_PROVIDER.lower()
        
        if provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
            }
        elif provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required when using Google provider")
            return {
                "provider": "google",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_MODEL,
                "temperature": self.GOOGLE_TEMPERATURE,
                "max_tokens": self.GOOGLE_MAX_TOKENS,
            }
        elif provider == "huggingface":
            if not self.HF_API_TOKEN:
                raise ValueError("HF_API_TOKEN is required when using HuggingFace provider")
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}. Supported: openai, google, huggingface")

    def get_fallback_llm_config(self):
        """
        Get fallback LLM configuration.
        
        Priority:
        1. If FALLBACK_LLM_PROVIDER and custom fields are provided, use those
        2. If FALLBACK_LLM_PROVIDER is set but no custom fields, use that provider's config
        3. If no fallback configured, defaults to small HuggingFace model
        """
        fallback_provider = self.FALLBACK_LLM_PROVIDER
        
        # Default to HuggingFace small model if no fallback configured
        if not fallback_provider:
            return {
                "provider": "huggingface",
                "api_key": self.FALLBACK_HF_API_TOKEN or self.HF_API_TOKEN,
                "model": self.FALLBACK_HF_MODEL,
                "temperature": self.FALLBACK_HF_TEMPERATURE,
                "max_tokens": self.FALLBACK_HF_MAX_TOKENS,
            }
        
        fallback_provider = fallback_provider.lower()
        
        # If custom fallback fields are provided, use them
        if self.FALLBACK_LLM_MODEL:
            api_key = self.FALLBACK_LLM_API_KEY
            
            # Try to get API key from provider-specific config if not explicitly set
            if not api_key:
                if fallback_provider == "openai":
                    api_key = self.OPENAI_API_KEY
                elif fallback_provider == "google":
                    api_key = self.GOOGLE_API_KEY
                elif fallback_provider == "huggingface":
                    api_key = self.HF_API_TOKEN
            
            if not api_key:
                raise ValueError(f"FALLBACK_LLM_API_KEY or {fallback_provider.upper()}_API_KEY is required")
            
            return {
                "provider": fallback_provider,
                "api_key": api_key,
                "model": self.FALLBACK_LLM_MODEL,
                "temperature": self.FALLBACK_LLM_TEMPERATURE or 0.7,
                "max_tokens": self.FALLBACK_LLM_MAX_TOKENS or 1000,
            }
        
        # Otherwise, use provider's default config
        if fallback_provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for fallback OpenAI provider")
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
            }
        elif fallback_provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for fallback Google provider")
            return {
                "provider": "google",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_MODEL,
                "temperature": self.GOOGLE_TEMPERATURE,
                "max_tokens": self.GOOGLE_MAX_TOKENS,
            }
        elif fallback_provider == "huggingface":
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unsupported fallback provider: {fallback_provider}. Supported: openai, google, huggingface")
    
    def _validate_fallback_config(self):
        """Validate that fallback provider/model is different from primary"""
        if not self.FALLBACK_LLM_PROVIDER:
            return
        
        primary_provider = self.LLM_PROVIDER.lower()
        fallback_provider = self.FALLBACK_LLM_PROVIDER.lower()
        
        # Get primary config
        primary_config = self.get_llm_config()
        
        # Get fallback config  
        fallback_config = self.get_fallback_llm_config()
        
        # Check if same provider and model
        if (primary_config["provider"] == fallback_config["provider"] and 
            primary_config["model"] == fallback_config["model"]):
            raise ValueError(
                f"Fallback LLM cannot be the same as primary LLM. "
                f"Primary: {primary_config['provider']}/{primary_config['model']}, "
                f"Fallback: {fallback_config['provider']}/{fallback_config['model']}"
            )

settings = Settings()