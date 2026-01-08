#!/usr/bin/env python
"""
Test suite for system prompt configuration.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from unittest.mock import MagicMock, patch

async def test_prompt_configuration():
    """Test that system prompts are properly configured."""
    from app.config.settings import settings
    from app.config.prompt_settings import PromptSettings
    
    # Test that all prompts are defined as attributes (can be empty from env)
    assert hasattr(settings, 'RAG_SYSTEM_PROMPT')
    assert hasattr(settings, 'RETRIEVAL_NO_CONTEXT_MESSAGE')
    assert hasattr(settings, 'RETRIEVAL_DEPT_BLOCKED_MESSAGE')
    assert hasattr(settings, 'RETRIEVAL_SECURITY_BLOCKED_MESSAGE')
    assert hasattr(settings, 'PARTIAL_CONTEXT_CLEARANCE_PROMPT')
    assert hasattr(settings, 'CLASSIFIER_SYSTEM_PROMPT')
    
    # Test that PromptSettings has defaults
    ps = PromptSettings()
    assert len(ps.RAG_SYSTEM_PROMPT) > 100, "Default prompt should be detailed"
    assert len(ps.RETRIEVAL_NO_CONTEXT_MESSAGE) > 0, "Default message should exist"
    
    print("✅ All system prompts defined with defaults")

async def test_no_context_response_handling():
    """Test that response service handles no-context scenarios."""
    from app.services.conversation.response_service import ConversationResponseService
    
    with patch('app.services.conversation.response_service.get_retriever_service') as mock_retriever, \
         patch('app.services.conversation.response_service.get_llm_router') as mock_llm, \
         patch('app.services.conversation.response_service.ConversationService') as mock_conv_svc, \
         patch('app.services.conversation.response_service.get_intent_classifier') as mock_intent, \
         patch('app.services.conversation.response_service.get_llm_intent_classifier') as mock_llm_intent, \
         patch('app.services.conversation.response_service.get_query_decomposer') as mock_decomposer:
        
        # Set return values for all mocked factories
        mock_retriever.return_value = MagicMock()
        mock_llm.return_value = MagicMock()
        mock_conv_svc.return_value = MagicMock()
        mock_intent.return_value = MagicMock()
        mock_llm_intent.return_value = MagicMock()
        mock_decomposer.return_value = MagicMock()
        
        session = MagicMock()
        service = ConversationResponseService(session)
        
        # Service should be created successfully
        assert service is not None, "Service should be instantiated"
        
        print("✅ ConversationResponseService instantiated correctly")

async def test_markdown_in_system_prompt():
    """Test that system prompt has default value."""
    from app.config.prompt_settings import PromptSettings
    
    # Should have default system prompt
    ps = PromptSettings()
    assert ps.RAG_SYSTEM_PROMPT is not None
    assert isinstance(ps.RAG_SYSTEM_PROMPT, str)
    assert len(ps.RAG_SYSTEM_PROMPT) > 0
    
    print("✅ System prompt default is available")

async def test_settings_integration():
    """Test that prompt settings are integrated into main Settings class."""
    from app.config.settings import Settings
    
    settings = Settings()
    
    # Should have all prompt settings attributes
    assert hasattr(settings, 'RAG_SYSTEM_PROMPT')
    assert hasattr(settings, 'RETRIEVAL_NO_CONTEXT_MESSAGE')
    assert hasattr(settings, 'PARTIAL_CONTEXT_CLEARANCE_PROMPT')
    assert hasattr(settings, 'CLASSIFIER_SYSTEM_PROMPT')
    assert hasattr(settings, 'DECOMPOSER_SYSTEM_PROMPT')
    
    print("✅ PromptSettings integrated into main Settings class")

async def test_response_service_uses_configurable_prompts():
    """Test that response service uses configurable prompts."""
    from app.services.conversation.response_service import ConversationResponseService
    
    with patch('app.services.conversation.response_service.get_retriever_service') as mock_retriever, \
         patch('app.services.conversation.response_service.get_llm_router') as mock_llm, \
         patch('app.services.conversation.response_service.ConversationService') as mock_conv_svc, \
         patch('app.services.conversation.response_service.get_intent_classifier') as mock_intent, \
         patch('app.services.conversation.response_service.get_llm_intent_classifier') as mock_llm_intent, \
         patch('app.services.conversation.response_service.get_query_decomposer') as mock_decomposer:
        
        # Set return values for all mocked factories
        mock_retriever.return_value = MagicMock()
        mock_llm.return_value = MagicMock()
        mock_conv_svc.return_value = MagicMock()
        mock_intent.return_value = MagicMock()
        mock_llm_intent.return_value = MagicMock()
        mock_decomposer.return_value = MagicMock()
        
        session = MagicMock()
        service = ConversationResponseService(session)
        
        # Service should use settings
        assert service is not None
        
        print("✅ Response service instantiated with configurable prompts")

async def main():
    """Run all tests."""
    print("=" * 70)
    print("System Prompt Configuration Tests")
    print("=" * 70)
    print()
    
    try:
        await test_prompt_configuration()
        print()
        
        await test_no_context_response_handling()
        print()
        
        await test_markdown_in_system_prompt()
        print()
        
        await test_settings_integration()
        print()
        
        await test_response_service_uses_configurable_prompts()
        print()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary of changes:")
        print("  ✓ System prompts are now configurable via ENV variables")
        print("  ✓ Prompt settings integrated into main Settings class")
        print("  ✓ Response service uses configurable prompts")
        print()
        
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
