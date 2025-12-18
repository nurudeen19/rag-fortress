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

    # Classifier/Decomposer LLM (uses primary LLM config if not specified)
    ENABLE_LLM_CLASSIFIER: bool = Field(False, env="ENABLE_LLM_CLASSIFIER")
    ENABLE_QUERY_DECOMPOSER: bool = Field(False, env="ENABLE_QUERY_DECOMPOSER")
    
    # Optional: Override primary LLM for classifier/decomposer
    CLASSIFIER_LLM_PROVIDER: Optional[str] = Field(None, env="CLASSIFIER_LLM_PROVIDER")
    CLASSIFIER_LLM_API_KEY: Optional[str] = Field(None, env="CLASSIFIER_LLM_API_KEY")
    CLASSIFIER_LLM_MODEL: Optional[str] = Field(None, env="CLASSIFIER_LLM_MODEL")


    def get_classifier_llm_config(self) -> Optional[dict]:
        """
        Get classifier/decomposer LLM configuration.
        
        Falls back to primary LLM if no specific classifier LLM is configured.
        Uses temperature=0 for factual, deterministic responses.
        """
        if not (self.ENABLE_LLM_CLASSIFIER or self.ENABLE_QUERY_DECOMPOSER):
            return None
        
        # Use dedicated classifier LLM if configured
        if self.CLASSIFIER_LLM_PROVIDER:
            provider = self.CLASSIFIER_LLM_PROVIDER.lower()
            
            config = {
                "api_key": self.CLASSIFIER_LLM_API_KEY,
                "model": self.CLASSIFIER_LLM_MODEL,
                "temperature": 0.0,  # Factual, deterministic
                "max_tokens": 300,
            }
            
            if provider == "openai":
                return self._build_openai_config(config)
            elif provider == "google":
                return self._build_google_config(config)
            elif provider == "huggingface":
                return self._build_huggingface_config(config)
            elif provider == "llamacpp":
                return self._build_llamacpp_config(config)
            else:
                raise ValueError(f"Unsupported classifier LLM provider: {provider}")
        
        # Fall back to primary LLM config with temperature=0
        primary_config = self.get_llm_config()
        primary_config["temperature"] = 0.0  # Override for factual responses
        primary_config["max_tokens"] = 300
        return primary_config

    def get_llm_config(self) -> dict:
        """Get primary LLM configuration."""
        provider = self.LLM_PROVIDER.lower()
        
        if provider == "openai":
            return self._build_openai_config()
        if provider == "google":
            return self._build_google_config()
        if provider == "huggingface":
            return self._build_huggingface_config()
        if provider == "llamacpp":
            return self._build_llamacpp_config()
        
        raise ValueError(
            f"Unsupported LLM provider: {self.LLM_PROVIDER}. "
            "Supported: openai, google, huggingface, llamacpp"
        )

    def get_fallback_llm_config(self) -> dict:
        """Get fallback LLM configuration (defaults to HuggingFace if not specified)."""
        provider = (self.FALLBACK_LLM_PROVIDER or "huggingface").lower()
        
        # Build config overrides from fallback-specific env vars
        config = {
            "api_key": self.FALLBACK_LLM_API_KEY,
            "model": self.FALLBACK_LLM_MODEL,
            "temperature": self.FALLBACK_LLM_TEMPERATURE,
            "max_tokens": self.FALLBACK_LLM_MAX_TOKENS,
        }
        
        if provider == "openai":
            return self._build_openai_config(config)
        if provider == "google":
            return self._build_google_config(config)
        if provider == "huggingface":
            # Add HuggingFace-specific fallback fields
            config.update({
                "endpoint_url": getattr(self, "FALLBACK_HF_ENDPOINT_URL", None),
                "task": getattr(self, "FALLBACK_HF_TASK", None),
                "timeout": getattr(self, "FALLBACK_HF_TIMEOUT", None),
            })
            return self._build_huggingface_config(config)
        if provider == "llamacpp":
            # Add llamacpp-specific fallback fields
            config.update({
                "mode": self.FALLBACK_LLAMACPP_MODE,
                "model_path": self.FALLBACK_LLM_MODEL,
            })
            return self._build_llamacpp_config(config)
        
        raise ValueError(
            f"Unsupported fallback provider: {provider}. "
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
        """Get internal LLM configuration (for sensitive data processing)."""
        if not self.USE_INTERNAL_LLM:
            return None
        
        if not self.INTERNAL_LLM_PROVIDER:
            raise ValueError("INTERNAL_LLM_PROVIDER is required when USE_INTERNAL_LLM is true")
        
        provider = self.INTERNAL_LLM_PROVIDER.lower()
        
        # Build config overrides from internal-specific env vars
        config = {
            "api_key": self.INTERNAL_LLM_API_KEY,
            "model": self.INTERNAL_LLM_MODEL,
            "temperature": self.INTERNAL_LLM_TEMPERATURE,
            "max_tokens": self.INTERNAL_LLM_MAX_TOKENS,
        }
        
        if provider == "openai":
            result = self._build_openai_config(config)
        elif provider == "google":
            result = self._build_google_config(config)
        elif provider == "huggingface":
            config.update({
                "endpoint_url": self.INTERNAL_LLM_ENDPOINT_URL,
                "task": "text-generation",
                "timeout": self.INTERNAL_LLM_TIMEOUT,
            })
            result = self._build_huggingface_config(config)
        elif provider == "llamacpp":
            config.update({
                "mode": self.INTERNAL_LLM_MODE,
                "model_path": self.INTERNAL_LLM_MODEL,
            })
            result = self._build_llamacpp_config(config)
        else:
            raise ValueError(
                f"Unsupported internal LLM provider: {self.INTERNAL_LLM_PROVIDER}. "
                "Supported: openai, google, huggingface, llamacpp"
            )
        
        result["min_security_level"] = self.INTERNAL_LLM_MIN_SECURITY_LEVEL
        return result

    # Provider-specific builders - use their own env vars by default, accept optional config overrides
    def _build_openai_config(self, config: Optional[dict] = None) -> dict:
        """Build OpenAI configuration - uses env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.OPENAI_API_KEY
        model = config.get("model") or self.OPENAI_MODEL
        temperature = config.get("temperature") or self.OPENAI_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.OPENAI_MAX_TOKENS
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
        if not model:
            raise ValueError("OpenAI model is required")
        
        return {
            "provider": "openai",
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _build_google_config(self, config: Optional[dict] = None) -> dict:
        """Build Google configuration - uses env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.GOOGLE_API_KEY
        model = config.get("model") or self.GOOGLE_MODEL
        temperature = config.get("temperature") or self.GOOGLE_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.GOOGLE_MAX_TOKENS
        
        if not api_key:
            raise ValueError("Google API key is required")
        if not model:
            raise ValueError("Google model is required")
        
        return {
            "provider": "google",
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _build_huggingface_config(self, config: Optional[dict] = None) -> dict:
        """Build HuggingFace configuration - uses env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.HF_API_TOKEN
        model = config.get("model") or self.HF_MODEL
        endpoint_url = config.get("endpoint_url") or self.HF_ENDPOINT_URL
        task = config.get("task") or self.HF_TASK
        temperature = config.get("temperature") or self.HF_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.HF_MAX_TOKENS
        timeout = config.get("timeout") or self.HF_TIMEOUT
        
        if not api_key:
            raise ValueError("HuggingFace API token is required")
        if not (model or endpoint_url):
            raise ValueError("HuggingFace model or endpoint URL is required")
        
        return {
            "provider": "huggingface",
            "api_key": api_key,
            "model": model,
            "endpoint_url": endpoint_url,
            "task": task,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout
        }

    def _build_llamacpp_config(self, config: Optional[dict] = None) -> dict:
        """
        Build llama.cpp configuration - uses env vars by default, accepts optional overrides.
        
        Mode determines which fields are included:
        - 'api' or 'endpoint': Returns endpoint-only config (no model_path)
        - 'local': Returns local-only config (no endpoint fields)
        """
        config = config or {}
        
        mode = config.get("mode") or self.LLAMACPP_MODE
        model_path = config.get("model_path") or self.LLAMACPP_MODEL_PATH
        endpoint_url = self.LLAMACPP_ENDPOINT_URL
        endpoint_model = self.LLAMACPP_ENDPOINT_MODEL
        endpoint_api_key = self.LLAMACPP_ENDPOINT_API_KEY
        endpoint_timeout = self.LLAMACPP_ENDPOINT_TIMEOUT
        temperature = config.get("temperature") or self.LLAMACPP_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.LLAMACPP_MAX_TOKENS
        context_size = self.LLAMACPP_CONTEXT_SIZE
        n_threads = self.LLAMACPP_N_THREADS
        n_batch = self.LLAMACPP_N_BATCH
        
        normalized_mode = (mode or "api").lower()
        
        # API/Endpoint mode: use OpenAI-compatible endpoint
        if normalized_mode in ("api", "endpoint"):
            if not endpoint_url:
                raise ValueError("llama.cpp endpoint URL is required for api mode")
            if not endpoint_model:
                raise ValueError("llama.cpp endpoint model is required for api mode")
            
            return {
                "provider": "llamacpp",
                "mode": "endpoint",
                "endpoint_url": endpoint_url,
                "model": endpoint_model,
                "api_key": endpoint_api_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": endpoint_timeout
            }
        
        # Local mode: use local GGUF model file
        if normalized_mode == "local":
            if not model_path:
                raise ValueError("llama.cpp model path is required for local mode")
            
            return {
                "provider": "llamacpp",
                "mode": "local",
                "model_path": model_path,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "context_size": context_size,
                "n_threads": n_threads,
                "n_batch": n_batch
            }
        
        raise ValueError(f"Invalid llama.cpp mode: {mode}. Must be 'api' or 'local'")
