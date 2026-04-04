"""Experiment runner node — picks the top hypothesis and invokes the inner pipeline.

Delegates to the existing 5-agent pipeline (central -> analyst -> plan ->
sklearn -> summary) with the hypothesis translated into a concrete training
objective.
"""

from __future__ import annotations

import logging
import time

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


def _primary_metric_value(metrics: dict) -> float:
    """Return a single representative score from a metrics dict.

    Prefers common validation metrics in order of priority.
    Falls back to the first numeric value found.
    """
    preferred = [
        "val_accuracy",
        "val_f1_weighted",
        "val_f1",
        "val_r2",
        "test_accuracy",
        "test_f1_weighted",
        "test_r2",
        "val_silhouette",
        "silhouette_score",
    ]
    for key in preferred:
        if key in metrics and isinstance(metrics[key], (int, float)):
            return float(metrics[key])
    # Fallback: first numeric value
    for v in metrics.values():
        if isinstance(v, (int, float)):
            return float(v)
    return 0.0


async def run_next_experiment(state: dict) -> dict:
    """Pick the top hypothesis and run an experiment via the inner pipeline.

    Creates a fresh ``CentralAgent`` for each experiment and calls
    ``agent.run()`` with the hypothesis baked into the objective. Failures
    are caught and recorded so the campaign continues.

    Returns:
        Partial state update with the latest experiment appended to
        ``completed_experiments``, ``current_iteration`` incremented,
        and ``best_result`` updated if the new result is better.
    """
    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import TrainRequest
    from scientist_bin_backend.utils.naming import generate_experiment_id

    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        logger.warning("No hypotheses available to run — skipping experiment")
        return {
            "messages": [
                HumanMessage(content="No hypotheses to test. Skipping.")
            ],
        }

    hypothesis = hypotheses[0]  # Pick the top-ranked hypothesis
    iteration = state.get("current_iteration", 0)
    description = hypothesis.get("description", "")
    algorithm_suggestions = hypothesis.get("algorithm_suggestions", [])

    logger.info(
        "Iteration %d: testing hypothesis — %s",
        iteration,
        description or "unknown",
    )

    # Build objective that includes the hypothesis context
    objective = f"{state['objective']} — Hypothesis: {description}"
    sub_experiment_id = generate_experiment_id(objective)

    request = TrainRequest(
        objective=objective,
        data_description=state.get("data_description", ""),
        data_file_path=state.get("data_file_path"),
        auto_approve_plan=True,  # Campaigns run autonomously
    )

    result_dict: dict
    try:
        agent = CentralAgent()
        response = await agent.run(
            request, experiment_id=sub_experiment_id
        )

        # Extract metrics from the AgentResponse
        eval_results = response.evaluation_results or {}
        test_metrics = response.test_metrics or {}
        metrics = {**eval_results, **test_metrics}

        result_dict = {
            "iteration": iteration,
            "hypothesis": description,
            "algorithm": response.best_model or (
                algorithm_suggestions[0]
                if algorithm_suggestions
                else "unknown"
            ),
            "metrics": metrics,
            "best_model": response.best_model,
            "best_hyperparameters": response.best_hyperparameters,
            "status": response.status,
            "experiment_id": sub_experiment_id,
            "iterations": response.iterations,
            "timestamp": time.time(),
        }

        logger.info(
            "Iteration %d completed: %s — %s (metrics: %s)",
            iteration,
            result_dict["algorithm"],
            result_dict["status"],
            metrics,
        )

    except Exception as exc:
        logger.error(
            "Iteration %d FAILED: %s — %s",
            iteration,
            description,
            exc,
            exc_info=True,
        )
        result_dict = {
            "iteration": iteration,
            "hypothesis": description,
            "algorithm": (
                algorithm_suggestions[0]
                if algorithm_suggestions
                else "unknown"
            ),
            "metrics": {},
            "status": "failed",
            "error": str(exc),
            "experiment_id": sub_experiment_id,
            "timestamp": time.time(),
        }

    # Accumulate results
    completed = list(state.get("completed_experiments", []))
    completed.append(result_dict)

    # Update best result — compare primary metric values
    best = state.get("best_result", {})
    new_score = _primary_metric_value(result_dict.get("metrics", {}))
    best_score = _primary_metric_value(best.get("metrics", {}))
    if (
        not best
        or result_dict.get("status") != "failed"
        and new_score > best_score
    ):
        best = result_dict

    return {
        "completed_experiments": completed,
        "current_iteration": iteration + 1,
        "best_result": best,
        "messages": [
            HumanMessage(
                content=(
                    f"Iteration {iteration}: tested "
                    f"'{description}' using "
                    f"{result_dict['algorithm']} — "
                    f"status: {result_dict['status']}"
                )
            )
        ],
    }
