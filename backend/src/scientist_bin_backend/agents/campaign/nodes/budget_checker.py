"""Budget checker node — decides whether the campaign loop should continue or stop."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def _evaluate_budget(state: dict) -> str:
    """Shared budget evaluation logic.

    Returns ``"continue"`` or ``"stop"`` and logs the decision.
    """
    iteration = state.get("current_iteration", 0)
    max_iterations = state.get("budget_max_iterations", 10)
    start_time = state.get("start_time", time.time())
    time_limit = state.get("budget_time_limit_seconds", 14400.0)

    elapsed = time.time() - start_time

    # Check iteration budget
    if iteration >= max_iterations:
        logger.info(
            "Budget exhausted: reached max iterations (%d/%d)",
            iteration,
            max_iterations,
        )
        return "stop"

    # Check time budget
    if elapsed >= time_limit:
        logger.info(
            "Budget exhausted: time limit reached (%.0fs / %.0fs)",
            elapsed,
            time_limit,
        )
        return "stop"

    logger.info(
        "Budget OK: iteration %d/%d, time %.0fs/%.0fs — continuing",
        iteration,
        max_iterations,
        elapsed,
        time_limit,
    )
    return "continue"


def check_budget_node(state: dict) -> dict:
    """LangGraph node that evaluates budget and writes campaign_status.

    Returns:
        Partial state update with ``campaign_status`` set to
        ``"budget_exhausted"`` or ``"running"``.
    """
    decision = _evaluate_budget(state)
    status = "budget_exhausted" if decision == "stop" else "running"
    return {"campaign_status": status}


def route_budget(state: dict) -> str:
    """Pure routing function for the conditional edge after check_budget.

    Returns:
        ``"continue"`` to loop back to hypothesis generation, or
        ``"stop"`` to end the campaign.
    """
    return _evaluate_budget(state)
