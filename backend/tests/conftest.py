"""Shared test fixtures."""

from pathlib import Path
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
def app(mock_settings, tmp_path: Path):
    """Create a fresh FastAPI app with mocked settings and isolated store."""
    from scientist_bin_backend.api import experiments

    # Use a temp directory so tests start with an empty experiment store
    fresh_store = experiments.ExperimentStore(store_dir=tmp_path / "experiments")

    with (
        patch(
            "scientist_bin_backend.config.settings.get_settings",
            return_value=mock_settings,
        ),
        patch.object(experiments, "experiment_store", fresh_store),
        patch("scientist_bin_backend.api.routes.experiment_store", fresh_store),
    ):
        from scientist_bin_backend.main import create_app

        yield create_app()


@pytest.fixture()
def client(app):
    """Return a FastAPI TestClient bound to the test app."""
    return TestClient(app)
