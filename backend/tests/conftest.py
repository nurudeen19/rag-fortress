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
