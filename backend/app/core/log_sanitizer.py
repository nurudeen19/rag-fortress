"""
Log sanitization utilities to prevent sensitive data leakage.

Automatically redacts passwords, tokens, API keys, and other sensitive information
from log messages and structured data before logging.
"""
import re
from typing import Any, Dict, List, Union


class LogSanitizer:
    """Sanitizes sensitive information from log messages and data structures."""
    
    # Sensitive field names to redact (case-insensitive)
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd',
        'token', 'access_token', 'refresh_token', 'reset_token', 'invite_token',
        'secret', 'api_key', 'apikey', 'private_key', 'privatekey',
        'authorization', 'auth', 'bearer',
        'old_password', 'new_password', 'confirm_password',
        'current_password', 'password_hash',
    }
    
    # Patterns to detect sensitive data in strings
    SENSITIVE_PATTERNS = [
        # JWT tokens (eyJ...)
        (re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'), '[REDACTED_JWT]'),
        # Bearer tokens
        (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
        # Password/token/secret fields in dict/JSON strings (e.g., 'password': 'value' or "password": "value")
        (re.compile(r"'(password|passwd|pwd|token|access_token|refresh_token|reset_token|secret|api_key|apikey|authorization|auth|bearer|private_key)':\s*'([^']*)'", re.IGNORECASE), r"'\1': '[REDACTED]'"),
        (re.compile(r'"(password|passwd|pwd|token|access_token|refresh_token|reset_token|secret|api_key|apikey|authorization|auth|bearer|private_key)":\s*"([^"]*)"', re.IGNORECASE), r'"\1": "[REDACTED]"'),
        # API keys starting with common prefixes (sk-, pk-, etc.) followed by alphanumeric
        (re.compile(r'\b(sk|pk|api|key)[-_][a-zA-Z0-9]{20,}'), '[REDACTED_API_KEY]'),
        # API keys (generic format with label)
        (re.compile(r'(?i)api[_-]?key["\s:=]+[A-Za-z0-9_\-]{16,}'), 'api_key=[REDACTED_KEY]'),
        # AWS keys
        (re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)["\s:=]+[A-Za-z0-9/+=]{16,}'), r'\1=[REDACTED_AWS]'),
        # Generic secrets (secret=..., secret:..., secret "...")
        (re.compile(r'(?i)secret["\s:=]+[A-Za-z0-9_\-\.]{8,}'), 'secret=[REDACTED_SECRET]'),
        # Password in URLs
        (re.compile(r'://([^:]+):([^@]+)@'), r'://\1:[REDACTED]@'),
        # Password/Token in log messages (e.g., "Password: xxx" or "Token: xxx") - but NOT format placeholders like %s
        (re.compile(r'\b(Password|Token|Secret|API[- ]?Key):\s*(?!%[sd])([^\s,]+)', re.IGNORECASE), r'\1: [REDACTED]'),
    ]
    
    REDACTED_TEXT = '[REDACTED]'
    
    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """
        Sanitize sensitive data from any data structure.
        
        Args:
            data: Data to sanitize (dict, list, str, or primitive)
        
        Returns:
            Sanitized copy of the data
        """
        if isinstance(data, dict):
            return cls._sanitize_dict(data)
        elif isinstance(data, (list, tuple)):
            return cls._sanitize_list(data)
        elif isinstance(data, str):
            return cls._sanitize_string(data)
        else:
            return data
    
    @classmethod
    def _sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary by redacting sensitive keys."""
        sanitized = {}
        
        for key, value in data.items():
            # Check if key is sensitive
            if cls._is_sensitive_key(key):
                sanitized[key] = cls.REDACTED_TEXT
            else:
                # Recursively sanitize nested structures
                sanitized[key] = cls.sanitize(value)
        
        return sanitized
    
    @classmethod
    def _sanitize_list(cls, data: Union[List, tuple]) -> Union[List, tuple]:
        """Sanitize list/tuple by recursively sanitizing elements."""
        sanitized = [cls.sanitize(item) for item in data]
        return tuple(sanitized) if isinstance(data, tuple) else sanitized
    
    @classmethod
    def _sanitize_string(cls, data: str) -> str:
        """Sanitize string by applying regex patterns."""
        result = data
        
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            result = pattern.sub(replacement, result)
        
        return result
    
    @classmethod
    def _is_sensitive_key(cls, key: str) -> bool:
        """Check if a key name is sensitive."""
        key_lower = key.lower().replace('_', '').replace('-', '')
        
        for sensitive_field in cls.SENSITIVE_FIELDS:
            sensitive_normalized = sensitive_field.replace('_', '').replace('-', '')
            if sensitive_normalized in key_lower:
                return True
        
        return False
    
    @classmethod
    def sanitize_message(cls, message: str, *args, **kwargs) -> tuple:
        """
        Sanitize log message and arguments.
        
        Args:
            message: Log message format string
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Tuple of (sanitized_message, sanitized_args, sanitized_kwargs)
        """
        sanitized_message = cls._sanitize_string(message)
        sanitized_args = tuple(cls.sanitize(arg) for arg in args)
        sanitized_kwargs = {k: cls.sanitize(v) for k, v in kwargs.items()}
        
        return sanitized_message, sanitized_args, sanitized_kwargs


def sanitize_log_data(data: Any) -> Any:
    """
    Convenience function to sanitize data before logging.
    
    Usage:
        logger.info(f"User data: {sanitize_log_data(user_dict)}")
        logger.debug(f"Request: {sanitize_log_data(request_body)}")
    
    Args:
        data: Data to sanitize
    
    Returns:
        Sanitized data safe for logging
    """
    return LogSanitizer.sanitize(data)


__all__ = ['LogSanitizer', 'sanitize_log_data']
