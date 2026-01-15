# Log Sanitization Guide

## Overview

RAG Fortress implements **automatic log sanitization at the logging core level**. All log messages are automatically sanitized before being written to console or log files, protecting against accidental exposure of passwords, tokens, API keys, and other confidential data.

## 🎯 Key Feature: Automatic Sanitization

**Sanitization happens automatically** - you don't need to manually sanitize data before logging!

The sanitization is integrated directly into the logging formatters (`ColoredFormatter` and `PlainFormatter` in `app/core/logging.py`), which means:

- ✅ **Universal**: Every single log message is sanitized
- ✅ **Automatic**: No manual calls needed
- ✅ **Foolproof**: Impossible to forget to sanitize
- ✅ **Zero overhead**: Developers just log normally

## How It Works

```python
from app.core import get_logger

logger = get_logger(__name__)

# Just log normally - sanitization is AUTOMATIC!
user_data = {
    'username': 'john_doe',
    'password': 'secret123',  # Automatically redacted
    'token': 'abc123xyz',     # Automatically redacted
    'email': 'john@example.com'
}

logger.info(f"User data: {user_data}")
# Output: User data: {'username': 'john_doe', 'password': '[REDACTED]', 'token': '[REDACTED]', 'email': 'john@example.com'}

# Even direct logging of sensitive strings is safe
logger.info(f"Reset token: eyJhbGciOiJIUzI1NiIsInR5...")
# Output: Reset token: [REDACTED_JWT]
```

## Security Principles

**Automatically sanitized data:**
- ✅ Passwords (plain text or hashed)
- ✅ Authentication tokens (access, refresh, reset, invite)
- ✅ API keys and secrets
- ✅ Authorization headers
- ✅ JWT tokens, Bearer tokens
- ✅ Credentials in URLs
- ✅ Any field matching sensitive patterns

## What Gets Sanitized

**Field Names (case-insensitive):**
- password, passwd, pwd, old_password, new_password, confirm_password
- token, access_token, refresh_token, reset_token, invite_token
- secret, api_key, apikey, private_key
- authorization, auth, bearer
- credit_card, cvv, ssn
- password_hash

**String Patterns:**
- JWT tokens (eyJ...)
- Bearer tokens
- API keys
- AWS credentials
- Password in URLs (`://user:password@`)

## Implementation Details

### Core Integration

Sanitization is implemented in `app/core/logging.py`:

```python
class ColoredFormatter(logging.Formatter):
    """Custom formatter with automatic sanitization"""
    
    def format(self, record):
        # Sanitize BEFORE formatting
        record = self._sanitize_record(record)
        # ... then format normally
    
    def _sanitize_record(self, record):
        from app.utils.log_sanitizer import LogSanitizer
        
        # Sanitize message string
        if isinstance(record.msg, str):
            record.msg = LogSanitizer._sanitize_string(record.msg)
        
        # Sanitize arguments
        if record.args:
            record.args = tuple(LogSanitizer.sanitize(arg) for arg in record.args)
        
        return record
```

Both `ColoredFormatter` (console) and `PlainFormatter` (file) include this sanitization.

### Usage Examples

```python
from app.core import get_logger

logger = get_logger(__name__)

# Example 1: Dict with sensitive fields (AUTOMATIC)
request_body = {
    'email': 'user@example.com',
    'password': 'MySecret123!',
    'api_key': 'sk-proj-abc123xyz'
}
logger.info(f"Request: {request_body}")
# Automatically sanitized: {'email': 'user@example.com', 'password': '[REDACTED]', 'api_key': '[REDACTED]'}

# Example 2: Nested structures (AUTOMATIC)
payload = {
    'user': {
        'id': 123,
        'credentials': {
            'username': 'admin',
            'password': 'secret'  # Nested, still redacted
        }
    },
    'reset_token': 'token_abc123'
}
logger.info(f"Payload: {payload}")
# All sensitive fields automatically redacted

# Example 3: Strings with JWT tokens (AUTOMATIC)
logger.info(f"Auth header: Bearer eyJhbGciOiJIUzI1NiIsInR5...")
# Output: Auth header: Bearer [REDACTED_TOKEN]

# Example 4: Database URLs (AUTOMATIC)
logger.info(f"Connecting to: postgresql://user:MyPass123@localhost:5432/db")
# Output: Connecting to: postgresql://user:[REDACTED]@localhost:5432/db

```
