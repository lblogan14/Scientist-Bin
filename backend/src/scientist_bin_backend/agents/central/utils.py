"""Central agent utility helpers."""

from __future__ import annotations

from scientist_bin_backend.agents.central.schemas import TrainRequest
from scientist_bin_backend.agents.central.states import PipelineState


def build_initial_state(
    request: TrainRequest, *, experiment_id: str | None = None
) -> PipelineState:
    """Convert a TrainRequest into the initial PipelineState dict."""
    return PipelineState(
        messages=[],
        objective=request.objective,
        data_description=request.data_description,
        data_file_path=request.data_file_path,
        framework_preference=request.framework_preference,
        selected_framework=None,
        task_analysis=None,
        plan_approved=request.auto_approve_plan,
        experiment_id=experiment_id,
        error=None,
        # Pipeline fields (populated by delegates)
        analysis_report=None,
        split_data_paths=None,
        problem_type=None,
        data_profile=None,
        execution_plan=None,
        plan_markdown=None,
        framework_results=None,
        summary_report=None,
        agent_response=None,
    )
