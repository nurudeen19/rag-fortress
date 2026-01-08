"""
Intent Classifier with Rule-Based Pattern Matching

Identifies user intents for simple queries (greetings, acknowledgements, goodbyes)
to bypass the full RAG pipeline and return templated responses directly.
"""

import re
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from app.core import get_logger

logger = get_logger(__name__)


class IntentType(Enum):
    """Supported intent types for rule-based classification."""
    GREETING = "greeting"
    ACKNOWLEDGEMENT = "acknowledgement"
    GOODBYE = "goodbye"
    GRATITUDE = "gratitude"
    HELP_REQUEST = "help_request"
    UNCLEAR = "unclear"
    KNOWLEDGE_QUERY = "knowledge_query"  # Default - needs RAG pipeline


@dataclass
class IntentResult:
    """Result of intent classification."""
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    matched_pattern: Optional[str] = None


class IntentClassifier:
    """
    Rule-based intent classifier using pattern matching.
    
    Confidence levels:
    - 0.9-1.0: Strong match (exact phrases, very specific patterns)
    - 0.7-0.89: Good match (clear patterns with some variation)
    - 0.5-0.69: Moderate match (fuzzy or partial match)
    - 0.0-0.49: Weak match (defaults to knowledge query)
    """
    
    # Pattern definitions with confidence scores
    PATTERNS = {
        IntentType.GREETING: [
            # High confidence - exact greetings (handling both one-word and multi-word variations)
            (r"^(hi|hey|hello|greetings|good morning|good afternoon|good evening)[\s!.?]*$", 0.95),
            (r"^(good\s+(morning|afternoon|evening|day))[\s!.?]*$", 0.95),
            (r"^(what's up|wassup|sup|yo|howdy|hiya)[\s!.?]*$", 0.95),
            # Medium confidence - greetings with context
            (r"^(hey|hi|hello)\s+(there|again|bot|assistant|friend)[\s!.?]*$", 0.85),
            (r"^(hey there|hi there|hello there)[\s!.?]*$", 0.85),
        ],
        
        IntentType.ACKNOWLEDGEMENT: [
            # High confidence - exact acknowledgements
            (r"^(ok|okay|alright|sure|got it|understood|i see|noted)[\s!.?]*$", 0.90),
            (r"^(yes|yep|yeah|yup|indeed|correct|right|exactly)[\s!.?]*$", 0.90),
            (r"^(no problem|no worries|all good|sounds good)[\s!.?]*$", 0.90),
            # Medium confidence - acknowledgements with context
            (r"^(ok|okay|alright),?\s+(thanks|thank you|got it)[\s!.?]*$", 0.80),
            (r"^(that('s|\s+is)\s+(helpful|great|perfect|good|fine))[\s!.?]*$", 0.80),
        ],
        
        IntentType.GOODBYE: [
            # High confidence - exact goodbyes (one or two word variations)
            (r"^(bye|goodbye|good\s+bye|farewell|cheers|peace|adios)[\s!.?]*$", 0.95),
            (r"^(see you|see\s+ya|catch you|later|gotta go)[\s!.?]*$", 0.95),
            (r"^(see you (later|soon|tomorrow|around)|catch you (later|around)|talk (to you )?later)[\s!.?]*$", 0.95),
            (r"^(have a (good|great|nice) (day|evening|night|one)|take care)[\s!.?]*$", 0.95),
            # Medium confidence - goodbyes with additions or punctuation
            (r"^(bye|goodbye|see you),?\s+(thanks|thank you)[\s!.?]*$", 0.85),
            (r"^(gotta go|i('m|\s+am) (leaving|off|done)|time to go)[\s!.?]*$", 0.80),
            (r"^(bye\s+(for\s+now|bye|then)|see\s+you\s+(then|next\s+time))[\s!.?]*$", 0.80),
        ],
        
        IntentType.GRATITUDE: [
            # High confidence - exact gratitude
            (r"^(thanks|thank you|thx|ty|appreciate it)[\s!.?]*$", 0.95),
            (r"^(thanks a lot|thank you (so much|very much)|many thanks)[\s!.?]*$", 0.95),
            (r"^(much appreciated|really appreciate it)[\s!.?]*$", 0.95),
            # Medium confidence - gratitude with context
            (r"^(thanks|thank you)\s+(for|so much for)[\s\w]+[\s!.?]*$", 0.80),
            (r"^(i\s+appreciate\s+(it|that|your\s+help))[\s!.?]*$", 0.85),
        ],
        
        IntentType.HELP_REQUEST: [
            # High confidence - explicit help requests
            (r"^(help|help me|can you help|i need help)[\s!.?]*$", 0.90),
            (r"^(what can you (do|help with))[\s!.?]*$", 0.90),
            (r"^(how do(es)? (this|it) work)[\s!.?]*$", 0.85),
            # Medium confidence - implicit help
            (r"^(i('m|\s+am) (lost|confused|stuck))[\s!.?]*$", 0.80),
            (r"^(what('s|\s+is) (this|your\s+purpose))[\s!.?]*$", 0.75),
        ],
        
        IntentType.UNCLEAR: [
            # Very short or uninformative queries
            (r"^[a-z]{1,2}[\s!.?]*$", 0.85),  # Single/two letters
            (r"^[?.!]+$", 0.90),  # Just punctuation
            (r"^(huh|what|umm|uh|hmm)[\s!.?]*$", 0.85),
        ],
    }
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize intent classifier.
        
        Args:
            confidence_threshold: Minimum confidence to use template response.
                                 Below this threshold, defaults to knowledge_query.
        """
        self.confidence_threshold = confidence_threshold
        logger.info(f"IntentClassifier initialized with threshold={confidence_threshold}")
    
    def classify(self, query: str) -> IntentResult:
        """
        Classify user query intent using rule-based patterns.
        
        Args:
            query: User query text
            
        Returns:
            IntentResult with intent type, confidence, and matched pattern
        """
        if not query or not query.strip():
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=1.0,
                matched_pattern="empty_query"
            )
        
        # Normalize query for pattern matching
        normalized = query.strip().lower()
        
        # Try each intent type's patterns
        best_match = None
        best_confidence = 0.0
        best_pattern = None
        
        for intent_type, patterns in self.PATTERNS.items():
            for pattern, confidence in patterns:
                if re.match(pattern, normalized, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_match = intent_type
                        best_confidence = confidence
                        best_pattern = pattern
        
        # If we found a match above threshold, return it
        if best_match and best_confidence >= self.confidence_threshold:
            logger.debug(
                f"Intent classified: {best_match.value} "
                f"(confidence={best_confidence:.2f}, pattern='{best_pattern[:50]}')"
            )
            return IntentResult(
                intent=best_match,
                confidence=best_confidence,
                matched_pattern=best_pattern
            )
        
        # Default to knowledge query (needs full pipeline)
        confidence = best_confidence if best_match else 0.0
        logger.debug(
            f"Intent defaulted to knowledge_query "
            f"(best_match={best_match.value if best_match else 'none'}, "
            f"confidence={confidence:.2f} < threshold={self.confidence_threshold})"
        )
        return IntentResult(
            intent=IntentType.KNOWLEDGE_QUERY,
            confidence=confidence,
            matched_pattern=None
        )
    
    def should_use_template(self, result: IntentResult) -> bool:
        """
        Determine if a template response should be used.
        
        Args:
            result: Classification result
            
        Returns:
            True if template response should be used, False for pipeline
        """
        # Always use pipeline for knowledge queries
        if result.intent == IntentType.KNOWLEDGE_QUERY:
            return False
        
        # Use template if confidence is above threshold
        return result.confidence >= self.confidence_threshold


# Global instance
_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier(confidence_threshold: float = 0.7) -> IntentClassifier:
    """
    Get or create the global intent classifier instance.
    
    Args:
        confidence_threshold: Minimum confidence for template responses
        
    Returns:
        IntentClassifier instance
    """
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier(confidence_threshold)
    return _intent_classifier


def reset_intent_classifier():
    """Reset the global intent classifier (useful for testing)."""
    global _intent_classifier
    _intent_classifier = None
