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
_internal_llm_instance: Optional[BaseLanguageModel] = None


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
            from langchain_huggingface import ChatHuggingFace
            from langchain_community.llms import HuggingFacePipeline
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        try:
            from transformers import BitsAndBytesConfig
        except ImportError:
            raise ConfigurationError(
                "transformers not installed. "
                "Install with: pip install transformers"
            )
        
        # Prepare model kwargs with quantization config if enabled
        model_kwargs = {}
        if config.get("enable_quantization"):
            quant_level = config.get("quantization_level", "4bit").lower()
            model_kwargs["quantization_config"] = _get_quantization_config(quant_level)
        
        llm = HuggingFacePipeline.from_model_id(
            model_id=config["model"],
            task="text-generation",
            pipeline_kwargs=dict(
                max_new_tokens=config["max_tokens"],
                do_sample=False,
                repetition_penalty=1.03,
                return_full_text=False,
            ),
            model_kwargs=model_kwargs,
        )
        return ChatHuggingFace(llm=llm)
    
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
            from langchain_huggingface import ChatHuggingFace
            from langchain_community.llms import HuggingFacePipeline
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        try:
            from transformers import BitsAndBytesConfig
        except ImportError:
            raise ConfigurationError(
                "transformers not installed. "
                "Install with: pip install transformers"
            )
        
        llm = HuggingFacePipeline.from_model_id(
            model_id=config["model"],
            task="text-generation",
            pipeline_kwargs=dict(
                max_new_tokens=config["max_tokens"],
                do_sample=False,
                repetition_penalty=1.03,
                return_full_text=False,
            ),
        )
        return ChatHuggingFace(llm=llm)
    
    else:
        raise ConfigurationError(f"Unsupported fallback LLM provider: {provider}")


def _get_quantization_config(quant_level: str):
    """
    Get BitsAndBytes quantization configuration based on level.
    
    Args:
        quant_level: Quantization level (e.g., '4bit', '8bit')
    
    Returns:
        BitsAndBytesConfig: Configured quantization settings
    """
    from transformers import BitsAndBytesConfig
    
    if quant_level == "4bit":
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_use_double_quant=True,
        )
    elif quant_level == "8bit":
        return BitsAndBytesConfig(
            load_in_8bit=True,
        )
    else:
        raise ConfigurationError(f"Unsupported quantization level: {quant_level}. Supported: 4bit, 8bit")


def get_internal_llm_provider() -> Optional[BaseLanguageModel]:
    """
    Get internal LangChain LLM provider for sensitive data.
    Returns existing instance if initialized, otherwise creates new one.
    Returns None if internal LLM is not enabled.
    
    Returns:
        Optional[BaseLanguageModel]: Internal LangChain LLM instance or None
    """
    if not settings.llm_settings.USE_INTERNAL_LLM:
        return None
    
    global _internal_llm_instance
    
    # Return existing instance if available
    if _internal_llm_instance is not None:
        return _internal_llm_instance
    
    # Create new instance
    _internal_llm_instance = _create_internal_llm_provider()
    return _internal_llm_instance


def _create_internal_llm_provider() -> BaseLanguageModel:
    """
    Create internal LangChain LLM provider based on configuration.
    Internal function - use get_internal_llm_provider() instead.
    
    Returns:
        BaseLanguageModel: Configured internal LangChain LLM instance
    """
    settings_obj = settings.llm_settings
    
    if not settings_obj.INTERNAL_LLM_PROVIDER or not settings_obj.INTERNAL_LLM_MODEL:
        raise ConfigurationError("Internal LLM provider and model are required when USE_INTERNAL_LLM is True")
    
    provider = settings_obj.INTERNAL_LLM_PROVIDER.lower()
    
    if provider == "huggingface":
        try:
            from langchain_huggingface import ChatHuggingFace
            from langchain_community.llms import HuggingFacePipeline
        except ImportError:
            raise ConfigurationError(
                "langchain-huggingface not installed. "
                "Install with: pip install langchain-huggingface"
            )
        
        try:
            from transformers import BitsAndBytesConfig
        except ImportError:
            raise ConfigurationError(
                "transformers not installed. "
                "Install with: pip install transformers"
            )
        
        # Prepare model kwargs with quantization config if enabled
        model_kwargs = {}
        if settings_obj.INTERNAL_LLM_ENABLE_QUANTIZATION:
            quant_level = (settings_obj.INTERNAL_LLM_QUANTIZATION_LEVEL or "4bit").lower()
            model_kwargs["quantization_config"] = _get_quantization_config(quant_level)
        
        llm = HuggingFacePipeline.from_model_id(
            model_id=settings_obj.INTERNAL_LLM_MODEL,
            task="text-generation",
            pipeline_kwargs=dict(
                max_new_tokens=settings_obj.INTERNAL_LLM_MAX_TOKENS,
                do_sample=False,
                repetition_penalty=1.03,
                return_full_text=False,
            ),
            model_kwargs=model_kwargs,
        )
        return ChatHuggingFace(llm=llm)
    
    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ConfigurationError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )
        
        return ChatOpenAI(
            api_key=settings_obj.INTERNAL_LLM_API_KEY,
            model=settings_obj.INTERNAL_LLM_MODEL,
            temperature=settings_obj.INTERNAL_LLM_TEMPERATURE,
            max_tokens=settings_obj.INTERNAL_LLM_MAX_TOKENS
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
            google_api_key=settings_obj.INTERNAL_LLM_API_KEY,
            model=settings_obj.INTERNAL_LLM_MODEL,
            temperature=settings_obj.INTERNAL_LLM_TEMPERATURE,
            max_tokens=settings_obj.INTERNAL_LLM_MAX_TOKENS
        )
    
    else:
        raise ConfigurationError(f"Unsupported internal LLM provider: {provider}")



