"""
Query Decomposer

Uses structured output to optimize queries for semantic search.
"""

from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate

from app.core import get_logger
from app.services.llm.classifier_llm import get_classifier_llm
from app.schemas.llm_classifier import QueryDecompositionResult
from app.config.settings import settings

logger = get_logger(__name__)


class QueryDecomposer:
    """Query decomposer with structured output."""
    
    def __init__(self):
        """Initialize with pre-initialized LLM from startup."""
        self.llm = get_classifier_llm()
        if not self.llm:
            logger.warning("Decomposer LLM not available - decomposition disabled")
            return
        
        # Use structured output with the schema
        try:
            self.structured_llm = self.llm.with_structured_output(QueryDecompositionResult)
        except Exception as e:
            logger.warning(f"Structured output not supported, falling back to JSON mode: {e}")
            self.structured_llm = self.llm
        
        # Create prompt from settings
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", settings.prompt_settings.DECOMPOSER_SYSTEM_PROMPT),
            ("user", settings.prompt_settings.DECOMPOSER_USER_PROMPT)
        ])
        
        logger.info("QueryDecomposer initialized with structured output")
    
    async def decompose(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Decompose/restructure a query using structured output.
        
        Args:
            query: User query to optimize
            
        Returns:
            Decomposition result with list of optimized queries
        """
        if not self.llm or not query or not query.strip():
            return None
        
        try:
            # Build and invoke chain with structured output
            chain = self.prompt | self.structured_llm
            result = await chain.ainvoke({"query": query.strip()})
            
            # If structured output returned the model directly, use it
            if isinstance(result, QueryDecompositionResult):
                # Limit to max 5 queries
                if len(result.queries) > 5:
                    result.queries = result.queries[:5]
                
                logger.info(f"Decomposed into {len(result.queries)} queries")
                return result
            
            # Fallback: parse from dict if needed
            if isinstance(result, dict):
                decomp_result = QueryDecompositionResult(**result)
                if len(decomp_result.queries) > 5:
                    decomp_result.queries = decomp_result.queries[:5]
                return decomp_result
            
            logger.warning(f"Unexpected decomposer response type: {type(result)}")
            return None
            
        except Exception as e:
            logger.error(f"Decomposition failed: {e}", exc_info=True)
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
