"""
Conversation request handlers.

Handlers delegate to service layer for:
- Creating conversations
- Retrieving conversations and messages
- Listing user conversations with pagination
- Updating conversation metadata
- Soft deleting conversations
- Generating AI responses (with context retrieval and LLM routing)

Service layer handles:
- Business logic (query validation, authorization)
- Serialization (model to dict)
- Transaction management
- Error handling
- LLM orchestration (context, history, routing, generation)
"""

import logging
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation import ConversationService, get_conversation_response_service
from app.models.user_permission import PermissionLevel
from app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# CONVERSATION MANAGEMENT HANDLERS
# ============================================================================

async def handle_create_conversation(
    user_id: int,
    title: str,
    session: AsyncSession
) -> dict:
    """
    Handle create conversation request.
    
    Args:
        user_id: User ID creating the conversation
        title: Conversation title
        session: Database session
        
    Returns:
        Dict with conversation data or error
    """
    logger.info(f"Creating conversation for user {user_id}: {title}")
    service = ConversationService(session)
    return await service.create_conversation(user_id=user_id, title=title)


async def handle_get_conversation(
    conversation_id: str,
    user_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle get conversation request.
    
    Args:
        conversation_id: Conversation ID to retrieve
        user_id: User ID (for authorization)
        session: Database session
        
    Returns:
        Dict with conversation data or error
    """
    logger.info(f"Getting conversation {conversation_id} for user {user_id}")
    service = ConversationService(session)
    return await service.get_conversation_dict(conversation_id, user_id)


async def handle_list_conversations(
    user_id: int,
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """
    Handle list conversations request.
    
    Args:
        user_id: User ID to list conversations for
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        Dict with conversations list and pagination info
    """
    logger.info(f"Listing conversations for user {user_id} with limit={limit}, offset={offset}")
    service = ConversationService(session)
    return await service.list_user_conversations(user_id=user_id, limit=limit, offset=offset)


async def handle_update_conversation(
    conversation_id: str,
    user_id: int,
    title: Optional[str],
    session: AsyncSession
) -> dict:
    """
    Handle update conversation request.
    
    Args:
        conversation_id: Conversation ID to update
        user_id: User ID (for authorization)
        title: New title (optional)
        session: Database session
        
    Returns:
        Dict with updated conversation or error
    """
    logger.info(f"Updating conversation {conversation_id} for user {user_id}")
    service = ConversationService(session)
    return await service.update_conversation(conversation_id=conversation_id, user_id=user_id, title=title)


async def handle_soft_delete_conversation(
    conversation_id: str,
    user_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle soft delete conversation request.
    
    Args:
        conversation_id: Conversation ID to delete
        user_id: User ID (for authorization)
        session: Database session
        
    Returns:
        Dict with success status or error
    """
    logger.info(f"Soft deleting conversation {conversation_id} for user {user_id}")
    service = ConversationService(session)
    return await service.soft_delete_conversation(conversation_id, user_id)


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def handle_add_message(
    conversation_id: str,
    user_id: int,
    role: str,
    content: str,
    token_count: Optional[int],
    meta: Optional[dict],
    session: AsyncSession
) -> dict:
    """
    Handle add message to conversation request.
    
    Args:
        conversation_id: Conversation ID to add message to
        user_id: User ID (for authorization)
        role: Message role (USER, ASSISTANT, SYSTEM)
        content: Message content
        token_count: Optional token count
        meta: Optional metadata (sources, citations, etc.)
        session: Database session
        
    Returns:
        Dict with message data or error
    """
    logger.info(f"Adding message to conversation {conversation_id}")
    
    # Validate role
    try:
        from app.models.message import MessageRole
        role_enum = MessageRole[role.upper()]
    except KeyError:
        logger.warning(f"Invalid role: {role}")
        return {
            "success": False,
            "error": f"Invalid role. Must be one of: USER, ASSISTANT, SYSTEM",
            "message": None
        }
    
    service = ConversationService(session)
    return await service.add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role_enum,
        content=content,
        token_count=token_count,
        meta=meta
    )


async def handle_get_messages(
    conversation_id: str,
    user_id: int,
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """
    Handle get messages request (reverse chronological pagination).
    
    Args:
        conversation_id: Conversation ID to get messages from
        user_id: User ID (for authorization)
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        Dict with messages list and pagination info
    """
    logger.info(f"Getting messages for conversation {conversation_id} with limit={limit}, offset={offset}")
    service = ConversationService(session)
    return await service.get_messages(
        conversation_id=conversation_id,
        user_id=user_id,
        limit=limit,
        offset=offset
    )


async def handle_get_conversation_context(
    conversation_id: str,
    user_id: int,
    last_n: int,
    session: AsyncSession
) -> dict:
    """
    Handle get conversation context for LLM request.
    
    Returns the last N messages in chronological order for LLM context.
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for authorization)
        last_n: Number of recent messages to retrieve
        session: Database session
        
    Returns:
        Dict with context messages or error
    """
    logger.info(f"Getting context for conversation {conversation_id} (last {last_n} messages)")
    service = ConversationService(session)
    return await service.get_conversation_context(
        conversation_id=conversation_id,
        user_id=user_id,
        last_n=last_n
    )


# ============================================================================
# AI RESPONSE GENERATION HANDLERS
# ============================================================================

async def handle_generate_response(
    conversation_id: str,
    user_id: int,
    user_query: str,
    user: User,
    session: AsyncSession,
    stream: bool = True
) -> dict:
    """
    Handle AI response generation for user query.
    
    Complete flow:
    1. Validate and save user message
    2. Retrieve context from vector store
    3. Load conversation history from cache
    4. Route to appropriate LLM based on security
    5. Generate response (streaming or complete)
    6. Cache messages and save to database
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        user_query: User's query text
        user: User object with permission information
        session: Database session
        stream: Whether to stream the response
        
    Returns:
        Dict with success status, messages, and optional stream generator
    """
    logger.info(f"Generating AI response for conversation {conversation_id}")
    
    # Get user's effective clearance level
    user_clearance = PermissionLevel.GENERAL
    if user.permission:
        user_clearance = user.permission.effective_permission_level
    
    # Get response service
    response_service = get_conversation_response_service(session)
    
    # Generate response with security filtering
    return await response_service.generate_response(
        conversation_id=conversation_id,
        user_id=user_id,
        user_query=user_query,
        user_clearance=user_clearance,
        user_department_id=user.department_id,
        stream=stream
    )


async def handle_stream_response(
    conversation_id: str,
    user_id: int,
    user_query: str,
    user: User,
    session: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Handle streaming AI response generation.
    
    Convenience wrapper for handle_generate_response with streaming enabled.
    Returns async generator that yields response chunks.
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        user_query: User's query text
        user: User object with permission information
        session: Database session
        
    Yields:
        Response chunks as they're generated
    """
    result = await handle_generate_response(
        conversation_id=conversation_id,
        user_id=user_id,
        user_query=user_query,
        user=user,
        session=session,
        stream=True
    )
    
    if result["success"] and result.get("streaming"):
        async for chunk in result["generator"]:
            yield chunk
    else:
        # If generation failed, yield error message
        error_msg = result.get("error", "Unknown error occurred")
        yield f"Error: {error_msg}"
