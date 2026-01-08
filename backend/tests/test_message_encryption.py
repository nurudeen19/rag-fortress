"""
Test message encryption at database layer.

Tests the HKDF-based encryption system for conversation messages.
"""

import pytest
from app.utils.encryption import (
    derive_key,
    encrypt,
    decrypt,
    encrypt_conversation_message,
    decrypt_conversation_message,
    parse_versioned_data,
    EncryptionError,
    DecryptionError
)


class TestHKDFKeyDerivation:
    """Test HKDF key derivation from master key."""
    
    def test_derive_key_deterministic(self):
        """Same purpose + version should derive same key."""
        key1 = derive_key("conversations", version=1)
        key2 = derive_key("conversations", version=1)
        assert key1 == key2
    
    def test_derive_key_different_purposes(self):
        """Different purposes should derive different keys."""
        conv_key = derive_key("conversations", version=1)
        settings_key = derive_key("settings", version=1)
        assert conv_key != settings_key
    
    def test_derive_key_different_versions(self):
        """Different versions should derive different keys."""
        key_v1 = derive_key("conversations", version=1)
        key_v2 = derive_key("conversations", version=2)
        assert key_v1 != key_v2


class TestVersionedEncryption:
    """Test encryption with version prefixes."""
    
    def test_encrypt_adds_version_prefix(self):
        """Encrypted data should have version prefix."""
        plaintext = "Hello, world!"
        encrypted = encrypt(plaintext, "conversations", version=1)
        
        assert encrypted.startswith("v1:")
        assert len(encrypted) > len("v1:")
    
    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt should return original text."""
        plaintext = "This is a secret message"
        encrypted = encrypt(plaintext, "conversations", version=1)
        decrypted = decrypt(encrypted, "conversations")
        
        assert decrypted == plaintext
    
    def test_decrypt_auto_detects_version(self):
        """Decryption should automatically use correct key version."""
        plaintext = "Test message"
        
        # Encrypt with v1
        encrypted_v1 = encrypt(plaintext, "conversations", version=1)
        decrypted_v1 = decrypt(encrypted_v1, "conversations")
        assert decrypted_v1 == plaintext
        
        # Encrypt with v2 (different key)
        encrypted_v2 = encrypt(plaintext, "conversations", version=2)
        decrypted_v2 = decrypt(encrypted_v2, "conversations")
        assert decrypted_v2 == plaintext
        
        # Ciphertexts should be different
        assert encrypted_v1 != encrypted_v2
    
    def test_encrypt_empty_string(self):
        """Empty strings should be handled gracefully."""
        encrypted = encrypt("", "conversations", version=1)
        assert encrypted == ""
    
    def test_encrypt_unicode(self):
        """Unicode characters should be encrypted correctly."""
        plaintext = "Hello 世界 🌍"
        encrypted = encrypt(plaintext, "conversations", version=1)
        decrypted = decrypt(encrypted, "conversations")
        
        assert decrypted == plaintext
    
    def test_decrypt_wrong_purpose_fails(self):
        """Decrypting with wrong purpose should fail."""
        plaintext = "Secret"
        encrypted = encrypt(plaintext, "conversations", version=1)
        
        # Different purpose = different key = decryption failure
        with pytest.raises(DecryptionError):
            decrypt(encrypted, "settings")


class TestVersionParsing:
    """Test version prefix parsing."""
    
    def test_parse_valid_version(self):
        """Valid version prefix should parse correctly."""
        version, data = parse_versioned_data("v1:gAAAAABf...")
        assert version == 1
        assert data == "gAAAAABf..."
    
    def test_parse_multi_digit_version(self):
        """Multi-digit versions should parse correctly."""
        version, data = parse_versioned_data("v42:somedata")
        assert version == 42
        assert data == "somedata"
    
    def test_parse_missing_colon_fails(self):
        """Missing colon should raise ValueError."""
        with pytest.raises(ValueError, match="missing version prefix"):
            parse_versioned_data("v1gAAAAABf...")
    
    def test_parse_invalid_prefix_fails(self):
        """Invalid prefix should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid version prefix"):
            parse_versioned_data("x1:data")
    
    def test_parse_non_numeric_version_fails(self):
        """Non-numeric version should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid version number"):
            parse_versioned_data("vabc:data")


class TestConvenienceWrappers:
    """Test convenience wrapper functions."""
    
    def test_conversation_message_wrappers(self):
        """Conversation message wrappers should work."""
        plaintext = "User query"
        encrypted = encrypt_conversation_message(plaintext)
        decrypted = decrypt_conversation_message(encrypted)
        
        assert encrypted.startswith("v1:")
        assert decrypted == plaintext
    
    def test_conversation_message_custom_version(self):
        """Should support custom version in wrapper."""
        plaintext = "User query"
        encrypted = encrypt_conversation_message(plaintext, version=2)
        
        assert encrypted.startswith("v2:")
        
        decrypted = decrypt_conversation_message(encrypted)
        assert decrypted == plaintext


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_long_message(self):
        """Very long messages should encrypt/decrypt correctly."""
        plaintext = "A" * 100000  # 100KB message
        encrypted = encrypt(plaintext, "conversations", version=1)
        decrypted = decrypt(encrypted, "conversations")
        
        assert decrypted == plaintext
    
    def test_special_characters(self):
        """Special characters should be handled correctly."""
        plaintext = "Line1\nLine2\tTab\r\nWindows\\Path"
        encrypted = encrypt(plaintext, "conversations", version=1)
        decrypted = decrypt(encrypted, "conversations")
        
        assert decrypted == plaintext
    
    def test_corrupted_ciphertext_fails(self):
        """Corrupted ciphertext should raise DecryptionError."""
        encrypted = "v1:corrupted_invalid_base64!!!"
        
        with pytest.raises(DecryptionError):
            decrypt(encrypted, "conversations")
