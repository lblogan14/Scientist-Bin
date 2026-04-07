"""State schema for the campaign orchestrator agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CampaignState(TypedDict):
    """Full state for the campaign orchestrator loop.

    The campaign agent wraps the existing 5-agent pipeline in an iterative
    loop, generating hypotheses, running experiments, extracting insights,
    and deciding whether to continue or stop.
    """

    # --- Input (set once at the start) ---
    objective: str
    """High-level research objective, e.g. 'Find the best classifier for iris species'."""

    data_file_path: str
    """Absolute path to the dataset file."""

    data_description: str
    """Free-text description of the dataset characteristics."""

    budget_max_iterations: int
    """Maximum number of experiments the campaign is allowed to run."""

    budget_time_limit_seconds: float
    """Wall-clock time limit in seconds for the entire campaign."""

    # --- Loop control ---
    current_iteration: int
    """Zero-based counter incremented after each experiment."""

    start_time: float
    """Epoch timestamp (``time.time()``) when the campaign started."""

    # --- Hypothesis management ---
    hypotheses: list[dict]
    """Ranked list of hypotheses to try. Each dict matches ``Hypothesis.model_dump()``."""

    # --- Results accumulation ---
    completed_experiments: list[dict]
    """Results from completed experiments (one dict per iteration)."""

    findings_summary: str
    """Accumulated insights extracted after each experiment (Findings Memory)."""

    best_result: dict
    """Best result observed so far across all iterations."""

    # --- Status ---
    campaign_status: str
    """Current status: 'running', 'budget_exhausted', 'converged', or 'completed'."""

    # --- LangGraph messages ---
    messages: Annotated[list, add_messages]
