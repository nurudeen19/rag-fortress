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
```

### Run specific test class
```bash
pytest tests/test_settings.py::TestFallbackLLMConfiguration
```

### Run specific test
```bash
pytest tests/test_settings.py::TestFallbackLLMConfiguration::test_same_provider_same_model_raises_error
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Categories

### TestSettingsBasic
Tests basic settings functionality:
- Default settings loading
- Environment validation
- Production/development environment enforcement

### TestLLMConfiguration
Tests LLM provider configuration:
- OpenAI, Google, HuggingFace provider configs
- API key validation
- Model configuration
- Unsupported provider handling

### TestFallbackLLMConfiguration
Tests fallback LLM system:
- Default HuggingFace fallback
- Custom fallback models
- Different provider fallback
- Same provider/model validation
- API key reuse
- Provider config inheritance

### TestCORSConfiguration
Tests CORS settings:
- Default origins
- Custom origins

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

## Adding Dependencies

If you need additional testing dependencies, add them to `requirements.txt`:
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
```
