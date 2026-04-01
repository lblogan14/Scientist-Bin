"""Query rewriter node — enriches the user objective with ML-specific details.

Uses structured output to produce a clear, detailed problem statement
from the user's raw objective and data description.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage

from scientist_bin_backend.agents.plan.prompts.templates import QUERY_REWRITER_PROMPT
from scientist_bin_backend.agents.plan.schemas import RewrittenQuery
from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


async def rewrite_query(state: PlanState) -> dict:
    """Enrich the user's objective into a precise ML problem statement.

    Takes the raw objective, data description, and framework preference,
    then produces a structured rewrite with enhanced objective, key
    requirements, and constraints.
    """
    objective = state["objective"]
    data_description = state.get("data_description", "")
    framework_preference = state.get("framework_preference") or "no preference"
    experiment_id = state.get("experiment_id")

    logger.info("Rewriting query for objective: %s", objective[:80])

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(RewrittenQuery)

    prompt = QUERY_REWRITER_PROMPT.format(
        objective=objective,
        data_description=data_description,
        framework_preference=framework_preference,
    )

    result: RewrittenQuery = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Format the rewritten query as a readable string for downstream nodes
    requirements_str = "\n".join(f"  - {r}" for r in result.key_requirements)
    constraints_str = "\n".join(f"  - {c}" for c in result.constraints)
    formatted = (
        f"{result.enhanced_objective}\n\n"
        f"Key requirements:\n{requirements_str}\n\n"
        f"Constraints:\n{constraints_str}"
    )

    logger.info("Query rewritten: %s", result.enhanced_objective[:100])

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "agent": "plan",
                    "node": "rewrite_query",
                    "summary": result.enhanced_objective[:200],
                    "requirements_count": len(result.key_requirements),
                    "constraints_count": len(result.constraints),
                },
            ),
        )

    return {
        "rewritten_query": formatted,
        "messages": [
            AIMessage(content=f"Rewritten query:\n{formatted}"),
        ],
    }
