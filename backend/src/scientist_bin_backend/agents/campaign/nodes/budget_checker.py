"""Budget checker node — decides whether the campaign loop should continue or stop."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def check_budget(state: dict) -> str:
    """Check whether the campaign should continue or stop.

    This is a pure function (no LLM call). It evaluates two hard budget
    constraints and returns a routing decision for the conditional edge.

    Checks performed:
    1. **Iteration budget**: ``current_iteration >= budget_max_iterations``
    2. **Time budget**: elapsed time >= ``budget_time_limit_seconds``

    Returns:
        ``"continue"`` to loop back to hypothesis generation, or
        ``"stop"`` to end the campaign.
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
