"""State schema for the scikit-learn subagent."""

from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class SklearnState(TypedDict, total=False):
    """Typed state for the sklearn subagent graph.

    Extends BaseMLState with sklearn-specific fields.
    All base fields are inlined here (rather than using inheritance)
    because TypedDict inheritance with Annotated fields and LangGraph
    requires all fields to be visible at the class level.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input context --
    objective: str
    data_description: str
    data_file_path: str | None
    problem_type: str | None

    # -- Phase 1: Data Analysis --
    data_profile: dict | None
    eda_code: str | None
    eda_output: str | None

    # -- Phase 2: Strategy --
    strategy: dict | None
    candidate_algorithms: list[str]
    preprocessing_plan: list[str]
    feature_engineering_plan: list[str]
    hyperparameter_spaces: dict | None
    cv_strategy: str | None
    success_criteria: dict | None

    # -- Phase 3: Code Generation & Execution --
    generated_code: str | None
    execution_output: str | None
    execution_success: bool
    execution_error: str | None
    execution_metrics: list[dict]

    # -- Phase 3b: Duration estimation --
    estimated_duration_seconds: float | None
    dynamic_timeout: int | None
    data_subset_size: int | None

    # -- Phase 4: Results & Iteration --
    experiment_history: Annotated[list[dict], operator.add]
    best_experiment: dict | None
    current_iteration: int
    max_iterations: int
    next_action: str | None
    refinement_context: str | None

    # -- Reflection & learning --
    reflection: str | None
    learned_heuristics: list[str]

    # -- Control --
    phase: str
    experiment_id: str | None
    error: str | None
    progress_events: list[dict]

    # -- Sklearn-specific --
    search_results: str | None
