"""
Pydantic schemas for conversation API requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation."""
    title: str = Field(..., min_length=1, max_length=255)


class ConversationUpdateRequest(BaseModel):
    """Request to update a conversation."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)


class MessageAddRequest(BaseModel):
    """Request to add a message to a conversation."""
    role: str = Field(..., description="USER, ASSISTANT, or SYSTEM")
    content: str = Field(..., min_length=1)
    token_count: Optional[int] = Field(None, ge=0)
    meta: Optional[dict] = Field(None, description="JSON metadata (sources, citations, etc.)")


class ConversationGenerateRequest(BaseModel):
    """Request body for AI response generation."""
    message: str = Field(..., min_length=1, max_length=4000)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ConversationResponse(BaseModel):
    """Response containing conversation details."""
    id: str
    title: str
    message_count: int
    last_message_at: Optional[str]
    created_at: Optional[str]


class ConversationListResponse(BaseModel):
    """Response for conversation list with pagination."""
    total: int
    limit: int
    offset: int
    conversations: list[ConversationResponse]


class MessageResponse(BaseModel):
    """Response containing message details."""
    id: str
    conversation_id: str
    role: str
    content: str
    token_count: Optional[int]
    meta: Optional[dict]
    created_at: Optional[str]


class MessageListResponse(BaseModel):
    """Response for message list with pagination."""
    conversation: ConversationResponse
    total: int
    limit: int
    offset: int
    messages: list[MessageResponse]


class ConversationContextResponse(BaseModel):
    """Response containing conversation context for LLM."""
    conversation_id: str
    message_count: int
    context: list[dict]


class SuccessResponse(BaseModel):
    """Simple success response."""
    message: str
