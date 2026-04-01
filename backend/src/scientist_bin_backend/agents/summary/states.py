"""State schema for the summary agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class SummaryState(TypedDict, total=False):
    """Typed state for the summary agent graph.

    The summary agent reviews all experiment runs, selects the best model,
    and generates a comprehensive markdown report enriched with pre-computed
    diagnostics (CV stability, overfitting analysis, feature importances, etc.).

    Flow:
        collect_context → compute_diagnostics → review_and_rank
        → generate_report → save_artifacts → END
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input from upstream agents --
    objective: str
    problem_type: str | None

    # From analyst agent
    analysis_report: str | None
    data_profile: dict | None
    split_data_paths: dict | None  # {"train": path, "val": path, "test": path}

    # From plan agent
    execution_plan: dict | None
    plan_markdown: str | None

    # From framework agent
    framework_results: dict | None  # Full results dict from framework agent
    experiment_history: list[dict]
    test_metrics: dict | None  # Metrics on held-out test set
    test_diagnostics: dict | None  # Enriched test results (confusion_matrix, etc.)
    generated_code: str | None  # For reproducibility section
    test_evaluation_code: str | None  # For reproducibility section

    # -- Computed by collect_context --
    summary_context: dict | None  # Normalized, organized upstream data

    # -- Computed by compute_diagnostics --
    diagnostics: dict | None  # Pre-computed analytics & chart data

    # -- From review_and_rank --
    model_rankings: list[dict]
    best_model: str | None
    best_hyperparameters: dict | None
    best_metrics: dict | None
    selection_reasoning: str | None

    # -- Output --
    summary_report: str | None
    report_sections: dict | None  # Structured sections for frontend rendering

    # -- Control --
    experiment_id: str | None
    error: str | None
