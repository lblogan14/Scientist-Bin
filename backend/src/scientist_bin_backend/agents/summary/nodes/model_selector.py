"""Model selector node — picks the best model from ranked comparisons.

Deterministically finds the highest-ranked model, then uses one LLM call
with structured output to provide human-readable reasoning.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.summary.prompts.templates import (
    MODEL_SELECTION_PROMPT,
)
from scientist_bin_backend.agents.summary.schemas import BestModelSelection
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


async def select_best(state: dict) -> dict:
    """Select the best model from the ranked model comparison.

    Deterministically identifies the highest-ranked model, then makes a
    single LLM call to produce a structured BestModelSelection with reasoning.
    """
    model_comparison = state.get("model_comparison", [])
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "unknown")
    experiment_id = state.get("experiment_id")

    if not model_comparison:
        logger.warning("No model comparison data available for selection")
        return {
            "best_model": None,
            "best_hyperparameters": None,
            "best_metrics": None,
            "error": "No models available for selection.",
            "messages": [HumanMessage(content="No models available for selection.")],
        }

    # Format model comparison for the prompt
    comparison_str = json.dumps(model_comparison, indent=2, default=str)

    # LLM call with structured output for reasoning
    prompt = MODEL_SELECTION_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        model_comparison=comparison_str,
    )

    llm = get_agent_model("summary")
    structured_llm = llm.with_structured_output(BestModelSelection)
    selection: BestModelSelection = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Build best_metrics from the top-ranked model's validation metrics
    top_ranked = model_comparison[0]  # Already sorted by rank
    best_metrics = {
        **top_ranked.get("val_metrics", {}),
        selection.primary_metric_name: selection.primary_metric_value,
    }
    if top_ranked.get("test_metrics"):
        best_metrics.update({f"test_{k}": v for k, v in top_ranked["test_metrics"].items()})

    logger.info(
        "Selected best model: %s (%s=%.4f)",
        selection.algorithm,
        selection.primary_metric_name,
        selection.primary_metric_value,
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "summary_selection",
                    "best_model": selection.algorithm,
                    "primary_metric": selection.primary_metric_name,
                    "primary_metric_value": selection.primary_metric_value,
                    "reasoning": selection.reasoning,
                },
            ),
        )

    summary = (
        f"Best model: {selection.algorithm} "
        f"({selection.primary_metric_name}={selection.primary_metric_value:.4f}). "
        f"Reasoning: {selection.reasoning}"
    )

    return {
        "best_model": selection.algorithm,
        "best_hyperparameters": selection.hyperparameters,
        "best_metrics": best_metrics,
        "messages": [HumanMessage(content=f"Model selection complete: {summary}")],
    }
