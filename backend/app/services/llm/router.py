"""
LLM Router Service

Returns either the primary or internal LLM instance based on the highest
document security level and the internal LLM configuration.

Also tracks which LLM is being used (primary/internal) and provides
fallback LLM access for error recovery.
"""

import logging
from typing import Optional, Tuple
from enum import Enum
from langchain_core.language_models import BaseLanguageModel

from app.core.llm_factory import (
    get_internal_llm_provider,
    get_llm_provider,
    get_fallback_llm_provider
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMType(str, Enum):
    """Track which type of LLM is being used."""
    PRIMARY = "primary"
    INTERNAL = "internal"
    FALLBACK = "fallback"


class LLMRouter:
    """Routes between primary, internal, and fallback LLMs with error recovery."""

    def __init__(self):
        self._primary_llm: Optional[BaseLanguageModel] = None
        self._internal_llm: Optional[BaseLanguageModel] = None
        self._fallback_llm: Optional[BaseLanguageModel] = None
        self._last_selected_type: Optional[LLMType] = None

    def _get_primary_llm(self) -> BaseLanguageModel:
        if self._primary_llm is None:
            self._primary_llm = get_llm_provider()
            logger.info("Primary LLM instance ready")
        return self._primary_llm

    def _get_internal_llm(self) -> Optional[BaseLanguageModel]:
        if self._internal_llm is None:
            self._internal_llm = get_internal_llm_provider()
            if self._internal_llm:
                logger.info("Internal LLM instance ready")
            else:
                logger.warning("Internal LLM could not be initialized")
        return self._internal_llm

    def _get_fallback_llm(self) -> Optional[BaseLanguageModel]:
        """Get fallback LLM if enabled and configured."""
        
        # Check if fallback is enabled first
        if not settings.llm_settings.ENABLE_FALLBACK_LLM:
            return None
            
        if self._fallback_llm is None:
            try:
                self._fallback_llm = get_fallback_llm_provider()
                if self._fallback_llm:
                    logger.info("Fallback LLM instance ready")
                else:
                    logger.warning("Fallback LLM not configured")
            except Exception as e:
                logger.warning(f"Could not initialize fallback LLM: {e}")
                self._fallback_llm = None
        return self._fallback_llm

    def select_llm(self, max_security_level: Optional[int]) -> Tuple[BaseLanguageModel, LLMType]:
        """
        Select appropriate LLM based on document security level.
        
        Returns:
            Tuple of (LLM instance, LLMType to track which was selected)
        """
        # Settings inherits from LLMSettings, so attributes are directly on settings
        if not settings.ENABLE_INTERNAL_LLM:
            logger.info("Internal LLM disabled; using primary LLM")
            self._last_selected_type = LLMType.PRIMARY
            return self._get_primary_llm(), LLMType.PRIMARY

        if max_security_level is None:
            logger.info("No document security level provided; using primary LLM")
            self._last_selected_type = LLMType.PRIMARY
            return self._get_primary_llm(), LLMType.PRIMARY

        threshold = settings.INTERNAL_LLM_MIN_SECURITY_LEVEL
        if max_security_level >= threshold:
            internal_llm = self._get_internal_llm()
            if internal_llm:
                logger.info(
                    "Routing to internal LLM (level %d >= threshold %d)",
                    max_security_level,
                    threshold
                )
                self._last_selected_type = LLMType.INTERNAL
                return internal_llm, LLMType.INTERNAL
            logger.warning("Internal LLM enabled but unavailable; using primary LLM")

        logger.info(
            "Using primary LLM (level %d < threshold %d)",
            max_security_level if max_security_level is not None else 0,
            threshold
        )
        self._last_selected_type = LLMType.PRIMARY
        return self._get_primary_llm(), LLMType.PRIMARY

    def get_fallback_llm(self) -> Optional[BaseLanguageModel]:
        """
        Get fallback LLM for error recovery.
        
        Returns None if not configured.
        """
        return self._get_fallback_llm()

    def is_fallback_enabled(self) -> bool:
        """Check if fallback LLM is enabled in settings."""
        return settings.llm_settings.ENABLE_FALLBACK_LLM
    
    def is_fallback_configured(self) -> bool:
        """Check if fallback LLM is both enabled and configured."""
        if not self.is_fallback_enabled():
            return False
        return self._get_fallback_llm() is not None

    def get_last_selected_type(self) -> Optional[LLMType]:
        """Get the type of LLM that was last selected."""
        return self._last_selected_type


# Singleton instance
_llm_router = None


def get_llm_router() -> LLMRouter:
    """
    Get singleton instance of LLMRouter.
    
    Returns:
        LLMRouter: Shared router instance
    """
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
