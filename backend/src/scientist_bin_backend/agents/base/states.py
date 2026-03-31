"""Shared state schemas for all ML framework subagents."""

from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class DataProfile(TypedDict, total=False):
    """Summary of dataset characteristics produced by EDA."""

    file_path: str
    shape: list[int]  # [rows, cols]
    column_names: list[str]
    dtypes: dict[str, str]
    missing_counts: dict[str, int]
    numeric_columns: list[str]
    categorical_columns: list[str]
    target_column: str | None
    class_distribution: dict[str, int] | None
    target_stats: dict[str, float] | None
    statistics_summary: str
    data_quality_issues: list[str]


class ExperimentRecord(TypedDict, total=False):
    """A single experiment iteration's results."""

    iteration: int
    algorithm: str
    hyperparameters: dict
    metrics: dict[str, float]
    training_time_seconds: float
    timestamp: str


class BaseMLState(TypedDict, total=False):
    """Base state schema shared by all ML framework subagents.

    Framework-specific subagents extend this with additional fields.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input context --
    objective: str
    data_description: str
    data_file_path: str | None
    problem_type: str | None

    # -- Phase 1: Data Analysis --
    data_profile: DataProfile | None
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
    data_subset_size: int | None  # For progressive training

    # -- Phase 4: Results & Iteration --
    experiment_history: Annotated[list[dict], operator.add]
    best_experiment: dict | None
    current_iteration: int
    max_iterations: int
    next_action: str | None
    refinement_context: str | None

    # -- Reflection & learning --
    reflection: str | None  # Agent's reflection on latest results
    learned_heuristics: list[str]  # Heuristics extracted from past experiments

    # -- Control --
    phase: str
    experiment_id: str | None
    error: str | None
    progress_events: list[dict]
