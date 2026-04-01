"""State schema for the summary agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class SummaryState(TypedDict, total=False):
    """Typed state for the summary agent graph.

    The summary agent reviews all experiment runs, selects the best model,
    and generates a comprehensive markdown report.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input --
    objective: str
    problem_type: str | None
    execution_plan: dict | None
    analysis_report: str | None
    sklearn_results: dict | None
    experiment_history: list[dict]
    runs: list[dict]
    test_metrics: dict | None  # Metrics on held-out test set

    # -- Analysis --
    best_model: str | None
    best_hyperparameters: dict | None
    best_metrics: dict | None
    model_comparison: list[dict]

    # -- Output --
    summary_report: str | None

    # -- Control --
    experiment_id: str | None
    error: str | None
