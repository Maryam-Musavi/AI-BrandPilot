"""Pytest configuration and fixtures for AI BrandPilot tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_message():
    """Sample chat message for testing."""
    return {"message": "Hello, how can you help me with my brand?"}


@pytest.fixture
def sample_chat_request(sample_message):
    """Sample chat request payload."""
    return sample_message
