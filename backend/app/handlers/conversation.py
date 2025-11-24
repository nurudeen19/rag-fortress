"""
Conversation request handlers.

Handlers manage business logic for:
- Creating conversations
- Retrieving conversations and messages
- Listing user conversations with pagination
- Updating conversation metadata
- Soft deleting conversations
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation_service import ConversationService

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
    try:
        logger.info(f"Creating conversation for user {user_id}: {title}")
        
        service = ConversationService(session)
        conversation = await service.create_conversation(
            user_id=user_id,
            title=title
        )
        
        await session.commit()
        
        return {
            "success": True,
            "conversation": {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "message_count": conversation.message_count,
                "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "is_deleted": conversation.is_deleted,
            }
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "conversation": None
        }


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
    try:
        logger.info(f"Getting conversation {conversation_id} for user {user_id}")
        
        service = ConversationService(session)
        conversation = await service.get_conversation(conversation_id, user_id)
        
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found",
                "conversation": None
            }
        
        return {
            "success": True,
            "conversation": {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "message_count": conversation.message_count,
                "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                "is_deleted": conversation.is_deleted,
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "conversation": None
        }


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
    try:
        logger.info(f"Listing conversations for user {user_id} with limit={limit}, offset={offset}")
        
        service = ConversationService(session)
        conversations, total = await service.list_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        conversation_list = [
            {
                "id": c.id,
                "user_id": c.user_id,
                "title": c.title,
                "message_count": c.message_count,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "is_deleted": c.is_deleted,
            }
            for c in conversations
        ]
        
        logger.info(f"Retrieved {len(conversation_list)} conversations for user {user_id}")
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "conversations": conversation_list
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "conversations": [],
            "total": 0
        }


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
    try:
        logger.info(f"Updating conversation {conversation_id} for user {user_id}")
        
        service = ConversationService(session)
        
        # Verify conversation exists and belongs to user
        conversation = await service.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found",
                "conversation": None
            }
        
        updated_conversation = await service.update_conversation(
            conversation_id=conversation_id,
            title=title
        )
        
        await session.commit()
        
        return {
            "success": True,
            "conversation": {
                "id": updated_conversation.id,
                "user_id": updated_conversation.user_id,
                "title": updated_conversation.title,
                "message_count": updated_conversation.message_count,
                "last_message_at": updated_conversation.last_message_at.isoformat() if updated_conversation.last_message_at else None,
                "created_at": updated_conversation.created_at.isoformat() if updated_conversation.created_at else None,
                "updated_at": updated_conversation.updated_at.isoformat() if updated_conversation.updated_at else None,
                "is_deleted": updated_conversation.is_deleted,
            }
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "conversation": None
        }


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
    try:
        logger.info(f"Soft deleting conversation {conversation_id} for user {user_id}")
        
        service = ConversationService(session)
        
        # Verify conversation exists and belongs to user
        conversation = await service.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found"
            }
        
        await service.soft_delete_conversation(conversation_id, user_id)
        await session.commit()
        
        logger.info(f"Conversation {conversation_id} soft deleted")
        
        return {
            "success": True,
            "message": f"Conversation deleted successfully"
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


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
    try:
        logger.info(f"Adding message to conversation {conversation_id}")
        
        service = ConversationService(session)
        
        # Verify conversation exists and belongs to user
        conversation = await service.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found",
                "message": None
            }
        
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
        
        message = await service.add_message(
            conversation_id=conversation_id,
            role=role_enum,
            content=content,
            token_count=token_count,
            meta=meta
        )
        
        await session.commit()
        
        return {
            "success": True,
            "message": {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role.value,
                "content": message.content,
                "token_count": message.token_count,
                "meta": message.meta,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "updated_at": message.updated_at.isoformat() if message.updated_at else None,
            }
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error adding message: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": None
        }


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
    try:
        logger.info(f"Getting messages for conversation {conversation_id} with limit={limit}, offset={offset}")
        
        service = ConversationService(session)
        
        # Verify conversation exists and belongs to user
        conversation = await service.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found",
                "messages": [],
                "total": 0
            }
        
        messages, total = await service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        message_list = [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "role": m.role.value,
                "content": m.content,
                "token_count": m.token_count,
                "meta": m.meta,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in messages
        ]
        
        logger.info(f"Retrieved {len(message_list)} messages for conversation {conversation_id}")
        
        # Convert conversation to dict
        conversation_dict = {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "message_count": conversation.message_count,
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "is_deleted": conversation.is_deleted
        }
        
        return {
            "success": True,
            "conversation": conversation_dict,
            "total": total,
            "limit": limit,
            "offset": offset,
            "messages": message_list
        }
        
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "messages": [],
            "total": 0
        }


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
    try:
        logger.info(f"Getting context for conversation {conversation_id} (last {last_n} messages)")
        
        service = ConversationService(session)
        
        # Verify conversation exists and belongs to user
        conversation = await service.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return {
                "success": False,
                "error": "Conversation not found",
                "context": [],
                "conversation_id": conversation_id
            }
        
        messages = await service.get_conversation_context(
            conversation_id=conversation_id,
            user_id=user_id,
            last_n=last_n
        )
        
        context = [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
        
        logger.info(f"Retrieved context with {len(context)} messages for conversation {conversation_id}")
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "context": context,
            "message_count": len(context)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "context": [],
            "conversation_id": conversation_id
        }
