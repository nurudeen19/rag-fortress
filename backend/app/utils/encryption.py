"""
Encryption utilities using HKDF key derivation from a master key.

Architecture:
- Single MASTER_ENCRYPTION_KEY in environment
- HKDF derives purpose-specific keys (settings, conversations, etc.)
- Versioning built into derivation context (v1, v2, etc.)
- Encrypted data prefixed with version (e.g., "v1:gAAAAAB...")

This allows:
- One key to manage (operational simplicity)
- Cryptographic isolation between purposes (security)
- Easy key rotation (just increment version)
- Self-describing encrypted data (version in prefix)

Based on cryptographic best practices from Signal Protocol and TLS 1.3.
"""

import base64
from typing import Tuple
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)


class EncryptionError(Exception):
    """Base exception for encryption operations."""


class DecryptionError(Exception):
    """Exception raised when decryption fails."""


def derive_key(purpose: str, version: int = 1) -> bytes:
    """
    Derive a purpose-specific encryption key from master key using HKDF.
    
    HKDF (HMAC-based Key Derivation Function) is a cryptographically secure
    way to derive multiple keys from a single master key. Used in TLS 1.3,
    Signal Protocol, and other security-critical systems.
    
    Args:
        purpose: Purpose of the key (e.g., "conversations", "settings")
        version: Key version for rotation (default: 1)
    
    Returns:
        URL-safe base64-encoded derived key (32 bytes)
    
    Example:
        key_v1 = derive_key("conversations", version=1)
        key_v2 = derive_key("conversations", version=2)  # For rotation
    """
    # Get master key from settings (fallback to SETTINGS_ENCRYPTION_KEY for backwards compat)
    master_key_b64 = getattr(settings, 'MASTER_ENCRYPTION_KEY', None) or settings.SETTINGS_ENCRYPTION_KEY
    
    if not master_key_b64:
        raise EncryptionError("No master encryption key configured. Set MASTER_ENCRYPTION_KEY in .env")
    
    master_key = base64.urlsafe_b64decode(master_key_b64)
    
    # Create derivation context: "purpose:vN"
    info = f"{purpose}:v{version}".encode()
    
    # Derive key using HKDF with SHA-256
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet requires 32-byte keys
        salt=None,  # Optional: could add application-specific salt
        info=info,
    )
    
    derived = hkdf.derive(master_key)
    
    # Fernet expects URL-safe base64-encoded keys
    return base64.urlsafe_b64encode(derived)


def encrypt(plaintext: str, purpose: str, version: int = 1) -> str:
    """
    Encrypt plaintext using purpose-specific derived key.
    
    Returns encrypted data with version prefix: "v1:ciphertext"
    This makes the data self-describing - we know which key to use.
    
    Args:
        plaintext: Text to encrypt
        purpose: Purpose context (e.g., "conversations", "settings")
        version: Key version to use (default: 1)
    
    Returns:
        Versioned encrypted string: "v{version}:{ciphertext}"
    
    Raises:
        EncryptionError: If encryption fails
    
    Example:
        encrypted = encrypt("Hello, world!", "conversations", version=1)
        # Returns: "v1:gAAAAABf..."
    """
    if not plaintext:
        return plaintext
    
    try:
        # Derive purpose-specific key
        key = derive_key(purpose, version)
        
        # Create Fernet cipher
        cipher = Fernet(key)
        
        # Encrypt (Fernet handles encoding internally)
        ciphertext = cipher.encrypt(plaintext.encode())
        
        # Return with version prefix
        versioned_ciphertext = f"v{version}:{ciphertext.decode()}"
        
        return versioned_ciphertext
        
    except EncryptionError:
        raise
    except Exception as e:
        error_msg = f"Encryption failed for purpose '{purpose}' v{version}: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise EncryptionError(error_msg) from e


def decrypt(versioned_ciphertext: str, purpose: str) -> str:
    """
    Decrypt versioned ciphertext using appropriate derived key.
    
    Automatically extracts version from prefix and uses correct key.
    This enables transparent key rotation.
    
    Args:
        versioned_ciphertext: Encrypted string with version prefix "v1:..."
        purpose: Purpose context (must match encryption purpose)
    
    Returns:
        Decrypted plaintext
    
    Raises:
        DecryptionError: If decryption fails or format is invalid
    
    Example:
        plaintext = decrypt("v1:gAAAAABf...", "conversations")
        # Returns: "Hello, world!"
    """
    if not versioned_ciphertext:
        return versioned_ciphertext
    
    try:
        # Parse version prefix
        version, ciphertext = parse_versioned_data(versioned_ciphertext)
        
        # Derive key with matching version
        key = derive_key(purpose, version)
        
        # Create Fernet cipher
        cipher = Fernet(key)
        
        # Decrypt
        plaintext = cipher.decrypt(ciphertext.encode())
        
        return plaintext.decode()
        
    except InvalidToken as e:
        error_msg = f"Invalid token for purpose '{purpose}' (wrong key or corrupted data): {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise DecryptionError(error_msg) from e
    except ValueError as e:
        # If it's a parse error, might be legacy unencrypted or old format
        error_msg = f"Failed to parse versioned data: {str(e)}. Data might be unencrypted (legacy format?)"
        logger.warning(error_msg)
        raise DecryptionError(error_msg) from e
    except DecryptionError:
        raise
    except Exception as e:
        error_msg = f"Decryption failed for purpose '{purpose}': {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise DecryptionError(error_msg) from e


def parse_versioned_data(versioned_data: str) -> Tuple[int, str]:
    """
    Parse version prefix from encrypted data.
    
    Args:
        versioned_data: String with version prefix "v1:data"
    
    Returns:
        Tuple of (version, data)
    
    Raises:
        ValueError: If format is invalid
    
    Example:
        version, data = parse_versioned_data("v1:gAAAAABf...")
        # Returns: (1, "gAAAAABf...")
    """
    if ":" not in versioned_data:
        raise ValueError(
            "Invalid encrypted data format: missing version prefix. "
            "Expected format: 'v1:ciphertext'"
        )
    
    version_str, data = versioned_data.split(":", 1)
    
    if not version_str.startswith("v"):
        raise ValueError(
            f"Invalid version prefix: '{version_str}'. "
            "Expected format: 'v1', 'v2', etc."
        )
    
    try:
        version = int(version_str[1:])
    except ValueError:
        raise ValueError(
            f"Invalid version number in prefix: '{version_str}'. "
            "Expected format: 'v1', 'v2', etc."
        )
    
    return version, data


# Convenience wrappers for common purposes

def encrypt_conversation_message(message: str, version: int = 1) -> str:
    """Encrypt a conversation message."""
    return encrypt(message, purpose="conversations", version=version)


def decrypt_conversation_message(encrypted_message: str) -> str:
    """Decrypt a conversation message."""
    return decrypt(encrypted_message, purpose="conversations")


def encrypt_settings_value(value: str, version: int = 1) -> str:
    """Encrypt a settings value."""
    return encrypt(value, purpose="settings", version=version)


def decrypt_settings_value(encrypted_value: str) -> str:
    """Decrypt a settings value."""
    return decrypt(encrypted_value, purpose="settings")


# Legacy compatibility (for existing code using old API)
def encrypt_value(value: str) -> str:
    """Legacy wrapper for settings encryption (backwards compatibility)."""
    return encrypt_settings_value(value, version=1)


def decrypt_value(encrypted_value: str) -> str:
    """Legacy wrapper for settings decryption (backwards compatibility)."""
    try:
        return decrypt_settings_value(encrypted_value)
    except (DecryptionError, ValueError):
        # If new format fails, might be old format - try legacy decryption
        logger.warning("Failed to decrypt with new format, returning as-is (legacy data?)")
        return encrypted_value


# Background re-encryption support for key rotation
async def reencrypt_to_new_version(
    old_encrypted: str,
    purpose: str,
    new_version: int
) -> str:
    """
    Re-encrypt data from old version to new version.
    
    Used for gradual key rotation in background jobs.
    
    Args:
        old_encrypted: Data encrypted with old key version
        purpose: Purpose context
        new_version: Target key version
    
    Returns:
        Data re-encrypted with new key version
    
    Example:
        # In background job
        new_encrypted = await reencrypt_to_new_version(
            message.content,
            purpose="conversations",
            new_version=2
        )
        message.content = new_encrypted
    """
    # Decrypt with old key (version auto-detected from prefix)
    plaintext = decrypt(old_encrypted, purpose)
    
    # Re-encrypt with new key version
    new_encrypted = encrypt(plaintext, purpose, version=new_version)
    
    return new_encrypted
