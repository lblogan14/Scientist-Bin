"""State schema for the central orchestrator agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class CentralState(TypedDict):
    """Typed state passed through the central agent graph.

    The central agent orchestrates the full pipeline:
    analyze → route → plan → analyst → sklearn → summary → END
    """

    messages: Annotated[list, add_messages]
    objective: str
    data_description: str
    data_file_path: str | None
    framework_preference: str | None
    selected_framework: str | None

    # Pipeline outputs flowing between agents
    execution_plan: dict | None
    plan_approved: bool
    plan_markdown: str | None
    analysis_report: str | None
    split_data_paths: dict | None
    problem_type: str | None
    data_profile: dict | None
    sklearn_results: dict | None
    summary_report: str | None

    agent_response: dict | None
    experiment_id: str | None
    error: str | None
