"""Shared state schemas for all ML framework subagents.

Framework-specific subagents extend ``BaseMLState`` with additional fields.
The base state covers the pipeline-driven flow where upstream agents (analyst,
plan) provide execution plans, split data paths, and data profiles.
"""

from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class DataProfile(TypedDict, total=False):
    """Summary of dataset characteristics produced by the analyst agent."""

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
    """A single experiment iteration's results.

    The base fields (iteration through timestamp) are always populated.
    Enriched diagnostic fields are optional — populated when the generated
    training code extracts them (e.g. sklearn CV fold scores, feature
    importances). Framework agents that don't produce a given field simply
    omit it.
    """

    iteration: int
    algorithm: str
    hyperparameters: dict
    metrics: dict[str, float]
    training_time_seconds: float
    timestamp: str

    # -- Enriched diagnostic fields (optional) --
    cv_fold_scores: dict[str, list[float]] | None  # e.g. {"accuracy": [0.95, 0.96, ...]}
    cv_results_top_n: list[dict] | None  # Top-N param combos from search
    feature_importances: list[dict] | None  # [{feature, importance}, ...]
    confusion_matrix: dict | None  # {labels: [...], matrix: [[...]]}
    residual_stats: dict | None  # Regression: {mean, std, max_abs, percentiles}


class BaseMLState(TypedDict, total=False):
    """Base state schema shared by all ML framework subagents.

    Framework-specific subagents extend this with additional fields.
    Fields are organised by pipeline phase.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input from upstream pipeline (analyst + plan agents) --
    objective: str
    execution_plan: dict | None
    analysis_report: str | None
    split_data_paths: dict | None  # {"train": path, "val": path, "test": path}
    problem_type: str | None
    data_profile: DataProfile | None

    # -- Strategy (derived from execution_plan on first iteration) --
    strategy: dict | None
    candidate_algorithms: list[str]
    hyperparameter_spaces: dict | None
    success_criteria: dict | None

    # -- Code validation (pre-execution) --
    generated_code: str | None
    validation_error: str | None
    validation_attempts: int

    # -- Code execution --
    execution_output: str | None
    execution_results_json: dict | None  # Parsed ===RESULTS=== JSON (avoids truncation)
    execution_success: bool
    execution_error: str | None
    execution_metrics: list[dict]

    # -- Duration estimation --
    estimated_duration_seconds: float | None
    dynamic_timeout: int | None
    data_subset_size: int | None  # For progressive training

    # -- Iteration & tracking --
    experiment_history: Annotated[list[dict], operator.add]
    best_experiment: dict | None
    current_iteration: int
    max_iterations: int
    next_action: str | None
    refinement_context: str | None

    # -- Test evaluation (held-out test set) --
    test_metrics: dict | None
    test_evaluation_code: str | None
    test_diagnostics: dict | None  # Enriched test results (confusion_matrix, residual_stats)

    # -- Error research (web search) --
    search_results: str | None

    # -- Reflection & learning (ERL pattern) --
    reflection: str | None
    learned_heuristics: list[str]

    # -- Output for summary agent --
    hyperparameters_summary: list[dict]

    # -- Control --
    phase: str
    experiment_id: str | None
    error: str | None
    progress_events: list[dict]
