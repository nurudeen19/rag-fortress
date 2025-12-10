"""
Tests for Intent Classifier

Verifies rule-based intent classification and template response system.
"""

import pytest
from app.utils.intent_classifier import (
    IntentClassifier,
    IntentType,
    IntentResult,
    get_intent_classifier,
    reset_intent_classifier
)
from app.config.response_templates import get_template_response, ResponseTemplates


class TestIntentClassifier:
    """Test intent classification patterns and confidence scoring."""
    
    @pytest.fixture
    def classifier(self):
        """Create a fresh classifier for each test."""
        reset_intent_classifier()
        return IntentClassifier(confidence_threshold=0.7)
    
    def test_greeting_patterns(self, classifier):
        """Test greeting intent detection."""
        greetings = [
            "hi",
            "hello",
            "hey",
            "hey there",
            "hi there",
            "good morning",
            "good afternoon",
            "good evening",
            "what's up",
            "wassup",
            "sup",
            "howdy",
            "hiya",
            "greetings",
        ]
        
        for greeting in greetings:
            result = classifier.classify(greeting)
            assert result.intent == IntentType.GREETING, f"Failed for: {greeting}"
            assert result.confidence >= 0.7, f"Low confidence for: {greeting}"
            assert classifier.should_use_template(result), f"Template not used for: {greeting}"
    
    def test_acknowledgement_patterns(self, classifier):
        """Test acknowledgement intent detection."""
        acknowledgements = [
            "ok",
            "okay",
            "got it",
            "understood",
            "yes",
            "alright",
            "sounds good",
        ]
        
        for ack in acknowledgements:
            result = classifier.classify(ack)
            assert result.intent == IntentType.ACKNOWLEDGEMENT
            assert result.confidence >= 0.7
            assert classifier.should_use_template(result)
    
    def test_goodbye_patterns(self, classifier):
        """Test goodbye intent detection."""
        goodbyes = [
            "bye",
            "goodbye",
            "good bye",           # Two-word variation (the reported issue)
            "see you",
            "see you later",
            "catch you later",
            "farewell",
            "take care",
            "have a good day",
            "have a great evening",
            "gotta go",
            "bye for now",
            "time to go",
        ]
        
        for goodbye in goodbyes:
            result = classifier.classify(goodbye)
            assert result.intent == IntentType.GOODBYE, f"Failed for: {goodbye}"
            assert result.confidence >= 0.7, f"Low confidence for: {goodbye}"
            assert classifier.should_use_template(result), f"Template not used for: {goodbye}"
    
    def test_gratitude_patterns(self, classifier):
        """Test gratitude intent detection."""
        gratitudes = [
            "thanks",
            "thank you",
            "thanks a lot",
            "appreciate it",
            "thank you very much",
        ]
        
        for gratitude in gratitudes:
            result = classifier.classify(gratitude)
            assert result.intent == IntentType.GRATITUDE
            assert result.confidence >= 0.7
            assert classifier.should_use_template(result)
    
    def test_help_request_patterns(self, classifier):
        """Test help request intent detection."""
        help_requests = [
            "help",
            "help me",
            "what can you do",
            "how does this work",
        ]
        
        for request in help_requests:
            result = classifier.classify(request)
            assert result.intent == IntentType.HELP_REQUEST
            assert result.confidence >= 0.7
            assert classifier.should_use_template(result)
    
    def test_unclear_patterns(self, classifier):
        """Test unclear/uninformative query detection."""
        unclear = [
            "a",
            "??",
            "huh",
            "umm",
        ]
        
        for query in unclear:
            result = classifier.classify(query)
            assert result.intent == IntentType.UNCLEAR
            assert result.confidence >= 0.7
    
    def test_knowledge_queries_not_intercepted(self, classifier):
        """Test that actual knowledge queries go through RAG pipeline."""
        knowledge_queries = [
            "What is the company policy on remote work?",
            "How do I submit an expense report?",
            "Tell me about the Q4 financial results",
            "What are the security protocols for data access?",
            "Explain the vacation policy",
            "show me the sales report",
        ]
        
        for query in knowledge_queries:
            result = classifier.classify(query)
            # Should either be KNOWLEDGE_QUERY or have low confidence
            if result.intent != IntentType.KNOWLEDGE_QUERY:
                assert result.confidence < 0.7, f"Query '{query}' should not be intercepted"
            assert not classifier.should_use_template(result)
    
    def test_empty_query(self, classifier):
        """Test handling of empty queries."""
        result = classifier.classify("")
        assert result.intent == IntentType.UNCLEAR
        assert result.confidence == 1.0
        
        result = classifier.classify("   ")
        assert result.intent == IntentType.UNCLEAR
    
    def test_case_insensitivity(self, classifier):
        """Test that classification is case-insensitive."""
        queries = [
            ("HELLO", IntentType.GREETING),
            ("Thanks", IntentType.GRATITUDE),
            ("BYE", IntentType.GOODBYE),
            ("OK", IntentType.ACKNOWLEDGEMENT),
        ]
        
        for query, expected_intent in queries:
            result = classifier.classify(query)
            assert result.intent == expected_intent
            assert result.confidence >= 0.7
    
    def test_confidence_threshold(self):
        """Test that confidence threshold affects template usage."""
        # High threshold - only very confident matches use templates
        strict_classifier = IntentClassifier(confidence_threshold=0.9)
        
        # Exact match should still work
        result = strict_classifier.classify("hi")
        assert result.intent == IntentType.GREETING
        assert result.confidence >= 0.9
        assert strict_classifier.should_use_template(result)
        
        # Lower threshold - more lenient
        lenient_classifier = IntentClassifier(confidence_threshold=0.5)
        result = lenient_classifier.classify("hi")
        assert lenient_classifier.should_use_template(result)
    
    def test_mixed_queries(self, classifier):
        """Test queries that might be ambiguous."""
        # These should favor the RAG pipeline over templates
        mixed_queries = [
            "hi, can you help me find the sales report?",
            "thanks, but what about the policy document?",
            "goodbye for now, but first tell me about...",
        ]
        
        for query in mixed_queries:
            result = classifier.classify(query)
            # Should default to knowledge query for longer/complex queries
            assert result.intent == IntentType.KNOWLEDGE_QUERY or result.confidence < 0.7


class TestResponseTemplates:
    """Test template response generation."""
    
    def test_all_intents_have_templates(self):
        """Ensure all intent types have template responses."""
        for intent in [
            IntentType.GREETING,
            IntentType.ACKNOWLEDGEMENT,
            IntentType.GOODBYE,
            IntentType.GRATITUDE,
            IntentType.HELP_REQUEST,
            IntentType.UNCLEAR,
        ]:
            response = get_template_response(intent)
            assert response is not None
            assert len(response) > 0
            assert isinstance(response, str)
    
    def test_template_variety(self):
        """Test that templates provide variety (randomization works)."""
        intent = IntentType.GREETING
        responses = set()
        
        # Get 20 responses - should see variety
        for _ in range(20):
            response = get_template_response(intent)
            responses.add(response)
        
        # Should have more than 1 unique response
        assert len(responses) > 1, "Templates should provide variety"
    
    def test_get_all_responses(self):
        """Test getting all templates for an intent."""
        templates = ResponseTemplates.get_all_responses(IntentType.GREETING)
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # All should be strings
        for template in templates:
            assert isinstance(template, str)
            assert len(template) > 0
    
    def test_unknown_intent_fallback(self):
        """Test handling of unknown intent types."""
        # Create a mock intent type
        class UnknownIntent:
            pass
        
        response = ResponseTemplates.get_response(UnknownIntent())
        # Should return a fallback response
        assert response is not None
        assert isinstance(response, str)


class TestIntentClassifierIntegration:
    """Integration tests for the intent classification system."""
    
    def test_global_instance(self):
        """Test that global instance works correctly."""
        reset_intent_classifier()
        
        classifier1 = get_intent_classifier()
        classifier2 = get_intent_classifier()
        
        # Should be the same instance
        assert classifier1 is classifier2
    
    def test_custom_threshold(self):
        """Test creating classifier with custom threshold."""
        reset_intent_classifier()
        
        classifier = get_intent_classifier(confidence_threshold=0.8)
        assert classifier.confidence_threshold == 0.8
    
    def test_end_to_end_flow(self):
        """Test complete flow: classify -> check -> get template."""
        reset_intent_classifier()
        classifier = get_intent_classifier(confidence_threshold=0.7)
        
        # Greeting flow
        query = "hello"
        result = classifier.classify(query)
        
        if classifier.should_use_template(result):
            template = get_template_response(result.intent)
            assert template is not None
            assert len(template) > 0
        
        # Knowledge query flow
        query = "What is the vacation policy?"
        result = classifier.classify(query)
        
        # Should NOT use template for knowledge queries
        assert not classifier.should_use_template(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
