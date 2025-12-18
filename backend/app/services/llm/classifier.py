"""
LLM-based Intent Classifier

Simple classifier that determines if a query needs RAG or can be answered directly.
For non-RAG queries, the LLM generates its own response.
"""

import json
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate

from app.core import get_logger
from app.services.llm.classifier_llm import get_classifier_llm
from app.schemas.llm_classifier import LLMClassificationResult

logger = get_logger(__name__)


CLASSIFICATION_PROMPT = """You are an intent classifier for a RAG system. Analyze the query and determine:

1. Does it need document retrieval (RAG)? Knowledge questions, policy lookups, etc.
2. Or can you answer directly? Greetings, pleasantries, small talk, etc.

For NON-RAG queries (greetings, thanks, etc.), provide a natural, friendly response.
For RAG queries, just indicate that retrieval is needed.

Return JSON:
{
    "requires_rag": true/false,
    "confidence": 0.0-1.0,
    "response": "your direct response if requires_rag=false, empty otherwise"
}

Examples:

Query: "Hi there!"
{
    "requires_rag": false,
    "confidence": 0.95,
    "response": "Hello! I'm here to help you find information. What would you like to know?"
}

Query: "What is the vacation policy?"
{
    "requires_rag": true,
    "confidence": 0.98,
    "response": ""
}

Query: "Thanks for the help!"
{
    "requires_rag": false,
    "confidence": 0.95,
    "response": "You're very welcome! Let me know if you need anything else."
}

Query: "{query}"

Return JSON only:"""


class LLMIntentClassifier:
    """Simple LLM-based intent classifier."""
    
    def __init__(self):
        """Initialize with pre-initialized LLM from startup."""
        self.llm = get_classifier_llm()
        if not self.llm:
            logger.warning("Classifier LLM not available - classification disabled")
        
        self.prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        logger.info("LLMIntentClassifier initialized")
    
    async def classify(self, query: str) -> Optional[LLMClassificationResult]:
        """
        Classify query intent.
        
        Returns:
            Classification result with requires_rag flag and optional response
        """
        if not query or not query.strip():
            return None
        
        try:
            messages = self.prompt.format_messages(query=query.strip())
            response = await self.llm.ainvoke(messages)
            
            content = response.content if hasattr(response, 'content') else str(response)
            parsed = self._extract_json(content)
            
            if not parsed:
                logger.warning(f"Failed to parse classifier response: {content}")
                return None
            
            result = LLMClassificationResult(
                requires_rag=parsed.get("requires_rag", True),
                confidence=float(parsed.get("confidence", 0.5)),
                response=parsed.get("response", "")
            )
            
            logger.info(
                f"Classified: requires_rag={result.requires_rag}, "
                f"confidence={result.confidence:.2f}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            return None
    
    def _extract_json(self, content: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        import re
        # Try markdown code blocks
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try finding any JSON object
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None


# Factory function
_classifier_instance = None

def get_llm_intent_classifier() -> Optional[LLMIntentClassifier]:
    """Get or create LLM intent classifier instance."""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = LLMIntentClassifier()
    
    return _classifier_instance
