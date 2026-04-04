"""Experiment runner node — picks the top hypothesis and invokes the inner pipeline.

This is currently a STUB. The full implementation will delegate to the existing
5-agent pipeline (central -> analyst -> plan -> sklearn -> summary) with the
hypothesis translated into a concrete training objective.
"""

from __future__ import annotations

import logging
import time

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


async def run_next_experiment(state: dict) -> dict:
    """Pick the top hypothesis and run an experiment via the inner pipeline.

    Returns:
        Partial state update with the latest experiment appended to
        ``completed_experiments``, ``current_iteration`` incremented,
        and ``best_result`` updated if the new result is better.

    .. note::
        **STUB IMPLEMENTATION** — returns a mock result. The full integration
        will be completed when the campaign agent is wired into the main system.
    """
    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        logger.warning("No hypotheses available to run — skipping experiment")
        return {
            "messages": [HumanMessage(content="No hypotheses to test. Skipping.")],
        }

    hypothesis = hypotheses[0]  # Pick the top-ranked hypothesis
    iteration = state.get("current_iteration", 0)

    logger.info(
        "Iteration %d: testing hypothesis — %s",
        iteration,
        hypothesis.get("description", "unknown"),
    )

    # TODO: Full integration steps:
    # 1. Build a TrainRequest from the hypothesis:
    #    - objective = f"{state['objective']} — {hypothesis['description']}"
    #    - data_file_path = state["data_file_path"]
    #    - framework_preference = infer from hypothesis["algorithm_suggestions"]
    #    - auto_approve_plan = True (campaigns run autonomously)
    # 2. Instantiate CentralAgent and call agent.run(request)
    # 3. Extract results from the AgentResponse:
    #    - experiment_id, best_model, best_hyperparameters, evaluation_results,
    #      test_metrics, iterations, status
    # 4. Handle errors gracefully — a failed experiment should not crash the
    #    campaign; log it and move on to the next hypothesis.
    # 5. Emit campaign-level events via the event bus for real-time monitoring.

    mock_result = {
        "iteration": iteration,
        "hypothesis": hypothesis.get("description", ""),
        "algorithm": (
            hypothesis.get("algorithm_suggestions", ["unknown"])[0]
            if hypothesis.get("algorithm_suggestions")
            else "unknown"
        ),
        "metrics": {"val_accuracy": 0.0, "val_f1_weighted": 0.0},
        "status": "stub",
        "notes": "Stub result — pipeline integration pending",
        "experiment_id": None,
        "timestamp": time.time(),
    }

    # Accumulate results
    completed = list(state.get("completed_experiments", []))
    completed.append(mock_result)

    # Update best result (stub: no real comparison logic yet)
    best = state.get("best_result", {})
    if not best:
        best = mock_result

    return {
        "completed_experiments": completed,
        "current_iteration": iteration + 1,
        "best_result": best,
        "messages": [
            HumanMessage(
                content=(
                    f"Iteration {iteration}: tested '{hypothesis.get('description', '')}' "
                    f"using {mock_result['algorithm']} — status: {mock_result['status']}"
                )
            )
        ],
    }
