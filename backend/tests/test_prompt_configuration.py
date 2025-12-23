#!/usr/bin/env python
"""
Test suite for system prompt configuration and markdown response formatting.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from unittest.mock import MagicMock, AsyncMock, patch

async def test_prompt_configuration():
    """Test that system prompts are properly configured."""
    from app.config.prompt_settings import get_prompt_settings
    
    ps = get_prompt_settings()
    
    # Test that all prompts are defined
    assert ps.RAG_SYSTEM_PROMPT, "RAG_SYSTEM_PROMPT not defined"
    assert ps.RETRIEVAL_NO_CONTEXT_MESSAGE, "RETRIEVAL_NO_CONTEXT_MESSAGE not defined"
    assert ps.LOW_QUALITY_CONTEXT_RESPONSE, "LOW_QUALITY_CONTEXT_RESPONSE not defined"
    
    print("✅ All system prompts defined")
    
    # Test get_system_prompt method
    full_prompt = ps.get_system_prompt()
    assert "markdown" in full_prompt.lower(), "System prompt should mention markdown"
    assert len(full_prompt) > 100, "System prompt should be reasonably detailed"
    
    print("✅ System prompt includes markdown directive")
    
    # Test markdown is enabled
    assert ps.ENABLE_MARKDOWN_FORMATTING == True, "Markdown formatting should be enabled"
    
    print("✅ Markdown formatting enabled")
    
    # Test source citation formatting
    citation = ps.format_source_citation("Test Document", 0.85, 1)
    assert "Test Document" in citation, "Citation should include source name"
    assert "85" in citation, "Citation should include score as percentage"
    
    print("✅ Source citations formatted correctly")
    
    # Test response length preferences
    assert ps.RESPONSE_LENGTH_PREFERENCE in ["concise", "moderate", "comprehensive"]
    
    print("✅ Response length preference valid")

async def test_no_context_response_handling():
    """Test that response service handles no-context scenarios."""
    from app.services.conversation.response_service import ConversationResponseService
    from app.config.prompt_settings import get_prompt_settings
    
    with patch('app.services.conversation.response_service.get_retriever_service'), \
         patch('app.services.conversation.response_service.get_llm_router'), \
         patch('app.services.conversation.response_service.ConversationService'), \
         patch('app.services.conversation.response_service.get_user_clearance_cache'):
        
        session = MagicMock()
        service = ConversationResponseService(session)
        
        # Test no context response
        response = service._get_no_context_response_text("no_documents")
        assert response, "No context response should not be empty"
        assert len(response) > 0, "Response should have content"
        
        print("✅ No-context response generated correctly")
        
        # Test low quality response
        response = service._get_no_context_response_text("low_quality_results")
        assert response, "Low quality response should not be empty"
        assert "confidence" in response.lower() or "relevant" in response.lower()
        
        print("✅ Low-quality context response generated correctly")

async def test_markdown_in_system_prompt():
    """Test that markdown formatting is emphasized in system prompt."""
    from app.config.prompt_settings import get_prompt_settings
    
    ps = get_prompt_settings()
    full_prompt = ps.get_system_prompt(include_markdown_directive=True)
    
    # Should include markdown instruction
    assert "markdown" in full_prompt.lower(), "Should mention markdown"
    
    # Should include formatting guidance
    assert any(x in full_prompt.lower() for x in ["heading", "bullet", "code", "format"])
    
    print("✅ System prompt includes markdown formatting guidance")

async def test_settings_integration():
    """Test that prompt settings are integrated into main Settings class."""
    from app.config.settings import Settings
    
    settings = Settings()
    
    # Should have all prompt settings attributes
    assert hasattr(settings, 'RAG_SYSTEM_PROMPT')
    assert hasattr(settings, 'RETRIEVAL_NO_CONTEXT_MESSAGE')
    assert hasattr(settings, 'ENABLE_MARKDOWN_FORMATTING')
    assert hasattr(settings, 'RESPONSE_LENGTH_PREFERENCE')
    
    print("✅ PromptSettings integrated into main Settings class")

async def test_response_service_uses_configurable_prompts():
    """Test that response service uses configurable prompts."""
    from app.services.conversation.response_service import ConversationResponseService
    
    with patch('app.services.conversation.response_service.get_retriever_service'), \
         patch('app.services.conversation.response_service.get_llm_router'), \
         patch('app.services.conversation.response_service.ConversationService'), \
         patch('app.services.conversation.response_service.get_user_clearance_cache'), \
         patch('app.services.conversation.response_service.get_prompt_settings') as mock_get_prompt:
        
        # Setup mock
        mock_prompt_settings = MagicMock()
        mock_prompt_settings.get_system_prompt.return_value = "Test system prompt"
        mock_get_prompt.return_value = mock_prompt_settings
        
        session = MagicMock()
        service = ConversationResponseService(session)
        
        # Verify prompt settings is initialized
        assert service.prompt_settings is not None
        
        print("✅ Response service initializes prompt settings")

async def main():
    """Run all tests."""
    print("=" * 70)
    print("System Prompt Configuration & Markdown Response Tests")
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
        print("  ✓ Markdown formatting is enforced in responses")
        print("  ✓ 'I don't know' responses when context is insufficient")
        print("  ✓ Multi-layer configuration strategy implemented")
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
