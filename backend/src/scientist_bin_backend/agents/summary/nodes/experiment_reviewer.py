"""Experiment reviewer node — analyzes all runs and ranks models.

Uses one LLM call with structured output to produce a ranked list of
ModelRanking objects sorted by primary validation metric.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.summary.prompts.templates import (
    EXPERIMENT_REVIEW_PROMPT,
)
from scientist_bin_backend.agents.summary.schemas import ModelRankingList
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
        training_time = record.get("training_time", 0)
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


def _format_runs(runs: list[dict]) -> str:
    """Format raw run details into a readable string for the prompt."""
    if not runs:
        return "No raw run details available."

    lines: list[str] = []
    for i, run in enumerate(runs, 1):
        run_str = json.dumps(run, indent=2, default=str)
        lines.append(f"Run {i}:\n{run_str}")

    return "\n\n".join(lines)


async def review_experiments(state: dict) -> dict:
    """Analyze experiment history and rank all models tried.

    Takes experiment_history and runs from state, builds a structured
    comparison of all models, and uses an LLM call to produce ranked
    ModelRanking objects.
    """
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "unknown")
    execution_plan = state.get("execution_plan")
    analysis_report = state.get("analysis_report")
    experiment_history = state.get("experiment_history", [])
    runs = state.get("runs", [])
    experiment_id = state.get("experiment_id")

    # Format inputs for the prompt
    execution_plan_str = (
        json.dumps(execution_plan, indent=2, default=str)
        if execution_plan
        else "No execution plan available."
    )
    analysis_report_str = analysis_report or "No analysis report available."
    history_str = _format_experiment_history(experiment_history)
    runs_str = _format_runs(runs)

    # Build the prompt
    prompt = EXPERIMENT_REVIEW_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        execution_plan=execution_plan_str,
        analysis_report=analysis_report_str,
        experiment_history=history_str,
        runs=runs_str,
    )

    # LLM call with structured output
    llm = get_agent_model("summary")
    structured_llm = llm.with_structured_output(ModelRankingList)
    result: ModelRankingList = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Sort rankings by rank (ascending — rank 1 is best)
    rankings = sorted(result.rankings, key=lambda r: r.rank)

    logger.info(
        "Reviewed %d experiments, produced %d rankings",
        len(experiment_history),
        len(rankings),
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "summary_review",
                    "models_reviewed": len(rankings),
                    "top_model": rankings[0].algorithm if rankings else None,
                },
            ),
        )

    comparison = [ranking.model_dump() for ranking in rankings]
    summary = (
        f"Reviewed {len(rankings)} models. Top model: {rankings[0].algorithm} (rank 1)"
        if rankings
        else "No models to rank."
    )

    return {
        "model_comparison": comparison,
        "messages": [HumanMessage(content=f"Experiment review complete: {summary}")],
    }
