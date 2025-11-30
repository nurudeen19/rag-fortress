"""
LLM Router Service

Returns either the primary or internal LLM instance based on the highest
document security level and the internal LLM configuration.
"""

import logging
from typing import Optional
from langchain_core.language_models import BaseLanguageModel

from app.core.llm_factory import get_internal_llm_provider, get_llm_provider
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Simple router that chooses between primary and internal LLMs."""

    def __init__(self):
        self._primary_llm: Optional[BaseLanguageModel] = None
        self._internal_llm: Optional[BaseLanguageModel] = None

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

    def select_llm(self, max_security_level: Optional[int]) -> BaseLanguageModel:
        llm_settings = settings.llm_settings

        if not llm_settings.USE_INTERNAL_LLM:
            logger.info("Internal LLM disabled; using primary LLM")
            return self._get_primary_llm()

        if max_security_level is None:
            logger.info("No document security level provided; falling back to primary LLM")
            return self._get_primary_llm()

        threshold = llm_settings.INTERNAL_LLM_MIN_SECURITY_LEVEL
        if max_security_level >= threshold:
            internal_llm = self._get_internal_llm()
            if internal_llm:
                logger.info(
                    "Routing to internal LLM because max level %d >= threshold %d",
                    max_security_level,
                    threshold
                )
                return internal_llm
            logger.warning("Internal LLM enabled but unavailable; using primary LLM")

        logger.info(
            "Max document security level %s below threshold %d; using primary LLM",
            str(max_security_level),
            threshold
        )
        return self._get_primary_llm()


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
