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
        default="You are a knowledgeable assistant. Answer questions based on your knowledge base. If you don't know the answer, say 'I don't have that information.'",
        env="RAG_SYSTEM_PROMPT"
    )
    
    # Response when no relevant context
    NO_CONTEXT_RESPONSE: str = Field(
        default="I don't have that information in my knowledge base.",
        env="NO_CONTEXT_RESPONSE"
    )


def get_prompt_settings() -> PromptSettings:
    """Get prompt settings instance."""
    return PromptSettings()

