"""State schemas for the central orchestrator agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class CentralState(TypedDict):
    """Central agent's own fields (analyze + route nodes).

    These fields are read/written by the central agent's analyze and route
    nodes. They represent the orchestrator's understanding of the request.
    """

    messages: Annotated[list, add_messages]
    objective: str
    data_description: str
    data_file_path: str | None
    framework_preference: str | None
    selected_framework: str | None
    task_analysis: dict | None
    plan_approved: bool
    experiment_id: str | None
    error: str | None


class PipelineState(CentralState):
    """Extended state for the full agent pipeline.

    The StateGraph uses this type. Central-agent nodes only touch
    CentralState fields; delegate nodes populate the pipeline fields
    below as they execute.
    """

    # Analyst agent outputs
    analysis_report: str | None
    split_data_paths: dict | None
    problem_type: str | None
    data_profile: dict | None
    # Plan agent outputs
    execution_plan: dict | None
    plan_markdown: str | None
    # Framework agent outputs (generic key for any framework)
    framework_results: dict | None
    # Summary agent outputs
    summary_report: str | None
    # Final assembled response
    agent_response: dict | None
