"""API-driven FLAML E2E tests — verifies the train endpoint with FLAML framework.

Calls ``_run_training`` directly (no HTTP server needed) with an isolated
ExperimentStore, matching the pattern in ``test_e2e_pipeline.py``.

Run with::

    uv run pytest tests/test_e2e_api_flaml.py -v --timeout=600 -m slow

"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

IRIS_PATH = _DATA_DIR / "iris_data" / "Iris.csv"
ELECTRIC_PATH = _DATA_DIR / "electric_data" / "Electric_Production.csv"

_HAS_API_KEY = bool(os.environ.get("GOOGLE_API_KEY"))
_SKIP_REASON = "GOOGLE_API_KEY not set — skipping live E2E test"


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not IRIS_PATH.is_file(), reason=f"Dataset not found: {IRIS_PATH}")
@pytest.mark.timeout(600)
async def test_api_train_flaml_classification():
    """Submit a FLAML classification request via the API helper and verify completion."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, ExperimentStore
    from scientist_bin_backend.api.routes import _run_training

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperimentStore(store_dir=Path(tmpdir))
        experiment = store.create(
            objective="Classify iris via FLAML API E2E",
            data_file_path=str(IRIS_PATH),
            framework="flaml",
        )
        exp_id = experiment.id

        with patch("scientist_bin_backend.api.routes.experiment_store", store):
            await _run_training(
                experiment_id=exp_id,
                objective="Classify iris via FLAML API E2E",
                data_description="",
                data_file_path=str(IRIS_PATH),
                framework="flaml",
                auto_approve_plan=True,
                deep_research=False,
                budget_max_iterations=10,
                budget_time_limit_seconds=600.0,
            )

        updated = store.get(exp_id)
        assert updated is not None
        assert updated.status == ExperimentStatus.completed, (
            f"Expected completed, got {updated.status}. Result: {updated.result}"
        )
        assert updated.result is not None
        assert updated.problem_type == "classification"
        assert updated.framework == "flaml"


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not ELECTRIC_PATH.is_file(), reason=f"Dataset not found: {ELECTRIC_PATH}")
@pytest.mark.timeout(600)
async def test_api_train_flaml_ts_forecast():
    """Submit a FLAML time-series forecast request via the API helper."""
    from scientist_bin_backend.api.experiments import ExperimentStatus, ExperimentStore
    from scientist_bin_backend.api.routes import _run_training

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperimentStore(store_dir=Path(tmpdir))
        experiment = store.create(
            objective="Forecast electric production via FLAML API E2E",
            data_file_path=str(ELECTRIC_PATH),
            framework="flaml",
        )
        exp_id = experiment.id

        with patch("scientist_bin_backend.api.routes.experiment_store", store):
            await _run_training(
                experiment_id=exp_id,
                objective="Forecast electric production via FLAML API E2E",
                data_description="",
                data_file_path=str(ELECTRIC_PATH),
                framework="flaml",
                auto_approve_plan=True,
                deep_research=False,
                budget_max_iterations=10,
                budget_time_limit_seconds=600.0,
            )

        updated = store.get(exp_id)
        assert updated is not None
        assert updated.status == ExperimentStatus.completed, (
            f"Expected completed, got {updated.status}. Result: {updated.result}"
        )
        assert updated.result is not None
        assert updated.framework == "flaml"
