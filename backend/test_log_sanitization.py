"""
Quick test to demonstrate automatic log sanitization.

Run with: python test_log_sanitization.py
"""
from app.core.logging import setup_logging

# Setup logger
logger = setup_logging("test_sanitizer")

print("=" * 80)
print("TESTING AUTOMATIC LOG SANITIZATION")
print("=" * 80)

# Test 1: Dict with sensitive fields
print("\n1. Dictionary with password and token:")
user_data = {
    'username': 'john_doe',
    'password': 'SuperSecret123!',
    'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature',
    'email': 'john@example.com'
}
logger.info(f"User data: {user_data}")

# Test 2: String with JWT token
print("\n2. String with JWT token:")
logger.info(f"Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.test")

# Test 3: Nested structure
print("\n3. Nested structure with credentials:")
payload = {
    'user': {
        'id': 123,
        'credentials': {
            'username': 'admin',
            'password': 'admin_secret_pass'
        }
    },
    'reset_token': 'abc123xyz789',
    'api_key': 'sk-proj-1234567890abcdef'
}
logger.info(f"Payload: {payload}")

# Test 4: Database URL with password
print("\n4. Database URL with password:")
logger.info(f"Database: postgresql://user:MyPassword123@localhost:5432/db")

# Test 5: Args-style logging
print("\n5. Args-style logging:")
logger.info("User: %s, Password: %s, Token: %s", "alice", "alice_secret", "token_xyz123")

# Test 6: API key in string
print("\n6. API key in string:")
logger.info("API Key: sk-proj-abcdefghijklmnopqrstuvwxyz123456")

# Test 7: Safe data (should NOT be redacted)
print("\n7. Safe data (should remain visible):")
safe_data = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'role': 'admin',
    'last_login': '2026-01-15'
}
logger.info(f"Safe data: {safe_data}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nAll sensitive data should show as '[REDACTED]' or '[REDACTED_JWT]'")
print("while safe data like email, name, role should remain visible.")
