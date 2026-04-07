"""End-to-end FLAML pipeline tests with real LLM and code execution.

Mirrors ``test_e2e_pipeline.py`` structure for the FLAML AutoML framework,
covering classification, regression, and time-series forecasting.

These tests invoke the real LLM (Google Gemini) and execute real FLAML
training code. They are marked ``@pytest.mark.slow`` and skipped when
``GOOGLE_API_KEY`` is not set.

Run with::

    uv run pytest tests/test_e2e_flaml.py -v --timeout=600 -m slow

"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.e2e_helpers import assert_artifact_files, cleanup_artifacts

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

IRIS_PATH = _DATA_DIR / "iris_data" / "Iris.csv"
WINE_PATH = _DATA_DIR / "wine_data" / "WineQT.csv"
ELECTRIC_PATH = _DATA_DIR / "electric_data" / "Electric_Production.csv"

_HAS_API_KEY = bool(os.environ.get("GOOGLE_API_KEY"))
_SKIP_REASON = "GOOGLE_API_KEY not set — skipping live E2E test"


# ---------------------------------------------------------------------------
# FLAML Classification
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not IRIS_PATH.is_file(), reason=f"Dataset not found: {IRIS_PATH}")
@pytest.mark.timeout(600)
async def test_flaml_classification_iris():
    """Run the full FLAML classification pipeline on the Iris dataset."""
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest

    request = TrainRequest(
        objective="Classify iris species from petal and sepal measurements using FLAML AutoML",
        data_file_path=str(IRIS_PATH),
        framework_preference="flaml",
        auto_approve_plan=True,
    )

    agent = CentralAgent()
    result: AgentResponse = await agent.run(request)

    assert result.status != "failed", f"Pipeline failed: {result}"
    assert result.problem_type == "classification"
    assert result.framework == "flaml"
    assert result.best_model is not None, "No best model selected"
    assert result.iterations >= 1, "Should have at least 1 iteration"

    assert len(result.experiment_history) >= 1
    for record in result.experiment_history:
        assert "algorithm" in record
        assert "metrics" in record
        assert "training_time_seconds" in record

    assert result.plan is not None or result.plan_markdown is not None
    assert result.analysis_report is not None
    assert result.summary_report is not None


# ---------------------------------------------------------------------------
# FLAML Regression
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not WINE_PATH.is_file(), reason=f"Dataset not found: {WINE_PATH}")
@pytest.mark.timeout(600)
async def test_flaml_regression_wine():
    """Run the full FLAML regression pipeline on the Wine Quality dataset."""
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest

    request = TrainRequest(
        objective="Predict wine quality score from physicochemical properties using FLAML AutoML",
        data_file_path=str(WINE_PATH),
        framework_preference="flaml",
        auto_approve_plan=True,
    )

    agent = CentralAgent()
    result: AgentResponse = await agent.run(request)

    assert result.status != "failed", f"Pipeline failed: {result}"
    assert result.problem_type == "regression"
    assert result.framework == "flaml"
    assert result.best_model is not None
    assert result.iterations >= 1

    assert len(result.experiment_history) >= 1
    for record in result.experiment_history:
        assert "algorithm" in record
        assert "metrics" in record

    assert result.analysis_report is not None
    assert result.summary_report is not None


# ---------------------------------------------------------------------------
# FLAML Time Series Forecast
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not ELECTRIC_PATH.is_file(), reason=f"Dataset not found: {ELECTRIC_PATH}")
@pytest.mark.timeout(600)
async def test_flaml_ts_forecast_electric():
    """Run the full FLAML time-series forecast pipeline on Electric Production."""
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest

    request = TrainRequest(
        objective="Forecast monthly electric production from historical data using FLAML AutoML",
        data_file_path=str(ELECTRIC_PATH),
        framework_preference="flaml",
        auto_approve_plan=True,
    )

    agent = CentralAgent()
    result: AgentResponse = await agent.run(request)

    assert result.status != "failed", f"Pipeline failed: {result}"
    assert result.problem_type == "ts_forecast"
    assert result.framework == "flaml"
    assert result.best_model is not None
    assert result.iterations >= 1

    assert len(result.experiment_history) >= 1
    assert result.analysis_report is not None
    assert result.summary_report is not None


# ---------------------------------------------------------------------------
# Artifact generation
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not IRIS_PATH.is_file(), reason=f"Dataset not found: {IRIS_PATH}")
@pytest.mark.timeout(600)
async def test_flaml_classification_artifacts_saved():
    """Verify artifact generation for a FLAML classification run."""
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest
    from scientist_bin_backend.utils.artifacts import save_experiment_artifacts
    from scientist_bin_backend.utils.naming import generate_experiment_id

    experiment_id = generate_experiment_id("e2e-flaml-artifact-iris")

    request = TrainRequest(
        objective="Classify iris for FLAML artifact test",
        data_file_path=str(IRIS_PATH),
        framework_preference="flaml",
        auto_approve_plan=True,
    )

    agent = CentralAgent()
    result: AgentResponse = await agent.run(request, experiment_id=experiment_id)

    assert result.status != "failed", f"Pipeline failed: {result}"

    result_dict = result.model_dump()
    save_experiment_artifacts(experiment_id, result_dict)

    try:
        assert_artifact_files(experiment_id, check_model=True)
    finally:
        cleanup_artifacts(experiment_id)


@pytest.mark.slow
@pytest.mark.skipif(not _HAS_API_KEY, reason=_SKIP_REASON)
@pytest.mark.skipif(not ELECTRIC_PATH.is_file(), reason=f"Dataset not found: {ELECTRIC_PATH}")
@pytest.mark.timeout(600)
async def test_flaml_ts_forecast_artifacts_saved():
    """Verify artifact generation for a FLAML time-series forecast run."""
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest
    from scientist_bin_backend.utils.artifacts import save_experiment_artifacts
    from scientist_bin_backend.utils.naming import generate_experiment_id

    experiment_id = generate_experiment_id("e2e-flaml-artifact-electric")

    request = TrainRequest(
        objective="Forecast electric production for FLAML artifact test",
        data_file_path=str(ELECTRIC_PATH),
        framework_preference="flaml",
        auto_approve_plan=True,
    )

    agent = CentralAgent()
    result: AgentResponse = await agent.run(request, experiment_id=experiment_id)

    assert result.status != "failed", f"Pipeline failed: {result}"

    result_dict = result.model_dump()
    save_experiment_artifacts(experiment_id, result_dict)

    try:
        assert_artifact_files(experiment_id, check_model=True)
    finally:
        cleanup_artifacts(experiment_id)
