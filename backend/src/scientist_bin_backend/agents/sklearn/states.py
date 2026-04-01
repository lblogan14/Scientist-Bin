"""State schema for the scikit-learn subagent.

The sklearn agent receives a pre-built execution plan and split data paths
from the plan and analyst agents.  It focuses on code generation, execution,
iterative refinement, and finalization.
"""

from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class SklearnState(TypedDict, total=False):
    """Typed state for the sklearn subagent graph."""

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input (from Plan + Analyst agents) --
    objective: str
    execution_plan: dict | None
    analysis_report: str | None
    split_data_paths: dict | None  # {"train": path, "val": path, "test": path}
    problem_type: str | None
    data_profile: dict | None

    # -- Strategy (derived from execution_plan on first iteration) --
    strategy: dict | None
    candidate_algorithms: list[str]
    hyperparameter_spaces: dict | None

    # -- Code Generation & Execution --
    generated_code: str | None
    execution_output: str | None
    execution_success: bool
    execution_error: str | None
    execution_metrics: list[dict]

    # -- Duration estimation --
    estimated_duration_seconds: float | None
    dynamic_timeout: int | None

    # -- Runs & Iteration --
    experiment_history: Annotated[list[dict], operator.add]
    best_run: dict | None
    current_iteration: int
    max_iterations: int
    next_action: str | None
    refinement_context: str | None

    # -- Error research (web search) --
    search_results: str | None

    # -- Hyperparameter listing for summary --
    hyperparameters_summary: list[dict]

    # -- Reflection & learning --
    reflection: str | None
    learned_heuristics: list[str]

    # -- Success criteria --
    success_criteria: dict | None

    # -- Control --
    phase: str
    experiment_id: str | None
    error: str | None
    progress_events: list[dict]
