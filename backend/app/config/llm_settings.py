"""
LLM provider configuration settings.
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """
    LLM provider configuration.
    
    Priority: DB (cached, encrypted keys decrypted, set via Settings class) → ENV → Field default
    """
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # ============================================================================
    # PRIMARY LLM CONFIGURATION
    # ============================================================================
    # Provider selection: openai, google, huggingface, llamacpp
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    
    # Generic fields for all providers
    LLM_API_KEY: Optional[str] = Field(None, env="LLM_API_KEY")
    LLM_MODEL: str = Field("gpt-3.5-turbo", env="LLM_MODEL")
    LLM_TEMPERATURE: float = Field(0.7, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(2000, env="LLM_MAX_TOKENS")
    
    # Optional provider-specific fields (user fills only when applicable)
    LLM_ENDPOINT_URL: Optional[str] = Field(None, env="LLM_ENDPOINT_URL")
    LLM_MODEL_PATH: Optional[str] = Field(None, env="LLM_MODEL_PATH")
    LLM_MODE: Optional[str] = Field(None, env="LLM_MODE")  # For llamacpp: 'local' or 'api'
    LLM_TIMEOUT: Optional[int] = Field(None, env="LLM_TIMEOUT")
    LLM_TASK: Optional[str] = Field(None, env="LLM_TASK")  # For huggingface
    
    # Llamacpp-specific advanced options
    LLM_CONTEXT_SIZE: Optional[int] = Field(None, env="LLM_CONTEXT_SIZE")
    LLM_N_THREADS: Optional[int] = Field(None, env="LLM_N_THREADS")
    LLM_N_BATCH: Optional[int] = Field(None, env="LLM_N_BATCH")

    # ============================================================================
    # FALLBACK LLM CONFIGURATION (Optional)
    # ============================================================================
    ENABLE_FALLBACK_LLM: bool = Field(False, env="ENABLE_FALLBACK_LLM")
    FALLBACK_LLM_PROVIDER: Optional[str] = Field(None, env="FALLBACK_LLM_PROVIDER")
    FALLBACK_LLM_API_KEY: Optional[str] = Field(None, env="FALLBACK_LLM_API_KEY")
    FALLBACK_LLM_MODEL: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL")
    FALLBACK_LLM_TEMPERATURE: Optional[float] = Field(None, env="FALLBACK_LLM_TEMPERATURE")
    FALLBACK_LLM_MAX_TOKENS: Optional[int] = Field(None, env="FALLBACK_LLM_MAX_TOKENS")
    FALLBACK_LLM_ENDPOINT_URL: Optional[str] = Field(None, env="FALLBACK_LLM_ENDPOINT_URL")
    FALLBACK_LLM_MODEL_PATH: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL_PATH")
    FALLBACK_LLM_MODE: Optional[str] = Field(None, env="FALLBACK_LLM_MODE")
    FALLBACK_LLM_TIMEOUT: Optional[int] = Field(None, env="FALLBACK_LLM_TIMEOUT")
    FALLBACK_LLM_TASK: Optional[str] = Field(None, env="FALLBACK_LLM_TASK")

    # ============================================================================
    # INTERNAL LLM CONFIGURATION (Optional - for sensitive documents)
    # ============================================================================
    ENABLE_INTERNAL_LLM: bool = Field(False, env="ENABLE_INTERNAL_LLM")
    INTERNAL_LLM_PROVIDER: Optional[str] = Field(None, env="INTERNAL_LLM_PROVIDER")
    INTERNAL_LLM_API_KEY: Optional[str] = Field(None, env="INTERNAL_LLM_API_KEY")
    INTERNAL_LLM_MODEL: Optional[str] = Field(None, env="INTERNAL_LLM_MODEL")
    INTERNAL_LLM_TEMPERATURE: float = Field(0.7, env="INTERNAL_LLM_TEMPERATURE")
    INTERNAL_LLM_MAX_TOKENS: int = Field(1000, env="INTERNAL_LLM_MAX_TOKENS")
    INTERNAL_LLM_MIN_SECURITY_LEVEL: int = Field(4, env="INTERNAL_LLM_MIN_SECURITY_LEVEL")
    INTERNAL_LLM_ENDPOINT_URL: Optional[str] = Field(None, env="INTERNAL_LLM_ENDPOINT_URL")
    INTERNAL_LLM_TIMEOUT: int = Field(120, env="INTERNAL_LLM_TIMEOUT")
    INTERNAL_LLM_MODE: Optional[str] = Field(None, env="INTERNAL_LLM_MODE")

    # ============================================================================
    # CLASSIFIER/DECOMPOSER CONFIGURATION
    # ============================================================================
    # LLM-based classifier (advanced, requires explicit provider configuration)
    ENABLE_LLM_CLASSIFIER: bool = Field(False, env="ENABLE_LLM_CLASSIFIER")
    # Query decomposer (breaks complex queries into sub-queries using LLM)
    ENABLE_QUERY_DECOMPOSER: bool = Field(False, env="ENABLE_QUERY_DECOMPOSER")
    
    # Classifier requires explicit configuration when enabled
    CLASSIFIER_LLM_PROVIDER: Optional[str] = Field(None, env="CLASSIFIER_LLM_PROVIDER")
    CLASSIFIER_LLM_API_KEY: Optional[str] = Field(None, env="CLASSIFIER_LLM_API_KEY")
    CLASSIFIER_LLM_MODEL: Optional[str] = Field(None, env="CLASSIFIER_LLM_MODEL")
    CLASSIFIER_LLM_ENDPOINT_URL: Optional[str] = Field(None, env="CLASSIFIER_LLM_ENDPOINT_URL")
    CLASSIFIER_LLM_TIMEOUT: Optional[int] = Field(None, env="CLASSIFIER_LLM_TIMEOUT")


    @field_validator("LLM_TIMEOUT", "LLM_CONTEXT_SIZE", "LLM_N_THREADS", "LLM_N_BATCH",
                    "FALLBACK_LLM_TIMEOUT", "FALLBACK_LLM_MAX_TOKENS",
                    "CLASSIFIER_LLM_TIMEOUT", mode="before")
    @classmethod
    def validate_optional_int_fields(cls, v):
        """Convert empty strings to None for optional int fields."""
        if v == "" or v is None:
            return None
        return int(v) if isinstance(v, str) else v

    def get_classifier_llm_config(self) -> Optional[dict]:
        """
        Get classifier/decomposer LLM configuration.
        
        When classifier/decomposer is enabled, requires explicit configuration.
        Uses temperature=0 for factual, deterministic responses.
        """
        if not (self.ENABLE_LLM_CLASSIFIER or self.ENABLE_QUERY_DECOMPOSER):
            return None
        
        # Classifier/decomposer requires explicit configuration
        if not self.CLASSIFIER_LLM_PROVIDER:
            raise ValueError(
                "Classifier/decomposer LLM is enabled but CLASSIFIER_LLM_PROVIDER is not configured. "
                "Please set CLASSIFIER_LLM_PROVIDER (openai, google, huggingface, llamacpp) along with "
                "CLASSIFIER_LLM_API_KEY and CLASSIFIER_LLM_MODEL, or disable ENABLE_LLM_CLASSIFIER and ENABLE_QUERY_DECOMPOSER."
            )
        
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
            config.update({
                "endpoint_url": self.CLASSIFIER_LLM_ENDPOINT_URL,
                "timeout": self.CLASSIFIER_LLM_TIMEOUT,
            })
            return self._build_huggingface_config(config)
        elif provider == "llamacpp":
            config.update({
                "endpoint_url": self.CLASSIFIER_LLM_ENDPOINT_URL,
                "timeout": self.CLASSIFIER_LLM_TIMEOUT,
            })
            return self._build_llamacpp_config(config)
        else:
            raise ValueError(f"Unsupported classifier LLM provider: {provider}")

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
        if not self.ENABLE_INTERNAL_LLM:
            return None
        
        if not self.INTERNAL_LLM_PROVIDER:
            raise ValueError("INTERNAL_LLM_PROVIDER is required when ENABLE_INTERNAL_LLM is true")
        
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
        """Build OpenAI configuration - uses consolidated env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.LLM_API_KEY
        model = config.get("model") or self.LLM_MODEL
        temperature = config.get("temperature") if config.get("temperature") is not None else self.LLM_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.LLM_MAX_TOKENS
        
        if not api_key:
            raise ValueError("OpenAI API key is required (set LLM_API_KEY)")
        if not model:
            raise ValueError("OpenAI model is required (set LLM_MODEL)")
        
        return {
            "provider": "openai",
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _build_google_config(self, config: Optional[dict] = None) -> dict:
        """Build Google configuration - uses consolidated env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.LLM_API_KEY
        model = config.get("model") or self.LLM_MODEL
        temperature = config.get("temperature") if config.get("temperature") is not None else self.LLM_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.LLM_MAX_TOKENS
        
        if not api_key:
            raise ValueError("Google API key is required (set LLM_API_KEY)")
        if not model:
            raise ValueError("Google model is required (set LLM_MODEL)")
        
        return {
            "provider": "google",
            "api_key": api_key,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    def _build_huggingface_config(self, config: Optional[dict] = None) -> dict:
        """Build HuggingFace configuration - uses consolidated env vars by default, accepts optional overrides."""
        config = config or {}
        
        api_key = config.get("api_key") or self.LLM_API_KEY
        model = config.get("model") or self.LLM_MODEL
        endpoint_url = config.get("endpoint_url") or self.LLM_ENDPOINT_URL
        task = config.get("task") or self.LLM_TASK or "text-generation"
        temperature = config.get("temperature") if config.get("temperature") is not None else self.LLM_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.LLM_MAX_TOKENS
        timeout = config.get("timeout") or self.LLM_TIMEOUT or 120
        
        if not api_key:
            raise ValueError("HuggingFace API token is required (set LLM_API_KEY)")
        if not (model or endpoint_url):
            raise ValueError("HuggingFace model or endpoint URL is required (set LLM_MODEL or LLM_ENDPOINT_URL)")
        
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
        Build llama.cpp configuration - uses consolidated env vars by default, accepts optional overrides.
        
        Mode determines which fields are included:
        - 'api' or 'endpoint': Returns endpoint-only config (no model_path)
        - 'local': Returns local-only config (no endpoint fields)
        """
        config = config or {}
        
        mode = config.get("mode") or self.LLM_MODE or "api"
        model_path = config.get("model_path") or self.LLM_MODEL_PATH
        endpoint_url = config.get("endpoint_url") or self.LLM_ENDPOINT_URL
        model = config.get("model") or self.LLM_MODEL
        api_key = config.get("api_key") or self.LLM_API_KEY
        temperature = config.get("temperature") if config.get("temperature") is not None else self.LLM_TEMPERATURE
        max_tokens = config.get("max_tokens") or self.LLM_MAX_TOKENS
        timeout = config.get("timeout") or self.LLM_TIMEOUT or 120
        context_size = config.get("context_size") or self.LLM_CONTEXT_SIZE or 4096
        n_threads = config.get("n_threads") or self.LLM_N_THREADS or 4
        n_batch = config.get("n_batch") or self.LLM_N_BATCH or 512
        
        normalized_mode = (mode or "api").lower()
        
        # API/Endpoint mode: use OpenAI-compatible endpoint
        if normalized_mode in ("api", "endpoint"):
            if not endpoint_url:
                raise ValueError("llama.cpp endpoint URL is required for api mode (set LLM_ENDPOINT_URL)")
            if not model:
                raise ValueError("llama.cpp model is required for api mode (set LLM_MODEL)")
            
            return {
                "provider": "llamacpp",
                "mode": "endpoint",
                "endpoint_url": endpoint_url,
                "model": model,
                "api_key": api_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout
            }
        
        # Local mode: use local GGUF model file
        if normalized_mode == "local":
            if not model_path:
                raise ValueError("llama.cpp model path is required for local mode (set LLM_MODEL_PATH)")
            
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

