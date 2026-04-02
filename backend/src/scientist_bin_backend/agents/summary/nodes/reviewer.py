"""Reviewer node — ranks all models and selects the best in one LLM call.

Replaces the former two-node pattern (experiment_reviewer + model_selector)
with a single structured LLM call that produces both rankings and selection
reasoning. Uses pre-computed diagnostics for informed judgment.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.summary.prompts import REVIEW_AND_RANK_PROMPT
from scientist_bin_backend.agents.summary.schemas import ReviewAndRankResult
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


def _format_experiment_history(experiment_history: list[dict]) -> str:
    """Format experiment history into a readable string for the prompt."""
    if not experiment_history:
        return "No experiment history available."

    lines: list[str] = []
    for i, record in enumerate(experiment_history, 1):
        algo = record.get("algorithm", record.get("best_model", "Unknown"))
        metrics = record.get("metrics", {})
        params = record.get("best_params", record.get("hyperparameters", {}))
        training_time = record.get("training_time_seconds", record.get("training_time", 0))
        error = record.get("error")

        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items()) if metrics else "N/A"
        params_str = json.dumps(params, default=str) if params else "{}"

        entry = (
            f"Run {i}:\n"
            f"  Algorithm: {algo}\n"
            f"  Metrics: {metrics_str}\n"
            f"  Hyperparameters: {params_str}\n"
            f"  Training time: {training_time}s"
        )
        if error:
            entry += f"\n  Error: {error}"
        lines.append(entry)

    return "\n\n".join(lines)


def _format_diagnostics_summary(diagnostics: dict | None) -> str:
    """Format pre-computed diagnostics into a readable summary for the prompt."""
    if not diagnostics:
        return "No diagnostics available."

    parts: list[str] = []

    # CV stability
    cv_stability = diagnostics.get("cv_stability", [])
    if cv_stability:
        parts.append("CV Stability:")
        for entry in cv_stability:
            parts.append(
                f"  {entry['algorithm']} ({entry['metric_name']}): "
                f"mean={entry['mean']:.4f}, std={entry['std']:.4f}, "
                f"CV={entry['cv_coefficient_of_variation']:.4f}, "
                f"range=[{entry['min_fold']:.4f}, {entry['max_fold']:.4f}]"
            )

    # Overfitting analysis
    overfit = diagnostics.get("overfit_analyses", [])
    if overfit:
        parts.append("\nOverfitting Analysis:")
        for entry in overfit:
            parts.append(
                f"  {entry['algorithm']} ({entry['metric_name']}): "
                f"train={entry['train_value']:.4f}, val={entry['val_value']:.4f}, "
                f"gap={entry['gap']:.4f} ({entry['gap_percentage']:.1f}%), "
                f"risk={entry['overfit_risk']}"
            )

    # Pareto frontier
    pareto = diagnostics.get("pareto_optimal_models", [])
    if pareto:
        parts.append(f"\nPareto-optimal (performance vs speed): {', '.join(pareto)}")

    # Hyperparameter sensitivity (top 5)
    sensitivities = diagnostics.get("hyperparam_sensitivities", [])
    if sensitivities:
        parts.append("\nTop Hyperparameter Sensitivities:")
        for entry in sensitivities[:5]:
            parts.append(
                f"  {entry['algorithm']}.{entry['param_name']}: "
                f"score_range={entry['score_range']:.4f}, "
                f"best={entry['best_value']}, tried={entry['values_tried']} values"
            )

    return "\n".join(parts) if parts else "No diagnostics available."


async def review_and_rank(state: dict) -> dict:
    """Rank all models and select the best in a single LLM call.

    Uses pre-computed diagnostics to ground the ranking in concrete data.
    Produces a ReviewAndRankResult with both rankings and selection reasoning.
    """
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "unknown")
    execution_plan = state.get("execution_plan")
    analysis_report = state.get("analysis_report")
    experiment_history = state.get("experiment_history", [])
    diagnostics = state.get("diagnostics")
    test_metrics = state.get("test_metrics")
    experiment_id = state.get("experiment_id")

    if not experiment_history:
        logger.warning("No experiment history available for review")
        return {
            "model_rankings": [],
            "best_model": None,
            "best_hyperparameters": None,
            "best_metrics": None,
            "selection_reasoning": None,
            "error": "No experiments to review.",
            "messages": [HumanMessage(content="No experiments to review.")],
        }

    # Format inputs for the prompt
    execution_plan_str = (
        json.dumps(execution_plan, indent=2, default=str)
        if execution_plan
        else "No execution plan available."
    )
    analysis_report_str = analysis_report or "No analysis report available."
    history_str = _format_experiment_history(experiment_history)
    diagnostics_str = _format_diagnostics_summary(diagnostics)
    test_metrics_str = (
        json.dumps(test_metrics, indent=2, default=str)
        if test_metrics
        else "No test set evaluation performed."
    )

    prompt = REVIEW_AND_RANK_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        execution_plan=execution_plan_str,
        analysis_report=analysis_report_str,
        experiment_history=history_str,
        diagnostics_summary=diagnostics_str,
        test_metrics=test_metrics_str,
    )

    llm = get_agent_model("summary")
    structured_llm = llm.with_structured_output(ReviewAndRankResult)
    result: ReviewAndRankResult = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Sort rankings by rank (ascending — rank 1 is best)
    rankings = sorted(result.rankings, key=lambda r: r.rank)
    rankings_dicts = [r.model_dump() for r in rankings]

    # Build best_metrics from the top-ranked model
    best_metrics: dict = {}
    if rankings:
        top = rankings[0]
        best_metrics = {**top.val_metrics}
        if top.test_metrics:
            best_metrics.update({f"test_{k}": v for k, v in top.test_metrics.items()})
        best_metrics[result.primary_metric_name] = result.primary_metric_value

    logger.info(
        "Review complete: %d models ranked. Best: %s (%s=%.4f)",
        len(rankings),
        result.best_algorithm,
        result.primary_metric_name,
        result.primary_metric_value,
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "summary_review",
                    "models_reviewed": len(rankings),
                    "best_model": result.best_algorithm,
                    "primary_metric": result.primary_metric_name,
                    "primary_metric_value": result.primary_metric_value,
                },
            ),
        )

    summary_msg = (
        f"Reviewed {len(rankings)} models. "
        f"Best: {result.best_algorithm} "
        f"({result.primary_metric_name}={result.primary_metric_value:.4f}). "
        f"Reasoning: {result.selection_reasoning}"
    )

    return {
        "model_rankings": rankings_dicts,
        "best_model": result.best_algorithm,
        "best_hyperparameters": result.best_hyperparameters,
        "best_metrics": best_metrics,
        "selection_reasoning": result.selection_reasoning,
        "messages": [HumanMessage(content=summary_msg)],
    }
