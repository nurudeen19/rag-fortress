"""
Embedding provider factory with singleton pattern.
Returns configured LangChain embedding provider based on settings.
Reuses instance if already initialized (from startup).

Also provides RedisVL vectorizer for semantic cache.
"""

from typing import Optional
from langchain_core.embeddings import Embeddings

from app.config.settings import settings
from app.core.exceptions import ConfigurationError
from app.core import get_logger
    
logger = get_logger(__name__)

# Global instances (initialized in startup)
_embedding_instance: Optional[Embeddings] = None
_redisvl_vectorizer_instance: Optional[any] = None


def get_embedding_provider() -> Embeddings:
    """
    Get LangChain embedding provider.
    Returns existing instance if initialized, otherwise creates new one.
    
    Returns:
        Embeddings: LangChain Embeddings instance with:
            - embed_documents(texts: List[str]) -> List[List[float]]
            - embed_query(text: str) -> List[float]
            - aembed_documents(texts: List[str]) -> List[List[float]] (async)
            - aembed_query(text: str) -> List[float] (async)
    """
    global _embedding_instance
    
    # Return existing instance if available
    if _embedding_instance is not None:
        return _embedding_instance
    
    # Create new instance
    _embedding_instance = _create_embedding_provider()
    return _embedding_instance


def _create_embedding_provider() -> Embeddings:
    """
    Create LangChain embedding provider based on configuration.
    Internal function - use get_embedding_provider() instead.
    
    Returns:
        Embeddings: Configured LangChain Embeddings instance
    """
    config = settings.get_embedding_config()
    provider = config["provider"].lower()
    
    if provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        return HuggingFaceEmbeddings(
            model_name=config["model"]
        )
    
    elif provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ConfigurationError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )
        
        kwargs = {
            "api_key": config["api_key"],
            "model": config["model"]
        }
        if config.get("dimensions"):
            kwargs["dimensions"] = config["dimensions"]
        
        return OpenAIEmbeddings(**kwargs)
    
    elif provider == "cohere":
        try:
            from langchain_cohere import CohereEmbeddings
        except ImportError:
            raise ConfigurationError(
                "langchain-cohere not installed. "
                "Install with: pip install langchain-cohere"
            )
        
        return CohereEmbeddings(
            cohere_api_key=config["api_key"],
            model=config["model"]
        )
    
    elif provider == "google":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ConfigurationError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        kwargs = {
            "google_api_key": config["api_key"],
            "model": config["model"]
        }
        
        return GoogleGenerativeAIEmbeddings(**kwargs)
    
    else:
        raise ConfigurationError(f"Unsupported embedding provider: {provider}")


def get_redisvl_vectorizer():
    """
    Get RedisVL vectorizer for semantic cache.
    Returns existing instance if initialized, otherwise creates new one.
    
    Uses configuration from settings.embedding_settings.get_redisvl_config()
    which can either reuse existing embedding config or use separate RedisVL config.
    
    Returns:
        RedisVL vectorizer instance (OpenAITextVectorizer, CohereTextVectorizer, or HuggingFaceTextVectorizer)
    """
    global _redisvl_vectorizer_instance
    
    # Return existing instance if available
    if _redisvl_vectorizer_instance is not None:
        return _redisvl_vectorizer_instance
    
    # Create new instance
    _redisvl_vectorizer_instance = _create_redisvl_vectorizer()
    return _redisvl_vectorizer_instance


def _create_redisvl_vectorizer():
    """
    Create RedisVL vectorizer based on configuration.
    Internal function - use get_redisvl_vectorizer() instead.
    
    Returns:
        RedisVL vectorizer instance configured for the selected provider
    """
    
    try:
        from redisvl.utils.vectorize import (
            OpenAITextVectorizer,
            CohereTextVectorizer,
            HFTextVectorizer,
        )
    except ImportError:
        raise ConfigurationError(
            "redisvl not installed. "
            "Install with: pip install redisvl"
        )
    
    config = settings.embedding_settings.get_redisvl_config()
    provider = config["provider"].lower()
    
    logger.info(f"Creating RedisVL vectorizer for provider: {provider}")
    
    if provider == "openai":
        return OpenAITextVectorizer(
            model=config["model"],
            api_config={"api_key": config["api_key"]}
        )
    
    elif provider == "cohere":
        return CohereTextVectorizer(
            model=config["model"],
            api_config={"api_key": config["api_key"]},
            input_type=config.get("input_type", "search_query")
        )
    
    elif provider == "huggingface":
        return HFTextVectorizer(
            model=config["model"]
        )
    
    else:
        raise ConfigurationError(
            f"Unsupported RedisVL provider: {provider}. "
            "Supported: openai, cohere, huggingface"
        )