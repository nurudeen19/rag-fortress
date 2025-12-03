"""
LLM provider configuration settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """
    LLM provider configuration.
    
    Priority: DB (cached, encrypted keys decrypted, set via Settings class) → ENV → Field default
    """
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # Provider selection
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

    # HuggingFace Provider (hosted endpoints)
    HF_API_TOKEN: Optional[str] = Field(None, env="HF_API_TOKEN")
    HF_MODEL: Optional[str] = Field("meta-llama/Llama-2-7b-chat-hf", env="HF_MODEL")
    HF_ENDPOINT_URL: Optional[str] = Field(None, env="HF_ENDPOINT_URL")
    HF_TASK: str = Field("text-generation", env="HF_TASK")
    HF_TEMPERATURE: float = Field(0.7, env="HF_TEMPERATURE")
    HF_MAX_TOKENS: int = Field(2000, env="HF_MAX_TOKENS")
    HF_TIMEOUT: int = Field(120, env="HF_TIMEOUT")

    # Fallback LLM configuration
    FALLBACK_LLM_PROVIDER: Optional[str] = Field(None, env="FALLBACK_LLM_PROVIDER")
    FALLBACK_LLM_API_KEY: Optional[str] = Field(None, env="FALLBACK_LLM_API_KEY")
    FALLBACK_LLM_MODEL: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL")
    FALLBACK_LLM_TEMPERATURE: Optional[float] = Field(None, env="FALLBACK_LLM_TEMPERATURE")
    FALLBACK_LLM_MAX_TOKENS: Optional[int] = Field(None, env="FALLBACK_LLM_MAX_TOKENS")
    FALLBACK_LLAMACPP_MODE: Optional[str] = Field(None, env="FALLBACK_LLAMACPP_MODE")


    # Llama.cpp Provider (local or endpoint)
    LLAMACPP_MODE: str = Field("api", env="LLAMACPP_MODE")
    LLAMACPP_MODEL_PATH: Optional[str] = Field(None, env="LLAMACPP_MODEL_PATH")
    LLAMACPP_TEMPERATURE: float = Field(0.1, env="LLAMACPP_TEMPERATURE")
    LLAMACPP_MAX_TOKENS: int = Field(512, env="LLAMACPP_MAX_TOKENS")
    LLAMACPP_CONTEXT_SIZE: int = Field(4096, env="LLAMACPP_CONTEXT_SIZE")
    LLAMACPP_N_THREADS: int = Field(4, env="LLAMACPP_N_THREADS")
    LLAMACPP_N_BATCH: int = Field(512, env="LLAMACPP_N_BATCH")
    LLAMACPP_ENDPOINT_URL: Optional[str] = Field(None, env="LLAMACPP_ENDPOINT_URL")
    LLAMACPP_ENDPOINT_MODEL: Optional[str] = Field(None, env="LLAMACPP_ENDPOINT_MODEL")
    LLAMACPP_ENDPOINT_API_KEY: Optional[str] = Field(None, env="LLAMACPP_ENDPOINT_API_KEY")
    LLAMACPP_ENDPOINT_TIMEOUT: int = Field(120, env="LLAMACPP_ENDPOINT_TIMEOUT")

    # Internal LLM Provider
    USE_INTERNAL_LLM: bool = Field(False, env="USE_INTERNAL_LLM")
    INTERNAL_LLM_PROVIDER: Optional[str] = Field(None, env="INTERNAL_LLM_PROVIDER")
    INTERNAL_LLM_API_KEY: Optional[str] = Field(None, env="INTERNAL_LLM_API_KEY")
    INTERNAL_LLM_MODEL: Optional[str] = Field(None, env="INTERNAL_LLM_MODEL")
    INTERNAL_LLM_TEMPERATURE: float = Field(0.7, env="INTERNAL_LLM_TEMPERATURE")
    INTERNAL_LLM_MAX_TOKENS: int = Field(1000, env="INTERNAL_LLM_MAX_TOKENS")
    INTERNAL_LLM_MIN_SECURITY_LEVEL: int = Field(4, env="INTERNAL_LLM_MIN_SECURITY_LEVEL")
    INTERNAL_LLM_ENDPOINT_URL: Optional[str] = Field(None, env="INTERNAL_LLM_ENDPOINT_URL")
    INTERNAL_LLM_TIMEOUT: int = Field(120, env="INTERNAL_LLM_TIMEOUT")
    INTERNAL_LLM_MODE: Optional[str] = Field(None, env="INTERNAL_LLM_MODE")


    def get_llm_config(self) -> dict:
        """Get LLM configuration for the selected provider."""
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
            if not (self.HF_MODEL or self.HF_ENDPOINT_URL):
                raise ValueError("HF_MODEL or HF_ENDPOINT_URL is required for HuggingFace provider")
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "endpoint_url": self.HF_ENDPOINT_URL,
                "task": self.HF_TASK,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
                "timeout": self.HF_TIMEOUT,
            }
        elif provider == "llamacpp":
            mode = (self.LLAMACPP_MODE or "api").lower()
            if mode == "api":
                if not self.LLAMACPP_ENDPOINT_URL:
                    raise ValueError("LLAMACPP_ENDPOINT_URL is required when LLAMACPP_MODE is set to api")
                if not self.LLAMACPP_ENDPOINT_MODEL:
                    raise ValueError("LLAMACPP_ENDPOINT_MODEL is required when LLAMACPP_MODE is set to api")
                return {
                    "provider": "llamacpp",
                    "mode": "endpoint",
                    "endpoint_url": self.LLAMACPP_ENDPOINT_URL,
                    "model": self.LLAMACPP_ENDPOINT_MODEL,
                    "api_key": self.LLAMACPP_ENDPOINT_API_KEY,
                    "temperature": self.LLAMACPP_TEMPERATURE,
                    "max_tokens": self.LLAMACPP_MAX_TOKENS,
                    "timeout": self.LLAMACPP_ENDPOINT_TIMEOUT,
                }
            if not self.LLAMACPP_MODEL_PATH:
                raise ValueError("LLAMACPP_MODEL_PATH is required when LLAMACPP_MODE is set to local")
            return {
                "provider": "llamacpp",
                "mode": "local",
                "model_path": self.LLAMACPP_MODEL_PATH,
                "temperature": self.LLAMACPP_TEMPERATURE,
                "max_tokens": self.LLAMACPP_MAX_TOKENS,
                "context_size": self.LLAMACPP_CONTEXT_SIZE,
                "n_threads": self.LLAMACPP_N_THREADS,
                "n_batch": self.LLAMACPP_N_BATCH,
            }
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.LLM_PROVIDER}. "
                "Supported: openai, google, huggingface, llamacpp"
            )

    def get_fallback_llm_config(self) -> dict:
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
                "endpoint_url": self.FALLBACK_HF_ENDPOINT_URL or self.HF_ENDPOINT_URL,
                "task": self.FALLBACK_HF_TASK,
                "temperature": self.FALLBACK_HF_TEMPERATURE,
                "max_tokens": self.FALLBACK_HF_MAX_TOKENS,
                "timeout": self.FALLBACK_HF_TIMEOUT,
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
            
            config = {
                "provider": fallback_provider,
                "api_key": api_key,
                "model": self.FALLBACK_LLM_MODEL,
                "temperature": self.FALLBACK_LLM_TEMPERATURE or 0.7,
                "max_tokens": self.FALLBACK_LLM_MAX_TOKENS or 1000,
            }
            if fallback_provider == "huggingface":
                config.update(
                    {
                        "endpoint_url": self.FALLBACK_HF_ENDPOINT_URL or self.HF_ENDPOINT_URL,
                        "task": self.FALLBACK_HF_TASK,
                        "timeout": self.FALLBACK_HF_TIMEOUT,
                    }
                )
            return config
        
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
            if not self.HF_API_TOKEN:
                raise ValueError("HF_API_TOKEN is required for fallback HuggingFace provider")
            if not (self.HF_MODEL or self.HF_ENDPOINT_URL):
                raise ValueError("HF_MODEL or HF_ENDPOINT_URL is required for fallback HuggingFace provider")
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "endpoint_url": self.HF_ENDPOINT_URL,
                "task": self.HF_TASK,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
                "timeout": self.HF_TIMEOUT,
            }
        elif fallback_provider == "llamacpp":
            mode = (self.FALLBACK_LLAMACPP_MODE or self.LLAMACPP_MODE or "api").lower()
            config = {
                "provider": "llamacpp",
                "temperature": self.LLAMACPP_TEMPERATURE,
                "max_tokens": self.LLAMACPP_MAX_TOKENS,
            }
            if mode == "api":
                if not self.LLAMACPP_ENDPOINT_URL:
                    raise ValueError("LLAMACPP_ENDPOINT_URL is required when fallback llama.cpp runs in api mode")
                if not self.LLAMACPP_ENDPOINT_MODEL:
                    raise ValueError("LLAMACPP_ENDPOINT_MODEL is required when fallback llama.cpp runs in api mode")
                config.update(
                    {
                        "mode": "endpoint",
                        "endpoint_url": self.LLAMACPP_ENDPOINT_URL,
                        "model": self.LLAMACPP_ENDPOINT_MODEL,
                        "api_key": self.LLAMACPP_ENDPOINT_API_KEY,
                        "timeout": self.LLAMACPP_ENDPOINT_TIMEOUT,
                    }
                )
            else:
                fallback_model = self.FALLBACK_LLM_MODEL or self.LLAMACPP_MODEL_PATH
                if not fallback_model:
                    raise ValueError("FALLBACK_LLM_MODEL or LLAMACPP_MODEL_PATH is required when fallback llama.cpp runs in local mode")
                config.update(
                    {
                        "mode": "local",
                        "model_path": fallback_model,
                        "context_size": self.LLAMACPP_CONTEXT_SIZE,
                        "n_threads": self.LLAMACPP_N_THREADS,
                        "n_batch": self.LLAMACPP_N_BATCH,
                    }
                )
            return config
        else:
            raise ValueError(
                f"Unsupported fallback provider: {fallback_provider}. "
                "Supported: openai, google, huggingface, llamacpp"
            )

    def validate_fallback_config(self):
        """Validate that fallback provider/model is different from primary."""
        if not self.FALLBACK_LLM_PROVIDER:
            return
        
        primary_config = self.get_llm_config()
        fallback_config = self.get_fallback_llm_config()
        
        def _model_identifier(config: dict) -> Optional[str]:
            return config.get("model") or config.get("model_path") or config.get("endpoint_url")

        # Check if same provider and identifier (model or endpoint)
        if (
            primary_config["provider"] == fallback_config["provider"] and
            _model_identifier(primary_config) == _model_identifier(fallback_config)
        ):
            raise ValueError(
                "Fallback LLM cannot be the same as primary LLM. "
                f"Primary: {primary_config['provider']}/{_model_identifier(primary_config)}, "
                f"Fallback: {fallback_config['provider']}/{_model_identifier(fallback_config)}"
            )


    def get_internal_llm_config(self) -> Optional[dict]:
        """Get internal LLM configuration if enabled."""
        if not self.USE_INTERNAL_LLM:
            return None
        
        if not self.INTERNAL_LLM_PROVIDER:
            raise ValueError("INTERNAL_LLM_PROVIDER is required when USE_INTERNAL_LLM is true")
        
        config = {
            "provider": self.INTERNAL_LLM_PROVIDER,
            "temperature": self.INTERNAL_LLM_TEMPERATURE,
            "max_tokens": self.INTERNAL_LLM_MAX_TOKENS,
            "min_security_level": self.INTERNAL_LLM_MIN_SECURITY_LEVEL,
        }

        provider = self.INTERNAL_LLM_PROVIDER.lower()
        if provider == "huggingface":
            if not self.INTERNAL_LLM_API_KEY:
                raise ValueError("INTERNAL_LLM_API_KEY is required for HuggingFace internal provider")
            if not (self.INTERNAL_LLM_MODEL or self.INTERNAL_LLM_ENDPOINT_URL):
                raise ValueError("INTERNAL_LLM_MODEL or INTERNAL_LLM_ENDPOINT_URL is required for HuggingFace internal provider")
            config.update(
                {
                    "api_key": self.INTERNAL_LLM_API_KEY,
                    "model": self.INTERNAL_LLM_MODEL,
                    "endpoint_url": self.INTERNAL_LLM_ENDPOINT_URL,
                    "timeout": self.INTERNAL_LLM_TIMEOUT,
                }
            )
        elif provider in {"openai", "google"}:
            if not self.INTERNAL_LLM_API_KEY or not self.INTERNAL_LLM_MODEL:
                raise ValueError("INTERNAL_LLM_API_KEY and INTERNAL_LLM_MODEL are required for OpenAI/Google internal provider")
            config.update(
                {
                    "api_key": self.INTERNAL_LLM_API_KEY,
                    "model": self.INTERNAL_LLM_MODEL,
                }
            )
        elif provider == "llamacpp":
            mode = (self.INTERNAL_LLM_MODE or self.LLAMACPP_MODE or "api").lower()
            if mode == "api":
                if not self.LLAMACPP_ENDPOINT_URL:
                    raise ValueError("LLAMACPP_ENDPOINT_URL is required when internal llama.cpp runs in api mode")
                if not self.LLAMACPP_ENDPOINT_MODEL:
                    raise ValueError("LLAMACPP_ENDPOINT_MODEL is required when internal llama.cpp runs in api mode")
                config.update(
                    {
                        "mode": "endpoint",
                        "endpoint_url": self.LLAMACPP_ENDPOINT_URL,
                        "model": self.LLAMACPP_ENDPOINT_MODEL,
                        "api_key": self.LLAMACPP_ENDPOINT_API_KEY,
                        "timeout": self.LLAMACPP_ENDPOINT_TIMEOUT,
                    }
                )
            else:
                model_path = self.LLAMACPP_MODEL_PATH or self.INTERNAL_LLM_MODEL
                if not model_path:
                    raise ValueError("LLAMACPP_MODEL_PATH or INTERNAL_LLM_MODEL is required when internal llama.cpp runs in local mode")
                config.update(
                    {
                        "mode": "local",
                        "model_path": model_path,
                        "context_size": self.LLAMACPP_CONTEXT_SIZE,
                        "n_threads": self.LLAMACPP_N_THREADS,
                        "n_batch": self.LLAMACPP_N_BATCH,
                    }
                )
        else:
            raise ValueError(
                f"Unsupported internal LLM provider: {self.INTERNAL_LLM_PROVIDER}. "
                "Supported: openai, google, huggingface, llamacpp"
            )

        return config
