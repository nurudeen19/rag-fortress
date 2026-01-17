"""
Text processing utilities for query cleanup and normalization.

Enhanced query preprocessing with comprehensive cleaning strategies.
"""

import re
from typing import Set, List
from pydantic import BaseModel, Field

# Expanded stop words list based on common English corpus
# Includes articles, prepositions, conjunctions, auxiliary verbs, and pronouns
STOP_WORDS: Set[str] = {
    # Articles
    "a", "an", "the",
    # Conjunctions
    "and", "or", "but", "nor", "yet", "so", "for",
    # Prepositions (common)
    "in", "on", "at", "to", "of", "by", "with", "from", "into", "onto",
    "upon", "after", "before", "between", "among", "through", "during",
    "within", "without", "about", "above", "below", "over", "under",
    "around", "behind", "beside", "near", "off", "out", "up", "down",
    # Pronouns
    "i", "me", "my", "mine", "myself",
    "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    # Demonstratives
    "this", "that", "these", "those",
    # Auxiliary/Modal verbs
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    # Interrogatives (handled separately to preserve question intent)
    # "what", "when", "where", "how", "who", "which", "why", "whose", "whom",
    # Other common words
    "if", "because", "as", "since", "while", "than", "then",
}

# Question prefixes to strip while preserving the core question words
QUESTION_PREFIXES: Set[str] = {
    "can you tell me",
    "could you tell me", 
    "can you explain",
    "could you explain",
    "please tell me",
    "please explain",
    "i want to know",
    "i would like to know",
    "i need to know",
    "tell me about",
    "explain about",
    "give me information about",
    "provide information about",
    "show me",
    "find me",
    "search for",
    "look for",
    "looking for",
}

# Protected entities and patterns that should NOT be modified
# These are preserved in their original form
PROTECTED_PATTERNS: List[tuple[re.Pattern, str]] = [
    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), 'EMAIL'),
    # URLs
    (re.compile(r'https?://[^\s]+'), 'URL'),
    # Phone numbers (various formats)
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), 'PHONE'),
    # Dates (MM/DD/YYYY, DD-MM-YYYY, etc.)
    (re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'), 'DATE'),
    # Currency amounts
    (re.compile(r'\$\d+(?:,\d{3})*(?:\.\d{2})?'), 'CURRENCY'),
    # Codes/IDs (alphanumeric with dashes/underscores)
    (re.compile(r'\b[A-Z0-9]+-[A-Z0-9-]+\b'), 'CODE'),
    # Acronyms (2+ capital letters)
    (re.compile(r'\b[A-Z]{2,}\b'), 'ACRONYM'),
]


class QueryPreprocessingResult(BaseModel):
    """
    Query preprocessing result compatible with QueryDecompositionResult.
    
    Used when LLM decomposer is not available - returns optimized single query.
    """
    decomposed: bool = Field(
        default=False,
        description="Always FALSE for preprocessing (not decomposed)"
    )
    queries: List[str] = Field(
        ...,
        description="List containing single optimized query"
    )


def preprocess_query(
    query: str,
    remove_stop_words: bool = True,
    preserve_question_words: bool = True
) -> QueryPreprocessingResult:
    """
    Clean and preprocess a user query with advanced normalization.
    
    Strategies:
    1. Question Prefix Stripping - Remove verbose question starters
    2. Key Entity Protection - Preserve emails, URLs, codes, acronyms
    3. Stop-word Removal - Remove common words while preserving meaning
    4. Question Word Preservation - Keep what/when/where/how/who/which/why
    5. Punctuation Handling - Smart punctuation removal
    6. Whitespace Normalization - Clean extra spaces
    
    Args:
        query: The raw user query string
        remove_stop_words: Whether to remove common stop words
        preserve_question_words: Keep interrogative words (what/when/where/etc)
        
    Returns:
        QueryPreprocessingResult with optimized query
    """
    if not query or not query.strip():
        return QueryPreprocessingResult(queries=[""])
    
    # Step 1: Initial normalization
    cleaned = query.strip()
    
    # Step 2: Protect important entities (replace with placeholders)
    protected_entities = {}
    for pattern, entity_type in PROTECTED_PATTERNS:
        matches = pattern.findall(cleaned)
        for i, match in enumerate(matches):
            placeholder = f"__{entity_type}_{i}__"
            protected_entities[placeholder] = match
            cleaned = cleaned.replace(match, placeholder)
    
    # Step 3: Strip verbose question prefixes
    cleaned_lower = cleaned.lower()
    for prefix in sorted(QUESTION_PREFIXES, key=len, reverse=True):  # Longest first
        if cleaned_lower.startswith(prefix):
            # Remove prefix but keep the rest
            cleaned = cleaned[len(prefix):].strip()
            cleaned_lower = cleaned.lower()
            break
    
    # Step 4: Handle punctuation intelligently
    # Keep hyphens in compound words, apostrophes in contractions
    # Remove other punctuation except question marks (preserve question intent)
    cleaned = re.sub(r'([^\w\s\'-])', ' ', cleaned)
    
    # Step 5: Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Step 6: Stop-word removal with question word preservation
    if remove_stop_words:
        words = cleaned.split()
        
        # Question words to always preserve (critical for search intent)
        question_words = {'what', 'when', 'where', 'how', 'who', 'which', 'why', 'whose', 'whom'}
        
        filtered_words = []
        for word in words:
            word_lower = word.lower()
            
            # Keep if: not a stop word, OR is a question word, OR is a placeholder
            if (word_lower not in STOP_WORDS or 
                (preserve_question_words and word_lower in question_words) or
                word.startswith('__')):
                filtered_words.append(word)
        
        # Fallback: if filtering removed everything, keep original
        if not filtered_words or all(w.startswith('__') for w in filtered_words):
            filtered_words = words
        
        cleaned = " ".join(filtered_words)
    
    # Step 7: Restore protected entities
    for placeholder, original in protected_entities.items():
        cleaned = cleaned.replace(placeholder, original)
    
    # Step 8: Final normalization
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # If result is empty, return original query
    if not cleaned:
        cleaned = query.strip()
    
    return QueryPreprocessingResult(
        decomposed=False,
        queries=[cleaned]
    )
