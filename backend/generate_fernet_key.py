#!/usr/bin/env python3
"""
Fernet Key Generator

Generates a secure Fernet encryption key for any encryption field in the application.
Run this script whenever you need to generate a new encryption key.

Usage:
    python generate_fernet_key.py

The generated key can be used for any encryption field in your .env file, such as:
    - SETTINGS_ENCRYPTION_KEY (for encrypting sensitive settings)
    - Any other field requiring Fernet encryption

IMPORTANT: Keep this key secure and never commit it to version control!
"""

from cryptography.fernet import Fernet


def generate_key() -> str:
    """Generate a new Fernet encryption key."""
    key = Fernet.generate_key()
    return key.decode('utf-8')


if __name__ == "__main__":
    key = generate_key()
    
    print("=" * 70)
    print("FERNET ENCRYPTION KEY GENERATOR")
    print("=" * 70)
    print()
    print("Generated Key:")
    print(f"Use this key for any encryption field in your .env file:")
    print(f"  SETTINGS_ENCRYPTION_KEY={key}")
    print(f"  <OTHER_ENCRYPTION_FIELD>={key}")
    print()
    print("⚠️  SECURITY WARNING:")
    print("  - Keep this key secure and private")
    print("  - Never commit it to version control")
    print("  - Store it in a secure location (password manager, vault, etc.)")
    print("  - Changing this key will invalidate all encrypted data using it")
    print("  - Each encryption field can use a different key for isolation")
    print("  - Store it in a secure location (password manager, vault, etc.)")
    print("  - Changing this key will invalidate all encrypted settings")
    print("=" * 70)
