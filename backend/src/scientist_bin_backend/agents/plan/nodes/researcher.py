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


async def research(state: PlanState) -> dict:
    """Search the web for best practices relevant to the ML problem.

    Uses the rewritten query to formulate targeted search queries,
    then combines results into a single context string for plan generation.
    """
    rewritten_query = state.get("rewritten_query", "")
    objective = state.get("objective", "")
    data_description = state.get("data_description", "")
    framework_preference = state.get("framework_preference") or "scikit-learn"
    experiment_id = state.get("experiment_id")

    logger.info("Researching best practices for: %s", objective[:80])

    # Build a search query that targets practical ML guidance
    search_query = (
        f"Best practices and recommended approach for: {rewritten_query[:500]}\n\n"
        f"Data context: {data_description[:300]}\n"
        f"Framework: {framework_preference}\n\n"
        f"Focus on: algorithm selection, preprocessing steps, "
        f"evaluation metrics, cross-validation strategy, and common pitfalls."
    )

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
