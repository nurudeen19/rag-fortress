"""
LLM provider factory with singleton pattern.
Returns configured LangChain LLM provider based on settings.
Reuses instance if already initialized (from startup).
"""

from typing import Optional
from langchain_core.language_models import BaseLanguageModel

from app.config.settings import settings
from app.core.exceptions import ConfigurationError
from app.core import get_logger

logger = get_logger(__name__)

# Global instances (initialized in startup)
_llm_instance: Optional[BaseLanguageModel] = None
_fallback_llm_instance: Optional[BaseLanguageModel] = None
_internal_llm_instance: Optional[BaseLanguageModel] = None
_classifier_llm_instance: Optional[BaseLanguageModel] = None


def get_llm_provider() -> BaseLanguageModel:
    """
    Get LangChain LLM provider.
    Returns existing instance if initialized, otherwise creates new one.
    
    Returns:
        BaseLanguageModel: LangChain LLM instance
    """
    global _llm_instance
    
    # Return existing instance if available
    if _llm_instance is not None:
        return _llm_instance
    
    # Create new instance
    _llm_instance = _create_llm_provider()
    return _llm_instance


def _create_llm_provider() -> BaseLanguageModel:
    """Create primary LLM provider from settings."""
    config = settings.get_llm_config()
    return _build_llm_from_config(config)


def get_fallback_llm_provider() -> BaseLanguageModel:
    """
    Get fallback LangChain LLM provider.
    Returns existing instance if initialized, otherwise creates new one.
    
    Returns:
        BaseLanguageModel: Fallback LangChain LLM instance
    """
    global _fallback_llm_instance
    
    # Return existing instance if available
    if _fallback_llm_instance is not None:
        return _fallback_llm_instance
    
    # Create new instance
    _fallback_llm_instance = _create_fallback_llm_provider()
    return _fallback_llm_instance


def _create_fallback_llm_provider() -> BaseLanguageModel:
    """Create fallback LLM provider from settings."""
    config = settings.get_fallback_llm_config()
    return _build_llm_from_config(config)


def get_internal_llm_provider() -> Optional[BaseLanguageModel]:
    """
    Get internal LangChain LLM provider for sensitive data.
    Returns existing instance if initialized, otherwise creates new one.
    Returns None if internal LLM is not enabled.
    
    Returns:
        Optional[BaseLanguageModel]: Internal LangChain LLM instance or None
    """
    if not settings.llm_settings.ENABLE_INTERNAL_LLM:
        return None
    
    global _internal_llm_instance
    
    # Return existing instance if available
    if _internal_llm_instance is not None:
        return _internal_llm_instance
    
    # Create new instance
    _internal_llm_instance = _create_internal_llm_provider()
    return _internal_llm_instance


def _create_internal_llm_provider() -> BaseLanguageModel:
    """Create internal LLM provider from settings."""
    config = settings.get_internal_llm_config()
    if not config:
        raise ConfigurationError("Internal LLM provider requested but no configuration found")
    return _build_llm_from_config(config)


def _build_llm_from_config(config: dict) -> BaseLanguageModel:
    """Instantiate a LangChain chat model from normalized provider config."""
    provider = config["provider"].lower()
    
    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ConfigurationError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )
        
        kwargs = {
            "api_key": config["api_key"],
            "model": config["model"],
            "temperature": config.get("temperature", 0.7),
        }
        if config.get("max_tokens") is not None:
            kwargs["max_tokens"] = config["max_tokens"]
        return ChatOpenAI(**kwargs)
    
    if provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ConfigurationError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        kwargs = {
            "google_api_key": config["api_key"],
            "model": config["model"],
            "temperature": config.get("temperature", 0.7),
        }
        if config.get("max_tokens") is not None:
            kwargs["max_tokens"] = config["max_tokens"]
        
        # Disable built-in retries: rate limits should immediately trigger fallback LLM
        # without being masked by LangChain's exponential backoff retry logic.
        # This ensures fast failover to fallback on 429 errors instead of waiting for retries.
        try:
            from google.api_core import gapic_v1
            kwargs["client_options"] = gapic_v1.client_options.ClientOptions(
                api_mtls_endpoint=None  # Disable retries via client config
            )
            # Alternative: configure through request options
            kwargs["request_options"] = {"max_retries": 0}
        except (ImportError, AttributeError, TypeError):
            # If configuration fails, continue without explicit retry disable
            # (newer versions may have different API)
            pass
        
        return ChatGoogleGenerativeAI(**kwargs)
    
    if provider == "huggingface":
        try:
            # New preferred package: langchain-huggingface
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )

        # Pass generation parameters explicitly (avoid model_kwargs deprecation)
        hf_kwargs = {
            "repo_id": config.get("model"),
            "endpoint_url": config.get("endpoint_url"),
            "huggingfacehub_api_token": config.get("api_key"),
            "task": config.get("task", "text-generation"),
            "timeout": config.get("timeout"),
        }

        # Explicit generation params required by newer LangChain versions
        temperature = config.get("temperature")
        if temperature is not None:
            hf_kwargs["temperature"] = temperature

        if config.get("max_tokens") is not None:
            hf_kwargs["max_new_tokens"] = config.get("max_tokens")

        llm = HuggingFaceEndpoint(**hf_kwargs)
        return ChatHuggingFace(llm=llm)
    
    if provider == "llamacpp":
        mode = config.get("mode", "local")
        # Support explicit modes: "api" (endpoint) or "local"
        if mode in {"endpoint", "api"}:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ConfigurationError(
                    "langchain-openai not installed. "
                    "Install with: pip install langchain-openai"
                )
            api_key = config.get("api_key") or "llamacpp-endpoint"
            kwargs = {
                "api_key": api_key,
                "model": config["model"],
                "temperature": config.get("temperature", 0.1),
                "base_url": config["endpoint_url"],
            }
            if config.get("max_tokens") is not None:
                kwargs["max_tokens"] = config["max_tokens"]
            if config.get("timeout") is not None:
                kwargs["timeout"] = config["timeout"]
            return ChatOpenAI(**kwargs)
        try:
            from langchain_community.chat_models import ChatLlamaCpp
        except ImportError:
            raise ConfigurationError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
        
        return ChatLlamaCpp(
            model_path=config["model_path"],
            temperature=config.get("temperature", 0.1),
            max_tokens=config.get("max_tokens"),
            n_ctx=config.get("context_size", 4096),
            n_threads=config.get("n_threads"),
            n_batch=config.get("n_batch"),
        )
    
    raise ConfigurationError(f"Unsupported LLM provider: {provider}")


def get_classifier_llm() -> Optional[BaseLanguageModel]:
    """
    Get or create the classifier/decomposer LLM instance.
    
    Returns None if both classifier and decomposer are disabled.
    
    Returns:
        Optional[BaseLanguageModel]: Classifier LLM instance or None
    """
    global _classifier_llm_instance
    
    # Check if either feature is enabled
    if not (settings.llm_settings.ENABLE_LLM_CLASSIFIER or settings.llm_settings.ENABLE_QUERY_DECOMPOSER):
        return None
    
    # Return existing instance if available
    if _classifier_llm_instance is not None:
        return _classifier_llm_instance
    
    # Create new instance
    _classifier_llm_instance = _create_classifier_llm()
    return _classifier_llm_instance


def _create_classifier_llm() -> Optional[BaseLanguageModel]:
    """Create classifier LLM provider from settings."""
    try:
        config = settings.get_classifier_llm_config()
        if not config:
            logger.warning("No classifier LLM config available")
            return None
        
        return _build_llm_from_config(config)
    except Exception as e:
        logger.error(f"Failed to initialize classifier LLM: {e}", exc_info=True)
        return None


def reset_classifier_llm():
    """Reset the classifier LLM instance (for testing)."""
    global _classifier_llm_instance
    _classifier_llm_instance = None



