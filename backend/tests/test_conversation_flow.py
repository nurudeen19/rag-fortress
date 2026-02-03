"""Integration test covering the full conversation response flow."""

import pytest

from app.core.database import get_db_manager
from app.core.cache import initialize_cache
from app.services.conversation.service import ConversationService
from app.services.conversation.response_service import ConversationResponseService


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Integration test requires full database setup with async context - greenlet error with user clearance cache")
async def test_conversation_flow_integrates_with_llm_and_history():
    """Simulate a user chat request end-to-end (cache, context, routing, persistence)."""
    
    user_id = 1  # Use an existing user from seed data

    # Initialize cache (required before using conversation services)
    await initialize_cache()
    
    # Get database manager and session
    manager = await get_db_manager()
    session = await manager.get_session()
    
    try:
        # Create a conversation for this user
        conversation_service = ConversationService(session)
        list_result = await conversation_service.list_user_conversations(
            user_id=user_id,
            limit=1,
            offset=0
        )
        
        if not list_result["success"]:
            # If listing fails, create new conversation
            create_result = await conversation_service.create_conversation(
                user_id=user_id,
                title="Integration Flow Test"
            )
            assert create_result["success"], f"Failed to create conversation: {create_result.get('error')}"
            conversation_id = create_result["conversation"]["id"]
        elif list_result["conversations"]:
            conversation_id = list_result["conversations"][0]["id"]
        else:
            # No conversations exist, create one
            create_result = await conversation_service.create_conversation(
                user_id=user_id,
                title="Integration Flow Test"
            )
            assert create_result["success"], f"Failed to create conversation: {create_result.get('error')}"
            conversation_id = create_result["conversation"]["id"]

        # Generate response (non-streaming for easier testing)
        response_service = ConversationResponseService(session)
        response = await response_service.generate_response(
            conversation_id=conversation_id,
            user_id=user_id,
            user_query="What are the key next steps for this project?",
            stream=False
        )

        # Verify response was generated successfully
        assert response["success"], f"Response failed: {response.get('error')} - {response.get('message')}"
        assert isinstance(response.get("response"), str), "Response should be a string"
        assert response["response"].strip(), "Response should not be empty"

        # Verify messages were persisted to database
        messages_result = await conversation_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=10,
            offset=0
        )

        assert messages_result["success"], f"Failed to load messages: {messages_result.get('error')}"
        assert messages_result["total"] >= 2, f"Expected at least 2 messages, got {messages_result['total']}"
        
        print(f"[PASS] Test passed for user {user_id}: {messages_result['total']} messages persisted")
    
    finally:
        # Ensure session is closed
        await session.close()