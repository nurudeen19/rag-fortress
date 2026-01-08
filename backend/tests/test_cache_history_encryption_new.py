"""
Tests for conversation history caching with optional encryption.

Tests two caching strategies:
1. Plaintext cache with configurable TTL (fast, brief exposure)
2. Encrypted cache with configurable TTL (slow, secure at rest)
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.encryption import encrypt_conversation_message, decrypt_conversation_message


@pytest.mark.asyncio
async def test_cache_history_plaintext_mode():
    """When encryption disabled, history should be cached as plaintext JSON."""
    from app.services.conversation.service import ConversationService
    
    mock_session = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.set = AsyncMock()
    
    cache_settings = MagicMock()
    cache_settings.ENABLE_CACHE_HISTORY_ENCRYPTION = False
    cache_settings.CACHE_TTL_HISTORY = 3600
    
    with patch('app.services.conversation.service.get_cache', return_value=mock_cache):
        with patch('app.services.conversation.service.settings') as mock_settings:
            mock_settings.cache_settings = cache_settings
            
            service = ConversationService(mock_session)
            
            conversation_id = "conv-123"
            history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]

            await service._cache_history(conversation_id, history)

            # Verify cache.set was called
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            
            # Extract the cached data
            cached_data = call_args[0][1]
            
            # Should be plaintext JSON
            cached_dict = json.loads(cached_data)
            assert cached_dict == history
            
            # Verify TTL was passed
            assert call_args[1]['ttl'] == 3600


@pytest.mark.asyncio
async def test_cache_history_encrypted_mode():
    """When encryption enabled, history should be encrypted before caching."""
    from app.services.conversation.service import ConversationService
    
    mock_session = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.set = AsyncMock()
    
    cache_settings = MagicMock()
    cache_settings.ENABLE_CACHE_HISTORY_ENCRYPTION = True
    cache_settings.CACHE_TTL_HISTORY = 3600
    
    with patch('app.services.conversation.service.get_cache', return_value=mock_cache):
        with patch('app.services.conversation.service.settings') as mock_settings:
            mock_settings.cache_settings = cache_settings
            
            service = ConversationService(mock_session)
            
            conversation_id = "conv-123"
            history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]

            await service._cache_history(conversation_id, history)

            # Verify cache.set was called
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            
            # Extract the cached data
            cached_data = call_args[0][1]
            
            # Should be encrypted (starts with v1:)
            assert cached_data.startswith("v1:")
            
            # Decrypt and verify
            decrypted_json = decrypt_conversation_message(cached_data)
            cached_dict = json.loads(decrypted_json)
            assert cached_dict == history
            
            # Verify TTL was passed
            assert call_args[1]['ttl'] == 3600


@pytest.mark.asyncio
async def test_cache_history_custom_ttl():
    """Custom TTL from settings should be used instead of hardcoded value."""
    from app.services.conversation.service import ConversationService
    
    mock_session = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.set = AsyncMock()
    
    custom_ttl = 3600  # 1 hour
    cache_settings = MagicMock()
    cache_settings.ENABLE_CACHE_HISTORY_ENCRYPTION = False
    cache_settings.CACHE_TTL_HISTORY = custom_ttl
    
    with patch('app.services.conversation.service.get_cache', return_value=mock_cache):
        with patch('app.services.conversation.service.settings') as mock_settings:
            mock_settings.cache_settings = cache_settings
            
            service = ConversationService(mock_session)
            
            conversation_id = "conv-123"
            history = [{"role": "user", "content": "Test"}]

            await service._cache_history(conversation_id, history)

            call_args = mock_cache.set.call_args
            assert call_args[1]['ttl'] == custom_ttl


@pytest.mark.asyncio
async def test_cache_exchange_with_encryption():
    """When encryption enabled, exchange should be encrypted before caching."""
    from app.services.conversation.service import ConversationService
    
    mock_session = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)  # No existing cache
    mock_cache.set = AsyncMock()
    
    cache_settings = MagicMock()
    cache_settings.ENABLE_CACHE_HISTORY_ENCRYPTION = True
    cache_settings.CACHE_TTL_HISTORY = 3600
    
    app_settings = MagicMock()
    app_settings.CONVERSATION_HISTORY_TURNS = 3
    
    conversation_id = "conv-123"
    user_msg = "What is AI?"
    assistant_msg = "AI is artificial intelligence."
    
    with patch('app.services.conversation.service.get_cache', return_value=mock_cache):
        with patch('app.services.conversation.service.settings') as mock_settings:
            mock_settings.cache_settings = cache_settings
            mock_settings.CONVERSATION_HISTORY_TURNS = 3
            
            service = ConversationService(mock_session)

            await service.cache_conversation_exchange(
                conversation_id=conversation_id,
                user_msg=user_msg,
                assistant_msg=assistant_msg
            )

            call_args = mock_cache.set.call_args
            cached_data = call_args[0][1]
            
            # Should be encrypted
            assert cached_data.startswith("v1:")
            
            # Decrypt and verify
            decrypted_json = decrypt_conversation_message(cached_data)
            cached_dict = json.loads(decrypted_json)
            assert len(cached_dict) == 2
            assert cached_dict[0]["content"] == user_msg
            assert cached_dict[1]["content"] == assistant_msg


def test_encryption_decryption_roundtrip():
    """Verify encryption/decryption roundtrip for history data."""
    history = [
        {"role": "user", "content": "Complex question with special chars: @#$%^&*()"},
        {"role": "assistant", "content": "Answer with unicode: 你好 مرحبا שלום"}
    ]
    
    # Encrypt
    history_json = json.dumps(history)
    encrypted = encrypt_conversation_message(history_json)
    
    # Verify encryption format
    assert encrypted.startswith("v1:")
    assert len(encrypted) > len(history_json)
    
    # Decrypt
    decrypted_json = decrypt_conversation_message(encrypted)
    decrypted_history = json.loads(decrypted_json)
    
    # Verify roundtrip
    assert decrypted_history == history
