"""Researcher node — performs web research for ML best practices.

Uses Google Search grounding via the google-genai SDK to find
relevant best practices, algorithm comparisons, and practical
guidance for the specific ML problem.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import search_with_gemini

logger = logging.getLogger(__name__)


def _build_search_query(state: PlanState) -> str:
    """Build a targeted search query from upstream context.

    Uses the objective, validated problem type, real data characteristics,
    and framework preference to formulate a precise search query.
    """
    objective = state.get("objective", "")
    problem_type = state.get("problem_type") or "unknown"
    framework = state.get("framework_preference") or "scikit-learn"
    data_profile = state.get("data_profile") or {}
    task_analysis = state.get("task_analysis") or {}

    # Extract key data characteristics for the search
    shape = data_profile.get("shape", "unknown")
    n_numeric = len(data_profile.get("numeric_columns", []))
    n_categorical = len(data_profile.get("categorical_columns", []))
    target = data_profile.get("target_column", "unknown")
    class_dist = data_profile.get("class_distribution")
    considerations = task_analysis.get("key_considerations", [])

    parts = [
        f"Best practices for {problem_type} using {framework}:",
        f"Objective: {objective[:300]}",
        f"Dataset: {shape} shape, {n_numeric} numeric features, "
        f"{n_categorical} categorical features",
        f"Target: {target}",
    ]

    if class_dist:
        parts.append(f"Class distribution: {class_dist}")

    if considerations:
        parts.append(f"Key considerations: {', '.join(considerations[:5])}")

    parts.append(
        "Focus on: algorithm selection and comparison, "
        "sklearn pipeline preprocessing best practices, "
        "evaluation metrics, cross-validation strategy, "
        "hyperparameter tuning approach, and common pitfalls."
    )

    return "\n".join(parts)


async def research(state: PlanState) -> dict:
    """Search the web for best practices relevant to the ML problem.

    Builds a targeted search query from upstream context (objective,
    problem type, data profile, framework) and uses Google Search
    grounding to find practical ML guidance.
    """
    objective = state.get("objective", "")
    experiment_id = state.get("experiment_id")

    logger.info("Researching best practices for: %s", objective[:80])

    search_query = _build_search_query(state)

    try:
        search_results = await search_with_gemini(search_query)
        logger.info("Research completed, received %d characters", len(search_results))
    except Exception:
        logger.exception("Search failed, proceeding without web research")
        search_results = "Web search unavailable. Proceed using general ML knowledge."

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "agent": "plan",
                    "node": "research",
                    "summary": f"Researched best practices ({len(search_results)} chars)",
                    "search_available": "unavailable" not in search_results,
                },
            ),
        )

    return {
        "search_results": search_results,
        "messages": [
            AIMessage(
                content=f"Research results ({len(search_results)} chars):\n"
                f"{search_results[:500]}..."
            ),
        ],
    }
