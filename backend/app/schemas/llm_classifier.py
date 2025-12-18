"""
Schemas for LLM-based classifier and decomposer.

Simple, straightforward schemas for query processing.
"""

from typing import List
from pydantic import BaseModel, Field


class LLMClassificationResult(BaseModel):
    """Classification result from LLM."""
    requires_rag: bool = Field(..., description="Whether query needs RAG pipeline")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    response: str = Field(default="", description="Direct response for non-RAG queries")


class QueryDecompositionResult(BaseModel):
    """Query decomposition result."""
    queries: List[str] = Field(..., max_length=5, description="Decomposed queries (max 5)")
