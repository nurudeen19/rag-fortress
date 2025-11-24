"""
Query Validator Service

Detects and blocks malicious queries including:
- Prompt injection attacks
- SQL injection attempts
- Code execution patterns
- Data exfiltration attempts
- Jailbreak/bypass attempts

Usage:
    validator = QueryValidator()
    result = await validator.validate_query(user_query, user_id)
    if not result["valid"]:
        raise ValidationError(result["reason"])
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryValidator:
    """
    Validates user queries for security threats.
    
    Detects various attack patterns and provides detailed feedback
    on why a query was rejected.
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        
        # Prompt Injection Patterns
        self.prompt_injection_patterns = [
            # Role manipulation
            re.compile(r'\b(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|prompts|commands|rules)', re.IGNORECASE),
            re.compile(r'\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be|assume\s+the\s+role)', re.IGNORECASE),
            re.compile(r'\b(system|assistant|user)\s*:', re.IGNORECASE),
            re.compile(r'<\|?(system|assistant|user|im_start|im_end)\|?>', re.IGNORECASE),
            
            # Instruction manipulation
            re.compile(r'\b(override|bypass|disable)\s+(safety|security|filter|guardrail|restriction)', re.IGNORECASE),
            re.compile(r'\b(new\s+instructions?|updated\s+instructions?|revised\s+instructions?)', re.IGNORECASE),
            re.compile(r'---+\s*(new|updated|revised)\s+(instruction|prompt|system)', re.IGNORECASE),
            
            # Jailbreak attempts
            re.compile(r'\bDAN\s+mode\b', re.IGNORECASE),  # "Do Anything Now"
            re.compile(r'\b(jailbreak|escape|break\s+out)', re.IGNORECASE),
            re.compile(r'simulate\s+(a\s+)?conversation', re.IGNORECASE),
            re.compile(r'from\s+now\s+on', re.IGNORECASE),
            
            # Output manipulation
            re.compile(r'(start|begin)\s+your\s+(response|answer|reply)\s+with', re.IGNORECASE),
            re.compile(r'do\s+not\s+(use|apply|follow)\s+(safety|ethics|moral)', re.IGNORECASE),
            re.compile(r'(write|generate|create)\s+a\s+response\s+that', re.IGNORECASE),
        ]
        
        # SQL Injection Patterns
        self.sql_injection_patterns = [
            # Classic SQL injection
            re.compile(r"['\"]\s*;\s*drop\s+table", re.IGNORECASE),
            re.compile(r"['\"]\s*;\s*delete\s+from", re.IGNORECASE),
            re.compile(r"['\"]\s*;\s*truncate\s+table", re.IGNORECASE),
            re.compile(r"\bunion\s+select\b", re.IGNORECASE),
            re.compile(r"'\s*or\s+['\"]?1['\"]?\s*=\s*['\"]?1", re.IGNORECASE),
            re.compile(r"'\s*or\s+['\"]?true['\"]?\s*=\s*['\"]?true", re.IGNORECASE),
            
            # SQL comments
            re.compile(r"--\s*$", re.MULTILINE),
            re.compile(r"/\*.*?\*/", re.DOTALL),
            re.compile(r"#.*?$", re.MULTILINE),
            
            # Encoded SQL
            re.compile(r"%27|%22|%3B|%2D%2D|%2F%2A", re.IGNORECASE),  # URL-encoded ', ", ;, --, /*
        ]
        
        # Code Execution Patterns
        self.code_execution_patterns = [
            # Python execution
            re.compile(r'\beval\s*\(', re.IGNORECASE),
            re.compile(r'\bexec\s*\(', re.IGNORECASE),
            re.compile(r'__import__\s*\(', re.IGNORECASE),
            re.compile(r'\bcompile\s*\(', re.IGNORECASE),
            re.compile(r'\bsubprocess\.(run|call|Popen)', re.IGNORECASE),
            re.compile(r'\bos\.(system|popen|exec)', re.IGNORECASE),
            
            # JavaScript execution
            re.compile(r'\bFunction\s*\(', re.IGNORECASE),
            re.compile(r'\bsetTimeout\s*\(', re.IGNORECASE),
            re.compile(r'\bsetInterval\s*\(', re.IGNORECASE),
            
            # Shell commands
            re.compile(r'[;&|]\s*(rm|del|format|mkfs|dd)\s+', re.IGNORECASE),
            re.compile(r'\b(wget|curl)\s+.*?\|\s*sh', re.IGNORECASE),
            
            # Base64 encoded commands (suspicious)
            re.compile(r'base64\s*-d.*?\|', re.IGNORECASE),
        ]
        
        # Data Exfiltration Patterns
        self.data_exfiltration_patterns = [
            # Database dumps
            re.compile(r'\b(dump|export|extract)\s+(all\s+)?(data|database|table|records?)', re.IGNORECASE),
            re.compile(r'\bshow\s+me\s+all\s+(users?|passwords?|credentials?|keys?|secrets?)', re.IGNORECASE),
            re.compile(r'\blist\s+all\s+(users?|accounts?|credentials?|api[_\s]?keys?)', re.IGNORECASE),
            
            # Credential extraction
            re.compile(r'\b(what|show|give|tell)\s+(is|are|me)\s+(the\s+)?(password|api[_\s]?key|secret|token|credential)', re.IGNORECASE),
            re.compile(r'\baccess[_\s]?token', re.IGNORECASE),
            re.compile(r'\bprivate[_\s]?key', re.IGNORECASE),
            
            # System information
            re.compile(r'\b(show|display|reveal)\s+system\s+(configuration|environment|variables)', re.IGNORECASE),
            re.compile(r'\benv\s+variables?', re.IGNORECASE),
            re.compile(r'\b\.env\s+file', re.IGNORECASE),
        ]
    
    async def validate_query(self, query: str, user_id: Optional[int] = None) -> Dict[str, any]:
        """
        Validate a user query for security threats.
        
        Args:
            query: The user's query string
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict with keys:
                - valid (bool): Whether the query is safe
                - reason (str): Explanation if rejected
                - threat_type (str): Type of threat detected (if any)
                - confidence (float): Confidence level 0.0-1.0
        """
        
        if not query or len(query.strip()) == 0:
            return {
                "valid": False,
                "reason": "Query cannot be empty",
                "threat_type": "empty_query",
                "confidence": 1.0
            }
        
        # Check query length (very long queries might be attack attempts)
        if len(query) > 10000:
            logger.warning(f"Suspicious query length: {len(query)} chars (user_id={user_id})")
            return {
                "valid": False,
                "reason": "Query exceeds maximum length limit",
                "threat_type": "excessive_length",
                "confidence": 0.9
            }
        
        # Check each threat category
        threat_checks = [
            ("prompt_injection", self._check_prompt_injection),
            ("sql_injection", self._check_sql_injection),
            ("code_execution", self._check_code_execution),
            ("data_exfiltration", self._check_data_exfiltration),
        ]
        
        for threat_type, check_func in threat_checks:
            is_threat, confidence, details = check_func(query)
            
            if is_threat:
                logger.warning(
                    f"Malicious query detected: type={threat_type}, "
                    f"confidence={confidence:.2f}, user_id={user_id}, "
                    f"details={details}"
                )
                
                return {
                    "valid": False,
                    "reason": self._get_rejection_message(threat_type),
                    "threat_type": threat_type,
                    "confidence": confidence,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Query is safe
        logger.info(f"Query validated successfully (user_id={user_id})")
        return {
            "valid": True,
            "reason": "Query passed all security checks",
            "threat_type": None,
            "confidence": 1.0
        }
    
    def _check_prompt_injection(self, query: str) -> tuple[bool, float, str]:
        """Check for prompt injection attempts."""
        for pattern in self.prompt_injection_patterns:
            match = pattern.search(query)
            if match:
                return True, 0.95, f"Pattern matched: {match.group()}"
        
        # Additional heuristic: Multiple special tokens
        special_tokens = ['<|', '|>', '###', '---', '"""', "'''"]
        token_count = sum(query.count(token) for token in special_tokens)
        if token_count >= 3:
            return True, 0.75, f"Multiple special tokens detected: {token_count}"
        
        return False, 0.0, "No prompt injection detected"
    
    def _check_sql_injection(self, query: str) -> tuple[bool, float, str]:
        """Check for SQL injection attempts."""
        for pattern in self.sql_injection_patterns:
            match = pattern.search(query)
            if match:
                return True, 0.95, f"SQL pattern matched: {match.group()}"
        
        # Heuristic: Multiple SQL keywords
        sql_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'union', 'where', 'from']
        keyword_count = sum(1 for kw in sql_keywords if re.search(r'\b' + kw + r'\b', query, re.IGNORECASE))
        if keyword_count >= 4:
            return True, 0.70, f"Multiple SQL keywords detected: {keyword_count}"
        
        return False, 0.0, "No SQL injection detected"
    
    def _check_code_execution(self, query: str) -> tuple[bool, float, str]:
        """Check for code execution attempts."""
        for pattern in self.code_execution_patterns:
            match = pattern.search(query)
            if match:
                return True, 0.90, f"Code execution pattern matched: {match.group()}"
        
        # Heuristic: Suspicious function-like patterns
        suspicious_functions = re.findall(r'\b\w+\s*\(', query)
        if len(suspicious_functions) >= 5:
            return True, 0.60, f"Multiple function calls detected: {len(suspicious_functions)}"
        
        return False, 0.0, "No code execution detected"
    
    def _check_data_exfiltration(self, query: str) -> tuple[bool, float, str]:
        """Check for data exfiltration attempts."""
        for pattern in self.data_exfiltration_patterns:
            match = pattern.search(query)
            if match:
                return True, 0.85, f"Exfiltration pattern matched: {match.group()}"
        
        # Heuristic: Asking for "all" or "every" combined with sensitive terms
        if re.search(r'\b(all|every|each)\s+(user|password|key|credential)', query, re.IGNORECASE):
            return True, 0.70, "Request for comprehensive sensitive data"
        
        return False, 0.0, "No data exfiltration detected"
    
    def _get_rejection_message(self, threat_type: str) -> str:
        """Get user-friendly rejection message."""
        messages = {
            "empty_query": "Your query cannot be empty. Please provide a question or request.",
            "excessive_length": "Your query is too long. Please shorten it and try again.",
            "prompt_injection": "Your query contains patterns that violate our security policies. Please rephrase your question in a straightforward manner.",
            "sql_injection": "Your query contains potentially harmful patterns. Please ensure you're asking a legitimate question about organizational knowledge.",
            "code_execution": "Your query contains code-like patterns that cannot be processed. Please ask your question in natural language.",
            "data_exfiltration": "Your query appears to request sensitive information in bulk. Please be more specific about what you need to know.",
        }
        return messages.get(threat_type, "Your query was rejected due to security concerns. Please rephrase and try again.")


# Singleton instance
_query_validator = None


def get_query_validator() -> QueryValidator:
    """
    Get singleton instance of QueryValidator.
    
    Returns:
        QueryValidator: Shared validator instance
    """
    global _query_validator
    if _query_validator is None:
        _query_validator = QueryValidator()
    return _query_validator
