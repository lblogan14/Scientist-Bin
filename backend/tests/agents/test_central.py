"""Tests for the central agent schemas and utilities."""

from scientist_bin_backend.agents.central.schemas import (
    AgentResponse,
    FrameworkSelection,
    TrainRequest,
)
from scientist_bin_backend.agents.central.utils import (
    build_initial_state,
    is_supported_framework,
)


def test_train_request_defaults():
    req = TrainRequest(objective="Classify iris")
    assert req.objective == "Classify iris"
    assert req.data_description == ""
    assert req.framework_preference is None


def test_train_request_full():
    req = TrainRequest(
        objective="Classify iris",
        data_description="4 features, 3 classes",
        framework_preference="sklearn",
    )
    assert req.framework_preference == "sklearn"


def test_framework_selection_schema():
    sel = FrameworkSelection(framework="sklearn", reasoning="tabular data")
    assert sel.framework == "sklearn"
    assert sel.reasoning == "tabular data"


def test_agent_response_defaults():
    resp = AgentResponse(framework="sklearn")
    assert resp.status == "completed"
    assert resp.plan is None
    assert resp.generated_code is None


def test_build_initial_state():
    req = TrainRequest(objective="Test", data_description="some data")
    state = build_initial_state(req)
    assert state["objective"] == "Test"
    assert state["data_description"] == "some data"
    assert state["selected_framework"] is None
    assert state["messages"] == []


def test_is_supported_framework():
    assert is_supported_framework("sklearn") is True
    assert is_supported_framework("SKLEARN") is True
    assert is_supported_framework("pytorch") is False
