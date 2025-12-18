"""
Query Decomposer

Simple query optimizer that restructures queries for better retrieval.
Breaks down complex questions into searchable components.
"""

import json
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate

from app.core import get_logger
from app.services.llm.classifier_llm import get_classifier_llm
from app.schemas.llm_classifier import QueryDecompositionResult

logger = get_logger(__name__)


DECOMPOSITION_PROMPT = """You are a query optimizer for a RAG system. Your job:

1. For SIMPLE queries: Restructure to be more explicit and search-friendly
2. For COMPLEX queries: Break into separate searchable sub-queries (max 3-5)

Make queries clear, specific, and optimized for semantic search.

Return JSON:
{
    "queries": ["query1", "query2", ...]  // Max 5, ideally 3
}

Examples:

Query: "What's the vacation policy?"
{
    "queries": ["What is the company vacation policy and how many days are provided"]
}

Query: "How do I apply for leave and what's the approval process?"
{
    "queries": [
        "How do I submit a leave application",
        "What is the leave approval process and timeline"
    ]
}

Query: "Tell me about ML"
{
    "queries": ["What is machine learning and how does it work"]
}

Query: "{query}"

Return JSON only:"""


class QueryDecomposer:
    """Simple query decomposer."""
    
    def __init__(self):
        """Initialize with pre-initialized LLM from startup."""
        self.llm = get_classifier_llm()
        if not self.llm:
            logger.warning("Decomposer LLM not available - decomposition disabled")
        
        self.prompt = ChatPromptTemplate.from_template(DECOMPOSITION_PROMPT)
        logger.info("QueryDecomposer initialized")
    
    async def decompose(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Decompose/restructure a query.
        
        Returns:
            Decomposition result with list of optimized queries
        """
        if not query or not query.strip():
            return None
        
        try:
            messages = self.prompt.format_messages(query=query.strip())
            response = await self.llm.ainvoke(messages)
            
            content = response.content if hasattr(response, 'content') else str(response)
            parsed = self._extract_json(content)
            
            if not parsed or "queries" not in parsed:
                logger.warning(f"Failed to parse decomposer response: {content}")
                return None
            
            queries = parsed["queries"][:5]  # Limit to 5
            
            result = QueryDecompositionResult(queries=queries)
            
            logger.info(f"Query decomposed into {len(queries)} sub-queries")
            
            return result
        
        except Exception as e:
            logger.error(f"Decomposition failed: {e}", exc_info=True)
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
    
    def get_primary_query(self, result: QueryDecompositionResult) -> str:
        """Get the first (primary) query."""
        return result.queries[0] if result.queries else ""
    
    def get_all_queries(self, result: QueryDecompositionResult) -> List[str]:
        """Get all decomposed queries."""
        return result.queries


# Factory function
_decomposer_instance = None

def get_query_decomposer() -> Optional[QueryDecomposer]:
    """Get or create query decomposer instance."""
    global _decomposer_instance
    
    if _decomposer_instance is None:
        _decomposer_instance = QueryDecomposer()
    
    return _decomposer_instance
