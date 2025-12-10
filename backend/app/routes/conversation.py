"""
Conversation API routes.

Routes delegate request handling to handlers for business logic separation.
Requires authentication for access.

Endpoints:
- GET  /api/v1/conversations - List user conversations (paginated)
- POST /api/v1/conversations - Create new conversation
- GET  /api/v1/conversations/{conversation_id} - Get conversation details
- PATCH /api/v1/conversations/{conversation_id} - Update conversation
- DELETE /api/v1/conversations/{conversation_id} - Soft delete conversation
- GET  /api/v1/conversations/{conversation_id}/messages - Get paginated messages
- POST /api/v1/conversations/{conversation_id}/messages - Add message
- GET  /api/v1/conversations/{conversation_id}/context - Get LLM context
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.core import get_logger
from app.utils.demo_mode import prevent_in_demo_mode
from app.utils.rate_limiter import get_limiter, get_conversation_rate_limit
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    MessageAddRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    ConversationContextResponse,
    SuccessResponse,
    ConversationGenerateRequest,
)
from app.handlers.conversation import (
    handle_create_conversation,
    handle_get_conversation,
    handle_list_conversations,
    handle_update_conversation,
    handle_soft_delete_conversation,
    handle_add_message,
    handle_get_messages,
    handle_get_conversation_context,
    handle_stream_response,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
limiter = get_limiter()


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new conversation.
    
    Requires authentication.
    """
    result = await handle_create_conversation(
        user_id=current_user.id,
        title=request.title,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create conversation")
        )
    
    return ConversationResponse(**result["conversation"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all conversations for the current user with pagination.
    
    Requires authentication.
    """
    result = await handle_list_conversations(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list conversations")
        )
    
    return ConversationListResponse(
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        conversations=[ConversationResponse(**c) for c in result["conversations"]]
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get conversation details by ID.
    
    Requires authentication and authorization (conversation must belong to user).
    """
    result = await handle_get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Conversation not found")
        )
    
    return ConversationResponse(**result["conversation"])


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update conversation (title and/or category).
    
    Requires authentication and authorization (conversation must belong to user).
    """
    result = await handle_update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=request.title,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to update conversation")
        )
    
    return ConversationResponse(**result["conversation"])


@router.delete("/{conversation_id}", response_model=SuccessResponse)
@prevent_in_demo_mode("Delete conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Soft delete a conversation.
    
    Requires authentication and authorization (conversation must belong to user).
    The conversation is soft-deleted and marked as deleted but not physically removed.
    """
    result = await handle_soft_delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Failed to delete conversation")
        )
    
    return SuccessResponse(message=result["message"])


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get paginated messages for a conversation (reverse chronological order).
    
    Requires authentication and authorization (conversation must belong to user).
    Messages are returned newest first.
    """
    result = await handle_get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to get messages")
        )
    
    return MessageListResponse(
        conversation=ConversationResponse(**result["conversation"]),
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        messages=[MessageResponse(**m) for m in result["messages"]]
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    conversation_id: str,
    request: MessageAddRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Add a message to a conversation.
    
    Requires authentication and authorization (conversation must belong to user).
    """
    result = await handle_add_message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        role=request.role,
        content=request.content,
        token_count=request.token_count,
        meta=request.meta,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "Invalid" in result.get("error", "") else status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Failed to add message")
        )
    
    return MessageResponse(**result["message"])


@router.get("/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: str,
    last_n: int = Query(6, ge=1, le=50, description="Number of recent messages to retrieve"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get conversation context for LLM (last N messages in chronological order).
    
    Requires authentication and authorization (conversation must belong to user).
    
    This endpoint returns the most recent messages in chronological order,
    which is suitable for feeding into an LLM for context.
    
    Query Parameters:
    - last_n: Number of recent messages to include (1-50, default: 6)
    """
    result = await handle_get_conversation_context(
        conversation_id=conversation_id,
        user_id=current_user.id,
        last_n=last_n,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Failed to get conversation context")
        )
    
    return ConversationContextResponse(**result)


@router.post("/{conversation_id}/respond", response_class=StreamingResponse)
@limiter.limit(get_conversation_rate_limit())
async def stream_conversation_response(
    http_request: Request,
    conversation_id: str,
    request: ConversationGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Stream AI response tokens for a conversation using Server-Sent Events.
    
    Rate limited to prevent RAG pipeline abuse.
    """

    async def event_generator():
        try:
            async for chunk in handle_stream_response(
                conversation_id=conversation_id,
                user_id=current_user.id,
                user_query=request.message,
                user=current_user,
                session=session
            ):
                payload = chunk if isinstance(chunk, dict) else {"type": "token", "content": str(chunk)}
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as exc:
            error_payload = {"type": "error", "message": str(exc)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
