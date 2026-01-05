"""
Pytest configuration and shared fixtures.
"""
import sys
from pathlib import Path
import pytest

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with async support."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture
def base_env():
    """Provide base environment variables for tests."""
    return {
        "APP_NAME": "RAG Fortress",
        "APP_DESCRIPTION": "Secure document intelligence platform for teams",
        "APP_VERSION": "1.0.0",
        "DEBUG": "True",
        "ENVIRONMENT": "development",
        "LLM_PROVIDER": "openai",
        "LLM_API_KEY": "test_key",
        "LLM_MODEL": "gpt-4",
        "LLM_TEMPERATURE": "0.7",
        "LLM_MAX_TOKENS": "2000",
        "EMBEDDING_PROVIDER": "huggingface",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "VECTOR_DB_PROVIDER": "chroma",
    }


@pytest.fixture
async def clean_test_settings(db_session):
    """Clean up test settings before and after each test."""
    from sqlalchemy import text
    
    # Clean up before test
    await db_session.execute(
        text("DELETE FROM application_settings WHERE category = 'test'")
    )
    await db_session.commit()
    
    yield
    
    # Clean up after test
    await db_session.execute(
        text("DELETE FROM application_settings WHERE category = 'test'")
    )
    await db_session.commit()
