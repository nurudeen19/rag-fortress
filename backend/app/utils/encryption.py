"""
Simple encryption/decryption utility for sensitive settings.

Uses Fernet (symmetric encryption) from cryptography library.
"""

import os
from cryptography.fernet import Fernet
from app.config import settings
from app.core import get_logger

logger = get_logger(__name__)

# Get encryption key from environment or generate one
ENCRYPTION_KEY = settings.SETTINGS_ENCRYPTION_KEY

if not ENCRYPTION_KEY:
    # Generate a key for development (in production, set SETTINGS_ENCRYPTION_KEY in .env)
    logger.warning("SETTINGS_ENCRYPTION_KEY not set, generating temporary key (not persistent across restarts!)")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

_fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """
    Encrypt a sensitive value.
    
    Args:
        value: Plain text value to encrypt
    
    Returns:
        Encrypted value as base64 string
    """
    if not value:
        return value
    
    try:
        encrypted = _fernet.encrypt(value.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_value(encrypted_value: str) -> str:
    """
    Decrypt a sensitive value.
    
    Args:
        encrypted_value: Encrypted value as base64 string
    
    Returns:
        Decrypted plain text value
    """
    if not encrypted_value:
        return encrypted_value
    
    try:
        decrypted = _fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        # Return as-is if decryption fails (might be unencrypted legacy value)
        return encrypted_value
