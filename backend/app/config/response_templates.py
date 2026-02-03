"""
Response Templates for Intent-Based Replies

Provides templated responses for common intents (greetings, acknowledgements, etc.)
to avoid unnecessary RAG pipeline invocations for simple interactions.
"""

import random
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.utils.intent_classifier import IntentType


class ResponseTemplates:
    """Collection of templated responses for each intent type."""
    
    TEMPLATES: Dict[str, List[str]] = {
        "greeting": [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Hey! I'm here to help. What would you like to know?",
            "Greetings! How may I help you?",
            "Hello! Feel free to ask me anything.",
            "Hi! What questions can I answer for you today?",
        ],
        
        "acknowledgement": [
            "Great! Let me know if you need anything else.",
            "Sounds good! I'm here if you have more questions.",
            "Perfect! Feel free to ask if you need further assistance.",
            "Understood! Don't hesitate to reach out if you need help.",
            "Alright! I'm ready to help with anything else you need.",
            "Got it! Just let me know if there's anything more I can do.",
        ],
        
        "goodbye": [
            "Goodbye! Have a great day!",
            "See you later! Feel free to come back anytime.",
            "Take care! I'm here whenever you need assistance.",
            "Farewell! Don't hesitate to return if you have questions.",
            "Bye! Hope I was able to help.",
            "See you! Have a wonderful day ahead!",
        ],
        
        "gratitude": [
            "You're welcome! Happy to help.",
            "My pleasure! Let me know if you need anything else.",
            "Glad I could assist! Feel free to ask more questions.",
            "You're very welcome! I'm here anytime you need help.",
            "No problem at all! That's what I'm here for.",
            "Happy to help! Don't hesitate to reach out again.",
        ],
        
        "help_request": [
            "I'm here to help! I can answer questions based on the documents and information available to me. Just ask me anything you'd like to know.",
            "I'm an AI assistant that can help you find information from our knowledge base. Feel free to ask questions about any topic you need assistance with.",
            "I can assist you by searching through available documents and providing relevant information. What would you like to know?",
            "I'm designed to help answer your questions using our document repository. Just tell me what you're looking for!",
            "I can help you find information and answer questions. Simply ask me about any topic you need assistance with.",
        ],
        
        "unclear": [
            "I didn't quite catch that. Could you please rephrase your question?",
            "I'm not sure I understood. Could you provide a bit more detail?",
            "Could you clarify what you're looking for? I'm here to help!",
            "I didn't get that. Can you try asking in a different way?",
            "Hmm, I'm not sure what you mean. Could you elaborate a bit?",
        ],
    }
    
    @classmethod
    def get_response(cls, intent: 'IntentType') -> str:
        """
        Get a random response template for the given intent.
        
        Args:
            intent: Intent type
            
        Returns:
            Random template response for that intent
        """
        # Convert IntentType enum to string value
        intent_key = intent.value if hasattr(intent, 'value') else str(intent)
        templates = cls.TEMPLATES.get(intent_key)
        if not templates:
            # Fallback for unknown intents
            return "I'm here to help! What can I assist you with?"
        
        return random.choice(templates)
        
    @classmethod
    def get_all_responses(cls, intent: 'IntentType') -> List[str]:
        """
        Get all response templates for a given intent.
        
        Args:
            intent: Intent type
            
        Returns:
            List of all templates for that intent
        """
        # Convert IntentType enum to string value
        intent_key = intent.value if hasattr(intent, 'value') else str(intent)
        return cls.TEMPLATES.get(intent_key, [])


def get_template_response(intent: 'IntentType') -> str:
    """
    Convenience function to get a template response.
    
    Args:
        intent: Intent type
        
    Returns:
        Random template response
    """
    return ResponseTemplates.get_response(intent)
