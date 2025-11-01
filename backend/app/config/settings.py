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

    def get_llm_config(self):
        """Get LLM configuration for the selected provider"""
        provider = self.LLM_PROVIDER.lower()
        
        if provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return {
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
            }
        elif provider == "google":
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required when using Google provider")
            return {
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GOOGLE_MODEL,
                "temperature": self.GOOGLE_TEMPERATURE,
                "max_tokens": self.GOOGLE_MAX_TOKENS,
            }
        elif provider == "huggingface":
            if not self.HF_API_TOKEN:
                raise ValueError("HF_API_TOKEN is required when using HuggingFace provider")
            return {
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}. Supported: openai, google, huggingface")

settings = Settings()