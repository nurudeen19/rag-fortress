"""
LLM-based Intent Classifier

Uses structured output to classify queries as RAG or non-RAG.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate

from app.core import get_logger
from app.services.llm.classifier_llm import get_classifier_llm
from app.schemas.llm_classifier import LLMClassificationResult
from app.config.settings import settings

logger = get_logger(__name__)


class LLMIntentClassifier:
    """LLM-based intent classifier with structured output."""
    
    def __init__(self):
        """Initialize with pre-initialized LLM from startup."""
        self.llm = get_classifier_llm()
        if not self.llm:
            logger.warning("Classifier LLM not available - classification disabled")
            return
        
        # Use structured output with the schema
        try:
            self.structured_llm = self.llm.with_structured_output(LLMClassificationResult)
        except Exception as e:
            logger.warning(f"Structured output not supported, falling back to JSON mode: {e}")
            self.structured_llm = self.llm
        
        # Create prompt from settings
        from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
        
        system_template = SystemMessagePromptTemplate.from_template(
            settings.prompt_settings.CLASSIFIER_SYSTEM_PROMPT
        )
        user_template = HumanMessagePromptTemplate.from_template(
            settings.prompt_settings.CLASSIFIER_USER_PROMPT
        )
        self.prompt = ChatPromptTemplate.from_messages([system_template, user_template])
        
        logger.info("LLMIntentClassifier initialized with structured output")
    
    async def classify(self, query: str) -> Optional[LLMClassificationResult]:
        """
        Classify query intent using structured output.
        
        Args:
            query: User query to classify
            
        Returns:
            Classification result with requires_rag flag and optional response
        """
        if not self.llm or not query or not query.strip():
            return None
        
        try:
            # Build and invoke chain with structured output
            chain = self.prompt | self.structured_llm
            result = await chain.ainvoke({"query": query.strip()})
            
            # If structured output returned the model directly, use it
            if isinstance(result, LLMClassificationResult):
                logger.info(
                    f"Classified: requires_rag={result.requires_rag}, "
                    f"confidence={result.confidence:.2f}"
                )
                return result
            
            # Fallback: parse from dict/JSON if needed
            if isinstance(result, dict):
                return LLMClassificationResult(**result)
            
            logger.warning(f"Unexpected classifier response type: {type(result)}")
            return None
            
        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            return None


# Factory function
_classifier_instance = None

def get_llm_intent_classifier() -> Optional[LLMIntentClassifier]:
    """Get or create LLM intent classifier instance."""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = LLMIntentClassifier()
    
    return _classifier_instance
