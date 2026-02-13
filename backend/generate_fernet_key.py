#!/usr/bin/env python3
"""
Fernet Key Generator

Generates secure Fernet encryption keys for application.
Run this script to generate all required encryption keys at once.

Usage:
    python generate_fernet_key.py

The generated keys should be copied to your .env file:
    - SECRET_KEY (for JWT token signing)
    - MASTER_ENCRYPTION_KEY (for encrypting sensitive data)
    - SETTINGS_ENCRYPTION_KEY (for encrypting settings)

IMPORTANT: Keep these keys secure and never commit them to version control!
"""

from cryptography.fernet import Fernet


def generate_key() -> str:
    """Generate a new Fernet encryption key."""
    key = Fernet.generate_key()
    return key.decode('utf-8')


if __name__ == "__main__":
    # Generate three separate keys for different purposes
    secret_key = generate_key()
    master_key = generate_key()
    settings_key = generate_key()
    
    print("=" * 80)
    print("ENCRYPTION KEY GENERATOR FOR RAG FORTRESS")
    print("=" * 80)
    print()
    print("Copy these keys to your .env.docker or .env file:")
    print()
    print("# JWT token signing key")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("# Master encryption key for sensitive data")
    print(f"MASTER_ENCRYPTION_KEY={master_key}")
    print()
    print("# Settings encryption key")
    print(f"SETTINGS_ENCRYPTION_KEY={settings_key}")
    print()
    print("=" * 80)
    print("⚠️  SECURITY WARNING:")
    print("  • Keep these keys secure and private")
    print("  • Never commit them to version control")
    print("  • Store them in a secure location (password manager, vault, etc.)")
    print("  • Changing these keys will invalidate all encrypted data")
    print("  • Each key serves a different purpose - do not reuse them")
    print("=" * 80)
