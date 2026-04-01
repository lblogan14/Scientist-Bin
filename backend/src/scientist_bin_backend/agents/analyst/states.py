"""State schema for the analyst agent."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class AnalystState(TypedDict, total=False):
    """Typed state for the analyst agent graph.

    Tracks data profiling, cleaning, splitting, and reporting.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input context --
    objective: str
    data_file_path: str | None
    execution_plan: dict | None
    task_analysis: dict | None  # Upstream TaskAnalysis from central orchestrator
    data_description: str | None  # Original user dataset description
    selected_framework: str | None  # Framework chosen by central router

    # -- Phase 1: Profiling --
    problem_type: str | None
    classification_confidence: str | None  # "confirmed" | "refined" | "overridden"
    classification_reasoning: str | None  # Evidence from data for the decision
    data_profile: dict | None

    # -- Phase 2: Cleaning --
    cleaning_code: str | None
    cleaning_output: str | None
    cleaned_data_path: str | None

    # -- Phase 3: Splitting --
    split_code: str | None
    split_output: str | None
    split_data_paths: dict | None  # {train: path, val: path, test: path}

    # -- Phase 4: Report --
    analysis_report: str | None

    # -- Control --
    experiment_id: str | None
    error: str | None
