"""Tests for the central agent schemas and utilities."""

from __future__ import annotations

from scientist_bin_backend.agents.central.schemas import (
    AgentResponse,
    FrameworkSelection,
    TrainRequest,
)
from scientist_bin_backend.agents.central.states import PipelineState
from scientist_bin_backend.agents.central.utils import build_initial_state

# ---------------------------------------------------------------------------
# TrainRequest schema tests
# ---------------------------------------------------------------------------


def test_train_request_defaults():
    req = TrainRequest(objective="Classify iris")
    assert req.objective == "Classify iris"
    assert req.data_description == ""
    assert req.framework_preference is None
    assert req.data_file_path is None
    assert req.auto_approve_plan is False


def test_train_request_full():
    req = TrainRequest(
        objective="Classify iris",
        data_description="4 features, 3 classes",
        framework_preference="sklearn",
        data_file_path="data/iris.csv",
        auto_approve_plan=True,
    )
    assert req.framework_preference == "sklearn"
    assert req.data_file_path == "data/iris.csv"
    assert req.auto_approve_plan is True


def test_train_request_auto_approve_default_false():
    req = TrainRequest(objective="Test")
    assert req.auto_approve_plan is False


# ---------------------------------------------------------------------------
# FrameworkSelection schema tests
# ---------------------------------------------------------------------------


def test_framework_selection_schema():
    sel = FrameworkSelection(framework="sklearn", reasoning="tabular data")
    assert sel.framework == "sklearn"
    assert sel.reasoning == "tabular data"


# ---------------------------------------------------------------------------
# AgentResponse schema tests
# ---------------------------------------------------------------------------


def test_agent_response_defaults():
    resp = AgentResponse(framework="sklearn")
    assert resp.status == "completed"
    assert resp.plan is None
    assert resp.plan_markdown is None
    assert resp.generated_code is None
    assert resp.evaluation_results is None
    assert resp.experiment_history == []
    assert resp.data_profile is None
    assert resp.problem_type is None
    assert resp.iterations == 0
    assert resp.analysis_report is None
    assert resp.summary_report is None
    assert resp.best_model is None
    assert resp.best_hyperparameters is None


def test_agent_response_full():
    resp = AgentResponse(
        framework="sklearn",
        plan={"algorithms_to_try": ["RF"]},
        plan_markdown="# Plan\n\nUse RF",
        generated_code="import sklearn",
        evaluation_results={"accuracy": 0.95},
        experiment_history=[{"iteration": 1, "algorithm": "RF"}],
        data_profile={"shape": [150, 5]},
        problem_type="classification",
        iterations=3,
        analysis_report="Dataset is clean",
        summary_report="# Summary Report",
        best_model="RandomForestClassifier",
        best_hyperparameters={"n_estimators": 100, "max_depth": 5},
        status="completed",
    )
    assert resp.plan_markdown == "# Plan\n\nUse RF"
    assert resp.analysis_report == "Dataset is clean"
    assert resp.summary_report == "# Summary Report"
    assert resp.best_model == "RandomForestClassifier"
    assert resp.best_hyperparameters["n_estimators"] == 100
    assert resp.problem_type == "classification"
    assert resp.iterations == 3


# ---------------------------------------------------------------------------
# build_initial_state tests
# ---------------------------------------------------------------------------


def test_build_initial_state():
    req = TrainRequest(objective="Test", data_description="some data")
    state = build_initial_state(req)
    assert state["objective"] == "Test"
    assert state["data_description"] == "some data"
    assert state["data_file_path"] is None
    assert state["selected_framework"] is None
    assert state["messages"] == []
    # Pipeline fields
    assert state["execution_plan"] is None
    assert state["plan_approved"] is False
    assert state["plan_markdown"] is None
    assert state["analysis_report"] is None
    assert state["split_data_paths"] is None
    assert state["problem_type"] is None
    assert state["data_profile"] is None
    assert state["framework_results"] is None
    assert state["summary_report"] is None
    assert state["task_analysis"] is None
    # New analyst output fields
    assert state["classification_confidence"] is None
    assert state["classification_reasoning"] is None


def test_build_initial_state_with_data_file():
    req = TrainRequest(
        objective="Test",
        data_description="some data",
        data_file_path="data/iris.csv",
    )
    state = build_initial_state(req)
    assert state["data_file_path"] == "data/iris.csv"


def test_build_initial_state_auto_approve():
    req = TrainRequest(objective="Test", auto_approve_plan=True)
    state = build_initial_state(req)
    assert state["plan_approved"] is True


def test_build_initial_state_no_auto_approve():
    req = TrainRequest(objective="Test", auto_approve_plan=False)
    state = build_initial_state(req)
    assert state["plan_approved"] is False


def test_build_initial_state_with_experiment_id():
    req = TrainRequest(objective="Test")
    state = build_initial_state(req, experiment_id="exp-123")
    assert state["experiment_id"] == "exp-123"


def test_build_initial_state_without_experiment_id():
    req = TrainRequest(objective="Test")
    state = build_initial_state(req)
    assert state["experiment_id"] is None


# ---------------------------------------------------------------------------
# PipelineState tests
# ---------------------------------------------------------------------------


def test_pipeline_state_has_classification_fields():
    """PipelineState includes analyst classification feedback fields."""
    state: PipelineState = {
        "messages": [],
        "objective": "Test",
        "data_description": "",
        "data_file_path": None,
        "framework_preference": None,
        "selected_framework": None,
        "task_analysis": None,
        "plan_approved": False,
        "experiment_id": None,
        "error": None,
        "analysis_report": None,
        "split_data_paths": None,
        "problem_type": "classification",
        "data_profile": None,
        "classification_confidence": "confirmed",
        "classification_reasoning": "Target is categorical with 3 classes.",
        "execution_plan": None,
        "plan_markdown": None,
        "framework_results": None,
        "summary_report": None,
        "agent_response": None,
    }
    assert state["classification_confidence"] == "confirmed"
    assert state["classification_reasoning"] == "Target is categorical with 3 classes."


def test_pipeline_state_classification_overridden():
    """PipelineState correctly carries overridden classification."""
    state: PipelineState = {
        "messages": [],
        "objective": "Predict price",
        "data_description": "",
        "data_file_path": None,
        "framework_preference": None,
        "selected_framework": "sklearn",
        "task_analysis": {"task_type": "classification"},
        "plan_approved": False,
        "experiment_id": "test-456",
        "error": None,
        "analysis_report": None,
        "split_data_paths": None,
        "problem_type": "regression",
        "data_profile": None,
        "classification_confidence": "overridden",
        "classification_reasoning": "Target 'price' is continuous, not categorical.",
        "execution_plan": None,
        "plan_markdown": None,
        "framework_results": None,
        "summary_report": None,
        "agent_response": None,
    }
    assert state["classification_confidence"] == "overridden"
    assert state["problem_type"] == "regression"
    assert state["task_analysis"]["task_type"] == "classification"  # Original was different
