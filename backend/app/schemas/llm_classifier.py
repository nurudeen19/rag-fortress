"""
Schemas for LLM-based classifier and decomposer.

Simple schemas with detailed descriptions for structured output.
"""

from typing import List
from pydantic import BaseModel, Field


class LLMClassificationResult(BaseModel):
    """
    Classification result from LLM for query intent analysis.
    
    Used with structured output to classify queries as requiring RAG or not.
    """
    requires_rag: bool = Field(
        ..., 
        description="Whether the query needs document retrieval (RAG pipeline). "
                    "True for knowledge questions, policies, facts. "
                    "False for greetings, thanks, small talk."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score from 0.0 to 1.0 indicating certainty of classification"
    )
    response: str = Field(
        default="", 
        description="Direct response for non-RAG queries (greetings, pleasantries). "
                    "Empty string for RAG queries - system will retrieve documents instead."
    )


class QueryDecompositionResult(BaseModel):
    """
    Query decomposition result for optimizing semantic search.
    
    Used with structured output to restructure/break down queries.
    """
    queries: List[str] = Field(
        ..., 
        max_length=5, 
        description="List of optimized search queries. "
                    "For simple queries: 1 expanded/clarified query. "
                    "For complex queries: 2-5 focused sub-queries. "
                    "Each query should be self-contained and searchable."
    )
