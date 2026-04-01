"""Error research node — searches the web to help resolve execution errors.

When the sklearn agent encounters an error during code execution, this node
uses Google Search grounding to look up solutions before the next code
generation attempt.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import AGENT_MODELS, search_with_gemini


async def error_research(state: dict) -> dict:
    """Search the web for solutions to the execution error."""
    execution_error = state.get("execution_error", "")
    refinement_context = state.get("refinement_context", "")
    experiment_id = state.get("experiment_id")

    # Build a focused search query from the error
    error_snippet = execution_error[:500] if execution_error else refinement_context[:500]
    query = (
        f"python scikit-learn error fix: {error_snippet}\n"
        "How to fix this error in a sklearn training script?"
    )

    search_results = ""
    try:
        search_results = await search_with_gemini(query, model=AGENT_MODELS["sklearn"])
    except Exception as exc:
        search_results = f"Search failed: {exc}"

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "action": "error_research",
                    "iteration": state.get("current_iteration", 0),
                    "query_snippet": error_snippet[:100],
                },
            ),
        )

    return {
        "search_results": search_results,
        "messages": [HumanMessage(content="Searched web for error resolution.")],
    }
