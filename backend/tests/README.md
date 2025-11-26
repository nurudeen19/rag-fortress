# Backend Tests

This directory contains all the tests for the RAG Fortress backend.

## Structure

```
tests/
├── conftest.py           # Pytest configuration and shared fixtures
├── test_settings.py      # Settings and configuration tests
└── __init__.py           # Python package marker
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/test_settings.py
pytest tests/test_encryption_settings.py
pytest tests/test_exceptions.py
```

### Run specific test class
```bash
pytest tests/test_encryption_settings.py::TestEncryptionSecurity
```

### Run specific test
```bash
pytest tests/test_encryption_settings.py::TestEncryptionSecurity::test_database_stores_encrypted
```

### Run with verbose output
```bash
pytest -v
```

### Run async tests only
```bash
pytest -v -m asyncio
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run tests requiring database
```bash
# Ensure database is running first
pytest tests/test_encryption_settings.py -v
```

## Test Categories

### test_settings.py
Tests ENV-based settings configuration:
- **TestSettingsBasic**: Default settings, ENV override behavior
- **TestLLMConfiguration**: LLM provider configs (OpenAI, Google, HuggingFace)
- **TestFallbackLLMConfiguration**: Fallback LLM system validation
- **TestCORSConfiguration**: CORS settings
- **TestEmbeddingProviderConfiguration**: Embedding provider configs
- **TestVectorDBConfiguration**: Vector database configuration

### test_encryption_settings.py (NEW)
Tests database-backed settings with encryption:
- **TestEncryptionSecurity**: Ensures API keys stay encrypted until accessed
  - Database stores encrypted values
  - Cache stores encrypted values
  - Memory stores encrypted values
  - Lazy decryption on attribute access
  - Consistent decryption across multiple accesses
- **TestSettingsPriority**: DB → ENV → defaults priority
  - NULL DB values fall back to defaults
  - DB values override defaults
  - Changes reflected after reload
  - Clearing DB returns to defaults
- **TestSettingsService**: SettingsService encryption behavior
  - Auto-detects and encrypts sensitive keys
  - Encrypts on create/update
  - Decrypts on get_value()
  - Non-sensitive values not encrypted

### test_exceptions.py
Tests exception handling system:
- Base exception classes
- Configuration, LLM, Document, Vector Store exceptions
- Database and Auth exceptions
- Validation and rate limiting
- Exception handlers integration

## Writing New Tests

### Example test structure:

```python
class TestMyFeature:
    """Test my feature"""
    
    def test_basic_functionality(self, clean_env, base_env):
        """Test description"""
        # Setup
        env = {**base_env, "MY_CONFIG": "value"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            settings = Settings()
            
            # Test
            assert settings.MY_CONFIG == "value"
    
    def test_error_handling(self, clean_env, base_env):
        """Test error cases"""
        env = {**base_env, "MY_CONFIG": "invalid"}
        
        with patch.dict(os.environ, env, clear=True):
            from app.config.settings import Settings
            
            with pytest.raises(ValueError, match="error message"):
                Settings()
```

## Fixtures

### clean_env
Provides a clean environment for each test by clearing relevant environment variables.

### base_env
Provides minimal required environment variables for settings to load.

Usage:
```python
def test_something(self, clean_env, base_env):
    env = {**base_env, "ADDITIONAL_VAR": "value"}
    with patch.dict(os.environ, env, clear=True):
        # Your test code
```

## Best Practices

1. **Isolate tests**: Use `clean_env` fixture to prevent test pollution
2. **Clear assertions**: Use descriptive assertion messages
3. **Test edge cases**: Include both success and failure scenarios
4. **Document tests**: Add clear docstrings explaining what is being tested
5. **Group related tests**: Use test classes to organize related tests
6. **Mock external dependencies**: Don't make real API calls in tests

## Continuous Integration

These tests should be run in CI/CD pipeline:
```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest -v --cov=app
```

## Dependencies

Testing dependencies (should be in `requirements.txt`):
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1  # Required for async tests
```

## Important Notes

### Database-Dependent Tests
Tests in `test_encryption_settings.py` require:
- PostgreSQL database running
- Database initialized and migrated
- Application settings seeded

Run setup before testing:
```bash
python -m alembic upgrade head
python run_seeders.py application_settings
```

### ENV vs DB Settings
- `test_settings.py`: Tests ENV-based configuration (isolated, no DB)
- `test_encryption_settings.py`: Tests DB-backed settings (requires DB)

Choose the appropriate test file based on what you're testing.
