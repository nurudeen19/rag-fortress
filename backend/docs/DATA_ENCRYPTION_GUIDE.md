# Data Encryption Guide

## Overview

RAG Fortress encrypts sensitive data at rest using **HKDF key derivation** from a single master key. Currently encrypts:
- Conversation messages (user queries and AI responses)
- Application settings (API keys, passwords, sensitive configuration)

## Architecture

```
MASTER_ENCRYPTION_KEY (single key in .env)
         ↓
    HKDF-SHA256
         ↓
Purpose-specific keys (conversations, settings, etc.)
```

**Encryption format:** `v1:gAAAAABf...` (version prefix + Fernet ciphertext)

## Quick Start

### 1. Configuration

```bash
# .env
MASTER_ENCRYPTION_KEY=cWirqUebM3s2K4PISKhTGc66rgQNpWQKfncS-WnCt9s=

# Generate new key (choose one):
# Option 1: Using provided script
python generate_fernet_key.py

# Option 2: Using Python directly
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Usage

**Conversation Messages (Automatic):**
```python
# Encryption/decryption happens automatically at DB layer
message = Message(content="Hello, world!")
await session.commit()  # Auto-encrypted before save

# Load and access
message = await session.get(Message, id)
plaintext = message.content  # Auto-decrypted on access
```

**Custom Data:**
```python
from app.utils.encryption import encrypt, decrypt

# Encrypt
encrypted = encrypt("sensitive data", purpose="custom", version=1)
# Returns: "v1:gAAAAABf..."

# Decrypt (auto-detects version)
plaintext = decrypt(encrypted, purpose="custom")
```

**Application Settings (Automatic):**
```python
from app.services.settings_service import SettingsService

# Sensitive settings (API keys, passwords) auto-encrypted
await settings_service.create(
    key="openai_api_key",
    value="sk-...",  # Auto-encrypted if key matches sensitive pattern
    category="llm"
)

# Auto-decrypted on retrieval
value = await settings_service.get_value("openai_api_key")
```

### 3. Migrate Existing Data

**Messages:**
```bash
# Preview what would be encrypted
python -m app.utils.migrate_message_encryption --dry-run

# Encrypt unencrypted messages
python -m app.utils.migrate_message_encryption
```

**Settings:**
```bash
# Preview settings migration
python -m app.utils.migrate_settings_encryption --dry-run

# Migrate from legacy SETTINGS_ENCRYPTION_KEY to HKDF
python -m app.utils.migrate_settings_encryption

# Verify all settings encrypted
python -m app.utils.migrate_settings_encryption --verify
```

## Key Rotation

**When to rotate:**
- Compliance requirement
- Key compromise suspected
- Personnel changes

**How to rotate:**

1. Update default version:
```python
# In encryption.py
def encrypt_conversation_message(msg, version=2):  # Changed from 1
```

2. Run re-encryption job:
```python
from app.utils.encryption import reencrypt_to_new_version

new_encrypted = await reencrypt_to_new_version(
    old_encrypted=message._content,
    purpose="conversations",
    new_version=2
)
```

3. Verify all data uses new version:
```sql
SELECT COUNT(*) FROM messages WHERE content NOT LIKE 'v2:%';
```

## Security Notes

**Protected:**
- Database dumps/backups
- SQL injection (data still encrypted)
- Unauthorized DB access

**NOT protected:**
- Application-level attacks
- Key theft from environment
- Compromised app server

**Best practices:**
- Store key in environment only (never in code)
- Back up key securely
- Different keys per environment (dev/prod)
- Restrict key access to ops team

## Troubleshooting

**Error: "No master encryption key configured"**
```bash
# Add to .env
MASTER_ENCRYPTION_KEY=<your-key-here>
```

**Error: "Decryption failed: Invalid token"**
- Wrong master key
- Corrupted data
- Different purpose/version used

**Performance:**
- Encryption: ~1ms per operation
- Decryption: ~1ms (cached in memory after first access)
- Storage overhead: ~33% (base64 + version prefix)

## API Reference

**Key functions in `app/utils/encryption.py`:**
- `derive_key(purpose, version)` - Derive purpose-specific key
- `encrypt(plaintext, purpose, version)` - Encrypt with versioning
- `decrypt(ciphertext, purpose)` - Decrypt (auto-detect version)
- `encrypt_conversation_message(msg)` - Convenience for messages
- `decrypt_conversation_message(encrypted)` - Convenience for messages
- `reencrypt_to_new_version(old, purpose, new_ver)` - For rotation

**SQLAlchemy integration:**
- Messages auto-encrypt on `before_insert`/`before_update` events
- Messages auto-decrypt on property access via `@property` decorator
- See `app/models/message.py` for implementation
