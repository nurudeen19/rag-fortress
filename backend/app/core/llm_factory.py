"""
LLM provider factory with singleton pattern.
Returns configured LangChain LLM provider based on settings.
Reuses instance if already initialized (from startup).
"""

from typing import Optional
from langchain_core.language_models import BaseLanguageModel

from app.config.settings import settings
from app.core.exceptions import ConfigurationError


# Global instances (initialized in startup)
_llm_instance: Optional[BaseLanguageModel] = None
_fallback_llm_instance: Optional[BaseLanguageModel] = None


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
    """
    Create LangChain LLM provider based on configuration.
    Internal function - use get_llm_provider() instead.
    
    Returns:
        BaseLanguageModel: Configured LangChain LLM instance
    """
    config = settings.get_llm_config()
    provider = config["provider"].lower()
    
    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ConfigurationError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )
        
        return ChatOpenAI(
            api_key=config["api_key"],
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"]
        )
    
    elif provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ConfigurationError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        return ChatGoogleGenerativeAI(
            google_api_key=config["api_key"],
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"]
        )
    
    elif provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEndpoint
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        return HuggingFaceEndpoint(
            huggingfacehub_api_token=config["api_key"],
            repo_id=config["model"],
            temperature=config["temperature"],
            max_new_tokens=config["max_tokens"]
        )
    
    else:
        raise ConfigurationError(f"Unsupported LLM provider: {provider}")


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
    """
    Create fallback LangChain LLM provider based on configuration.
    Internal function - use get_fallback_llm_provider() instead.
    
    Returns:
        BaseLanguageModel: Configured fallback LangChain LLM instance
    """
    config = settings.get_fallback_llm_config()
    provider = config["provider"].lower()
    
    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ConfigurationError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )
        
        return ChatOpenAI(
            api_key=config["api_key"],
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"]
        )
    
    elif provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ConfigurationError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        return ChatGoogleGenerativeAI(
            google_api_key=config["api_key"],
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"]
        )
    
    elif provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEndpoint
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        return HuggingFaceEndpoint(
            huggingfacehub_api_token=config["api_key"],
            repo_id=config["model"],
            temperature=config["temperature"],
            max_new_tokens=config["max_tokens"]
        )
    
    else:
        raise ConfigurationError(f"Unsupported fallback LLM provider: {provider}")


def test_llm_provider() -> bool:
    """
    Test LLM provider setup with a simple request.
    
    Returns:
        bool: True if provider responds successfully, False otherwise
    """
    try:
        llm = get_llm_provider()
        response = llm.invoke("Hello")
        
        if response and len(str(response).strip()) > 0:
            return True
        return False
    
    except Exception as e:
        print(f"LLM provider test failed: {e}")
        return False
