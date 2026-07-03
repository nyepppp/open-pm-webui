"""
Pytest fixtures for PM module smoke tests.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from open_webui.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return authentication headers for testing."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }