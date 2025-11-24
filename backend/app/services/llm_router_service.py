"""
LLM Router Service

Routes LLM requests based on document security levels and user clearance.
Implements security-aware LLM selection:
- HIGHLY_CONFIDENTIAL documents → Internal/Secure LLM
- Lower security documents → External/Default LLM

Usage:
    router = LLMRouter()
    llm = await router.route_llm(retrieved_docs, user_permission)
    response = await llm.ainvoke(prompt)
"""

import logging
from typing import List, Optional
from langchain_core.language_models import BaseLanguageModel

from app.core.llm_factory import get_llm_provider, get_fallback_llm_provider
from app.models.user_permission import PermissionLevel
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class LLMRoutingDecision:
    """
    Represents an LLM routing decision with audit information.
    """
    def __init__(
        self,
        llm: BaseLanguageModel,
        llm_type: str,
        reason: str,
        max_security_level: PermissionLevel,
        user_clearance: PermissionLevel,
        doc_count: int
    ):
        self.llm = llm
        self.llm_type = llm_type  # "internal" or "external"
        self.reason = reason
        self.max_security_level = max_security_level
        self.user_clearance = user_clearance
        self.doc_count = doc_count
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/auditing."""
        return {
            "llm_type": self.llm_type,
            "reason": self.reason,
            "max_security_level": self.max_security_level.name if self.max_security_level else None,
            "user_clearance": self.user_clearance.name if self.user_clearance else None,
            "doc_count": self.doc_count
        }


class LLMRouter:
    """
    Routes LLM requests based on security context.
    
    Routing Strategy:
    1. Check maximum security level of retrieved documents
    2. If HIGHLY_CONFIDENTIAL → Use internal/secure LLM (fallback)
    3. Otherwise → Use external/default LLM (primary)
    4. Log all routing decisions for audit trail
    
    Configuration:
    - Primary LLM: External provider (OpenAI, Google, etc.)
    - Fallback LLM: Internal/secure provider (for sensitive data)
    
    Future Enhancement:
    - Can be extended to route based on user department
    - Can route to specialized models for specific domains
    - Can implement cost-based routing for optimization
    """
    
    def __init__(self):
        self._primary_llm = None
        self._secure_llm = None
    
    def _get_primary_llm(self) -> BaseLanguageModel:
        """Get primary (external) LLM provider."""
        if self._primary_llm is None:
            self._primary_llm = get_llm_provider()
            logger.info("Primary LLM initialized for external queries")
        return self._primary_llm
    
    def _get_secure_llm(self) -> BaseLanguageModel:
        """Get secure (internal) LLM provider for sensitive data."""
        if self._secure_llm is None:
            try:
                self._secure_llm = get_fallback_llm_provider()
                logger.info("Secure LLM initialized for confidential queries")
            except Exception as e:
                logger.error(f"Failed to initialize secure LLM: {e}")
                raise ConfigurationError(
                    "Secure LLM not configured. Set FALLBACK_LLM_PROVIDER environment variable."
                )
        return self._secure_llm
    
    async def route_llm(
        self,
        document_security_levels: List[PermissionLevel],
        user_clearance: PermissionLevel,
        metadata: Optional[dict] = None
    ) -> LLMRoutingDecision:
        """
        Route to appropriate LLM based on document security levels.
        
        Args:
            document_security_levels: Security levels of retrieved documents
            user_clearance: User's effective permission level
            metadata: Optional metadata for routing decision (e.g., department, topic)
            
        Returns:
            LLMRoutingDecision: Decision with LLM instance and audit info
            
        Raises:
            ConfigurationError: If secure LLM not configured for confidential data
        """
        
        # Handle empty document set
        if not document_security_levels:
            logger.info("No documents retrieved, using primary LLM")
            return LLMRoutingDecision(
                llm=self._get_primary_llm(),
                llm_type="external",
                reason="No documents retrieved",
                max_security_level=None,
                user_clearance=user_clearance,
                doc_count=0
            )
        
        # Find maximum security level in retrieved documents
        max_security_level = max(document_security_levels)
        doc_count = len(document_security_levels)
        
        # Route based on maximum security level
        if max_security_level >= PermissionLevel.HIGHLY_CONFIDENTIAL:
            # Use secure/internal LLM for highly confidential data
            llm = self._get_secure_llm()
            llm_type = "internal"
            reason = f"Highly confidential documents present (max_level={max_security_level.name})"
            
            logger.info(
                f"Routing to SECURE LLM: {doc_count} docs, "
                f"max_level={max_security_level.name}, "
                f"user_clearance={user_clearance.name}"
            )
        
        elif max_security_level >= PermissionLevel.CONFIDENTIAL:
            # For CONFIDENTIAL, you can choose to use secure or external
            # Currently using secure for all confidential+ data
            llm = self._get_secure_llm()
            llm_type = "internal"
            reason = f"Confidential documents present (max_level={max_security_level.name})"
            
            logger.info(
                f"Routing to SECURE LLM: {doc_count} docs, "
                f"max_level={max_security_level.name}, "
                f"user_clearance={user_clearance.name}"
            )
        
        else:
            # Use external LLM for RESTRICTED and GENERAL data
            llm = self._get_primary_llm()
            llm_type = "external"
            reason = f"Standard security documents (max_level={max_security_level.name})"
            
            logger.info(
                f"Routing to EXTERNAL LLM: {doc_count} docs, "
                f"max_level={max_security_level.name}, "
                f"user_clearance={user_clearance.name}"
            )
        
        decision = LLMRoutingDecision(
            llm=llm,
            llm_type=llm_type,
            reason=reason,
            max_security_level=max_security_level,
            user_clearance=user_clearance,
            doc_count=doc_count
        )
        
        # Log decision for audit trail
        self._log_routing_decision(decision, metadata)
        
        return decision
    
    def _log_routing_decision(self, decision: LLMRoutingDecision, metadata: Optional[dict]):
        """Log routing decision for audit and analytics."""
        log_data = decision.to_dict()
        if metadata:
            log_data["metadata"] = metadata
        
        logger.info(f"LLM Routing Decision: {log_data}")
        
        # TODO: Persist to database for compliance/audit requirements
        # - Create llm_routing_log table
        # - Store: timestamp, user_id, llm_type, reason, security_levels, etc.
        # - Enable queries like "How often do we route to secure LLM?"
    
    async def route_llm_simple(
        self,
        max_security_level: PermissionLevel,
        user_clearance: PermissionLevel
    ) -> BaseLanguageModel:
        """
        Simplified routing that just returns the LLM instance.
        
        Args:
            max_security_level: Maximum security level of documents
            user_clearance: User's effective permission level
            
        Returns:
            BaseLanguageModel: The selected LLM instance
        """
        decision = await self.route_llm([max_security_level], user_clearance)
        return decision.llm


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
