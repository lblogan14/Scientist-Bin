"""Shared test fixtures."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from scientist_bin_backend.config.settings import Settings


@pytest.fixture()
def mock_settings():
    """Return a Settings instance with test values (no real API key needed)."""
    return Settings(
        google_api_key="test-key-not-real",
        gemini_model="gemini-2.0-flash",
        debug=True,
        cors_origins=["http://localhost:5173"],
    )


@pytest.fixture()
def app(mock_settings):
    """Create a fresh FastAPI app with mocked settings."""
    with patch(
        "scientist_bin_backend.config.settings.get_settings",
        return_value=mock_settings,
    ):
        from scientist_bin_backend.main import create_app

        yield create_app()


@pytest.fixture()
def client(app):
    """Return a FastAPI TestClient bound to the test app."""
    return TestClient(app)
