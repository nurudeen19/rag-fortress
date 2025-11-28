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

    # HuggingFace Provider
    HF_API_TOKEN: Optional[str] = Field(None, env="HF_API_TOKEN")
    HF_MODEL: str = Field("meta-llama/Llama-2-7b-chat-hf", env="HF_MODEL")
    HF_TEMPERATURE: float = Field(0.7, env="HF_TEMPERATURE")
    HF_MAX_TOKENS: int = Field(2000, env="HF_MAX_TOKENS")
    HF_ENABLE_QUANTIZATION: bool = Field(True, env="HF_ENABLE_QUANTIZATION")
    HF_QUANTIZATION_LEVEL: str = Field("4bit", env="HF_QUANTIZATION_LEVEL")

    # Fallback LLM configuration
    FALLBACK_LLM_PROVIDER: Optional[str] = Field(None, env="FALLBACK_LLM_PROVIDER")
    FALLBACK_LLM_API_KEY: Optional[str] = Field(None, env="FALLBACK_LLM_API_KEY")
    FALLBACK_LLM_MODEL: Optional[str] = Field(None, env="FALLBACK_LLM_MODEL")
    FALLBACK_LLM_TEMPERATURE: Optional[float] = Field(None, env="FALLBACK_LLM_TEMPERATURE")
    FALLBACK_LLM_MAX_TOKENS: Optional[int] = Field(None, env="FALLBACK_LLM_MAX_TOKENS")

    # Fallback HuggingFace Provider (small model for backup)
    FALLBACK_HF_API_TOKEN: Optional[str] = Field(None, env="FALLBACK_HF_API_TOKEN")
    FALLBACK_HF_MODEL: str = Field("google/flan-t5-small", env="FALLBACK_HF_MODEL")
    FALLBACK_HF_TEMPERATURE: float = Field(0.7, env="FALLBACK_HF_TEMPERATURE")
    FALLBACK_HF_MAX_TOKENS: int = Field(512, env="FALLBACK_HF_MAX_TOKENS")

    # Internal LLM Provider
    USE_INTERNAL_LLM: bool = Field(False, env="USE_INTERNAL_LLM")
    INTERNAL_LLM_PROVIDER: Optional[str] = Field(None, env="INTERNAL_LLM_PROVIDER")
    INTERNAL_LLM_API_KEY: Optional[str] = Field(None, env="INTERNAL_LLM_API_KEY")
    INTERNAL_LLM_MODEL: Optional[str] = Field(None, env="INTERNAL_LLM_MODEL")
    INTERNAL_LLM_TEMPERATURE: float = Field(0.7, env="INTERNAL_LLM_TEMPERATURE")
    INTERNAL_LLM_MAX_TOKENS: int = Field(1000, env="INTERNAL_LLM_MAX_TOKENS")
    INTERNAL_LLM_MIN_SECURITY_LEVEL: int = Field(4, env="INTERNAL_LLM_MIN_SECURITY_LEVEL")
    INTERNAL_LLM_ENABLE_QUANTIZATION: bool = Field(False, env="INTERNAL_LLM_ENABLE_QUANTIZATION")
    INTERNAL_LLM_QUANTIZATION_LEVEL: Optional[str] = Field(None, env="INTERNAL_LLM_QUANTIZATION_LEVEL")
    

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
            return {
                "provider": "huggingface",
                "api_key": self.HF_API_TOKEN,
                "model": self.HF_MODEL,
                "temperature": self.HF_TEMPERATURE,
                "max_tokens": self.HF_MAX_TOKENS,
                "enable_quantization": self.HF_ENABLE_QUANTIZATION,
                "quantization_level": self.HF_QUANTIZATION_LEVEL,
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}. Supported: openai, google, huggingface")

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

    def validate_fallback_config(self):
        """Validate that fallback provider/model is different from primary."""
        if not self.FALLBACK_LLM_PROVIDER:
            return
        
        primary_config = self.get_llm_config()
        fallback_config = self.get_fallback_llm_config()
        
        # Check if same provider and model
        if (primary_config["provider"] == fallback_config["provider"] and 
            primary_config["model"] == fallback_config["model"]):
            raise ValueError(
                f"Fallback LLM cannot be the same as primary LLM. "
                f"Primary: {primary_config['provider']}/{primary_config['model']}, "
                f"Fallback: {fallback_config['provider']}/{fallback_config['model']}"
            )


    def get_internal_llm_config(self) -> Optional[dict]:
        """Get internal LLM configuration if enabled."""
        if not self.USE_INTERNAL_LLM:
            return None
        
        if not self.INTERNAL_LLM_PROVIDER or not self.INTERNAL_LLM_MODEL:
            raise ValueError("INTERNAL_LLM_PROVIDER and INTERNAL_LLM_MODEL are required when USE_INTERNAL_LLM is true")
        
        return {
            "provider": self.INTERNAL_LLM_PROVIDER,
            "api_key": self.INTERNAL_LLM_API_KEY,
            "model": self.INTERNAL_LLM_MODEL,
            "temperature": self.INTERNAL_LLM_TEMPERATURE,
            "max_tokens": self.INTERNAL_LLM_MAX_TOKENS,
            "min_security_level": self.INTERNAL_LLM_MIN_SECURITY_LEVEL,
            "enable_quantization": self.INTERNAL_LLM_ENABLE_QUANTIZATION,
            "quantization_level": self.INTERNAL_LLM_QUANTIZATION_LEVEL,
        }