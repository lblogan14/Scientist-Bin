"""Central agent utility helpers."""

from __future__ import annotations

from scientist_bin_backend.agents.central.schemas import TrainRequest
from scientist_bin_backend.agents.central.states import CentralState

SUPPORTED_FRAMEWORKS = {"sklearn"}


def build_initial_state(request: TrainRequest) -> CentralState:
    """Convert a TrainRequest into the initial CentralState dict."""
    return CentralState(
        messages=[],
        objective=request.objective,
        data_description=request.data_description,
        framework_preference=request.framework_preference,
        selected_framework=None,
        agent_response=None,
        error=None,
    )


def is_supported_framework(name: str) -> bool:
    """Check whether a framework identifier is currently supported."""
    return name.lower() in SUPPORTED_FRAMEWORKS
