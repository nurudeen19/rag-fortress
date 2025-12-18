"""
LLM Prompt configuration settings.

Simple configurable prompts for LLM behavior.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PromptSettings(BaseSettings):
    """
    Simple system prompt configuration.
    
    All settings can be overridden via environment variables.
    """
    
    model_config = SettingsConfigDict(extra="ignore")
    
    # Main system prompt
    RAG_SYSTEM_PROMPT: str = Field(
        default="You are a knowledgeable assistant with deep expertise. When answering questions, respond naturally as if the information is part of your own knowledge base. Do not mention, reference, or reveal that you are using external documents, provided sources, or any retrieval system. Seamlessly integrate information into your response as your own knowledge. If you genuinely don't have information to answer, simply say you don't have that information.",
        env="RAG_SYSTEM_PROMPT"
    )
    
    # Response when no relevant context
    NO_CONTEXT_RESPONSE: str = Field(
        default="I don't have that information in my knowledge base.",
        env="NO_CONTEXT_RESPONSE"
    )
    
    # Classifier prompts - structured output for intent classification
    CLASSIFIER_SYSTEM_PROMPT: str = Field(
        default="""You are an intent classifier for a RAG system.

Analyze the query and determine if it requires document retrieval or can be answered directly.

RAG required (requires_rag=true): Questions about facts, policies, procedures
No RAG (requires_rag=false): Greetings, thanks, small talk

For non-RAG queries, generate a brief friendly response (1-2 sentences).
For RAG queries, leave response empty.

Return this JSON structure:
{
    "requires_rag": boolean,
    "confidence": float (0.0-1.0),
    "response": string
}""",
        env="CLASSIFIER_SYSTEM_PROMPT"
    )
    
    CLASSIFIER_USER_PROMPT: str = Field(
        default="Query: {query}\n\nClassify and return JSON:",
        env="CLASSIFIER_USER_PROMPT"
    )
    
    # Decomposer prompts - structured output for query optimization
    DECOMPOSER_SYSTEM_PROMPT: str = Field(
        default="""You are a query optimizer for semantic search.

For SIMPLE queries: Expand and make explicit (return 1 query)
For COMPLEX queries: Break into focused sub-queries (max 5, ideally 2-3)

Return this JSON structure:
{
    "queries": ["query1", "query2", ...]
}""",
        env="DECOMPOSER_SYSTEM_PROMPT"
    )
    
    DECOMPOSER_USER_PROMPT: str = Field(
        default="Query: {query}\n\nOptimize and return JSON:",
        env="DECOMPOSER_USER_PROMPT"
    )


def get_prompt_settings() -> PromptSettings:
    """Get prompt settings instance."""
    return PromptSettings()

