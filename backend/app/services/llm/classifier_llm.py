"""
Classifier/Decomposer LLM Factory

Initializes a dedicated LLM instance for classification and decomposition tasks.
Falls back to primary LLM if no dedicated config is provided.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)

_classifier_llm = None


def get_classifier_llm():
    """
    Get or create the classifier/decomposer LLM instance.
    
    Returns None if both classifier and decomposer are disabled.
    """
    global _classifier_llm
    
    # Check if either feature is enabled
    if not (settings.ENABLE_LLM_CLASSIFIER or settings.ENABLE_QUERY_DECOMPOSER):
        return None
    
    if _classifier_llm is not None:
        return _classifier_llm
    
    # Get config (with temperature=0)
    config = settings.get_classifier_llm_config()
    if not config:
        return None
    
    provider = config["provider"]
    
    try:
        if provider == "openai":
            _classifier_llm = ChatOpenAI(
                api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
        
        elif provider == "google":
            _classifier_llm = ChatGoogleGenerativeAI(
                google_api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_output_tokens=config["max_tokens"]
            )
        
        elif provider == "llamacpp":
            # For llamacpp, use OpenAI-compatible endpoint
            if config.get("mode") == "endpoint":
                _classifier_llm = ChatOpenAI(
                    base_url=config["endpoint_url"],
                    api_key=config.get("api_key", "not-needed"),
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
            else:
                logger.warning("Classifier LLM: llamacpp local mode not supported, using OpenAI endpoint mode")
                return None
        
        else:
            logger.warning(f"Unsupported classifier LLM provider: {provider}")
            return None
        
        return _classifier_llm
    
    except Exception as e:
        logger.error(f"Failed to initialize classifier LLM: {e}", exc_info=True)
        return None


def reset_classifier_llm():
    """Reset the classifier LLM instance (for testing)."""
    global _classifier_llm
    _classifier_llm = None
