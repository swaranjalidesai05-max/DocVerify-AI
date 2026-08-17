"""DocVerify AI - Tests configuration"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    os.environ["DATABASE_URL"] = "sqlite:///./test_docverify.db"
    os.environ["SECRET_KEY"] = "test-secret-key-32-characters-min"
    os.environ["DEMO_MODE"] = "true"
    from app.core.config import get_settings
    get_settings.cache_clear()
    return get_settings()
