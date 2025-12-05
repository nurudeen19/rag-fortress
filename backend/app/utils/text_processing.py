"""
Text processing utilities for query cleanup and normalization.
"""

import re
from typing import Set

# Common English stop words to remove from queries to improve retrieval focus
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "when", "where", "how", "who", "which", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "up", "about",
    "into", "over", "after"
}

def preprocess_query(query: str, remove_stop_words: bool = True) -> str:
    """
    Clean and preprocess a user query.
    
    Args:
        query: The raw user query string
        remove_stop_words: Whether to remove common stop words
        
    Returns:
        Cleaned query string
    """
    if not query:
        return ""
        
    # Convert to lowercase and strip whitespace
    cleaned = query.lower().strip()
    
    # Remove special characters but keep alphanumeric and spaces
    # This helps remove punctuation that might interfere with vector search
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    
    if remove_stop_words:
        words = cleaned.split()
        filtered_words = [word for word in words if word not in STOP_WORDS]
        
        # If removing stop words results in an empty string (e.g. query was "The and"),
        # fall back to the original cleaned query to avoid empty search
        if not filtered_words:
            return cleaned
            
        cleaned = " ".join(filtered_words)
        
    return cleaned
