"""
LLM-based Intent Classifier

Uses structured output to classify queries as RAG or non-RAG.
"""

from typing import Optional

from app.core import get_logger
from app.core.llm_factory import get_classifier_llm
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
            logger.info("Classifier initialized with structured output")
        except Exception as e:
            logger.warning(f"Structured output not supported, falling back to JSON mode: {e}")
            self.structured_llm = self.llm
    
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
            # Get system prompt directly from settings (Settings class inherits from PromptSettings)
            system_prompt = settings.prompt_settings.CLASSIFIER_SYSTEM_PROMPT
            
            # Send query with system prompt using structured output
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.strip()}
            ]
            
            result = await self.structured_llm.ainvoke(messages)
            
            # If structured output returned the model directly, use it
            if isinstance(result, LLMClassificationResult):
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
