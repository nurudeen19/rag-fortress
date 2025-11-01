# Quick Test Reference

## Running Tests

### Basic Commands

```bash
# Run all tests
cd backend && pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_settings.py

# Run specific test class
pytest tests/test_settings.py::TestFallbackLLMConfiguration

# Run specific test
pytest tests/test_settings.py::TestFallbackLLMConfiguration::test_same_provider_same_model_raises_error

# Run tests matching a pattern
pytest -k "fallback"
pytest -k "test_openai"
```

### Coverage Commands

```bash
# Run with coverage
pytest --cov=app

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# View report: open htmlcov/index.html

# Show missing lines
pytest --cov=app --cov-report=term-missing
```

### Useful Options

```bash
# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Show local variables in tracebacks
pytest -l

# Disable warnings
pytest --disable-warnings

# Show print statements
pytest -s
```

## Test Organization

Tests are organized by functionality:

- `test_settings.py` - Configuration and settings tests
  - `TestSettingsBasic` - Basic configuration
  - `TestLLMConfiguration` - LLM provider configs
  - `TestFallbackLLMConfiguration` - Fallback system
  - `TestCORSConfiguration` - CORS settings

## Common Test Patterns

### Testing Environment Variables

```python
def test_custom_setting(self, clean_env, base_env):
    env = {**base_env, "MY_VAR": "value"}
    with patch.dict(os.environ, env, clear=True):
        from app.config.settings import Settings
        settings = Settings()
        assert settings.MY_VAR == "value"
```

### Testing Validation Errors

```python
def test_invalid_input(self, clean_env, base_env):
    env = {**base_env, "MY_VAR": "invalid"}
    with patch.dict(os.environ, env, clear=True):
        from app.config.settings import Settings
        with pytest.raises(ValueError, match="error message"):
            Settings()
```

## Continuous Testing

### Watch Mode (requires pytest-watch)

```bash
pip install pytest-watch
ptw  # Runs pytest on file changes
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
pytest --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Make sure you're in the backend directory
cd backend
pytest

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Cache Issues

Clear pytest cache:
```bash
pytest --cache-clear
```

### Environment Pollution

Tests are isolated using the `clean_env` fixture. If you're seeing cross-test pollution:
1. Ensure you're using the `clean_env` fixture
2. Check that you're using `patch.dict(os.environ, env, clear=True)`

## Adding New Tests

1. Create test file in `tests/` with `test_` prefix
2. Create test class with `Test` prefix
3. Create test functions with `test_` prefix
4. Use fixtures for setup: `clean_env`, `base_env`
5. Document what you're testing with docstrings
6. Run tests to verify: `pytest tests/test_yourfile.py -v`
