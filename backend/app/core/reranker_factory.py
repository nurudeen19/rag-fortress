"""
Reranker Factory - Creates reranker instances with singleton pattern.
Uses LangChain wrappers for provider compatibility.

Supported providers:
- HuggingFace: Cross-encoder models via sentence-transformers (local)
- Cohere: LangChain CohereRerank wrapper
- Jina: LangChain JinaRerank wrapper
"""

from typing import Optional, Any

from app.config.settings import settings
from app.core.exceptions import ConfigurationError
from app.core import get_logger


logger = get_logger(__name__)


# Global instance (initialized in startup)
_reranker_instance: Optional[Any] = None


def get_reranker() -> Optional[Any]:
    """
    Get reranker instance.
    Returns existing instance if initialized, otherwise creates new one.
    Returns None if reranker is disabled.
    
    Returns:
        Optional[Any]: Reranker instance or None
    """
    global _reranker_instance
    
    # Check if reranker is enabled
    if not settings.app_settings.ENABLE_RERANKER:
        return None
    
    # Return existing instance if available
    if _reranker_instance is not None:
        return _reranker_instance
    
    # Create new instance
    _reranker_instance = _create_reranker()
    return _reranker_instance


def _create_reranker() -> Any:
    """
    Create reranker instance based on configuration.
    Internal function - use get_reranker() instead.
    
    Returns:
        Reranker instance
    """
    config = settings.get_reranker_config()
    provider = config["provider"].lower()
    
    if provider == "huggingface":
        try:
            from sentence_transformers import CrossEncoder
            return CrossEncoder(config["model"])
        except ImportError:
            raise ConfigurationError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    elif provider == "cohere":
        try:
            from langchain_cohere import CohereRerank            
            if not config.get("api_key"):
                raise ConfigurationError(
                    "Cohere API key not provided. "
                    "Set RERANKER_API_KEY environment variable or configuration."
                )
            
            kwargs = {"cohere_api_key": config.get("api_key")}
            
            # Only include model if explicitly provided in config
            if config.get("model"):
                kwargs["model"] = config["model"]
                
            return CohereRerank(**kwargs)
        except ImportError:
            raise ConfigurationError(
                "langchain-cohere not installed. "
                "Install with: pip install langchain-cohere"
            )
    
    elif provider == "jina":
        try:
            from langchain_community.document_compressors import JinaRerank
            if not config.get("api_key"):
                raise ConfigurationError(
                    "Jina API key not provided. "
                    "Set RERANKER_API_KEY environment variable or configuration."
                )
            
            kwargs = {"api_key": config.get("api_key")}
            
            # Only include model if explicitly provided in config
            if config.get("model"):
                kwargs["model"] = config["model"]
                
            return JinaRerank(**kwargs)
        except ImportError:
            raise ConfigurationError(
                "langchain-community not installed. "
                "Install with: pip install langchain-community"
            )
    
    else:
        raise ConfigurationError(
            f"Unsupported reranker provider: {provider}. "
            f"Supported: huggingface, cohere, jina"
        )
