"""Query rewriter node — enriches the user objective with ML-specific details.

Uses structured output to produce a clear, detailed problem statement
from the user's raw objective and data description.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import AIMessage, HumanMessage

from scientist_bin_backend.agents.plan.prompts import QUERY_REWRITER_PROMPT
from scientist_bin_backend.agents.plan.schemas import RewrittenQuery
from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


def _build_analysis_context(state: PlanState) -> str:
    """Build a context string from upstream task_analysis and analyst data."""
    parts: list[str] = []

    # Task analysis from central agent
    task_analysis = state.get("task_analysis")
    if task_analysis:
        parts.append("== Pre-Analysis (from upstream) ==")
        parts.append(f"Task type: {task_analysis.get('task_type', 'unknown')}")
        subtype = task_analysis.get("task_subtype")
        if subtype:
            parts.append(f"Subtype: {subtype}")
        parts.append(f"Complexity: {task_analysis.get('complexity_estimate', 'unknown')}")
        considerations = task_analysis.get("key_considerations", [])
        if considerations:
            parts.append(f"Key considerations: {', '.join(considerations)}")
        approach = task_analysis.get("recommended_approach")
        if approach:
            parts.append(f"Recommended approach: {approach}")
        chars = task_analysis.get("data_characteristics", {})
        if chars:
            parts.append(f"Estimated features: {chars.get('estimated_features', 'unknown')}")
            parts.append(f"Estimated samples: {chars.get('estimated_samples', 'unknown')}")

    # Data profile from analyst agent (real data characteristics)
    data_profile = state.get("data_profile")
    if data_profile:
        parts.append("")
        parts.append("== Actual Data Profile (from analyst) ==")
        parts.append(f"Shape: {data_profile.get('shape', 'unknown')}")
        parts.append(f"Columns: {data_profile.get('column_names', [])}")
        parts.append(f"Numeric columns: {data_profile.get('numeric_columns', [])}")
        parts.append(f"Categorical columns: {data_profile.get('categorical_columns', [])}")
        parts.append(f"Target column: {data_profile.get('target_column', 'unknown')}")
        missing = data_profile.get("missing_counts", {})
        if missing:
            parts.append(f"Missing values: {json.dumps(missing)}")
        class_dist = data_profile.get("class_distribution")
        if class_dist:
            parts.append(f"Class distribution: {json.dumps(class_dist)}")

    # Problem type from analyst
    problem_type = state.get("problem_type")
    if problem_type:
        parts.append(f"Confirmed problem type: {problem_type}")

    return "\n".join(parts) if parts else ""


async def rewrite_query(state: PlanState) -> dict:
    """Enrich the user's objective into a precise ML problem statement.

    Takes the raw objective, data description, and framework preference,
    then produces a structured rewrite with enhanced objective, key
    requirements, and constraints. Uses upstream context from the central
    analyzer and analyst agent when available.
    """
    objective = state["objective"]
    data_description = state.get("data_description", "")
    framework_preference = state.get("framework_preference") or "no preference"
    experiment_id = state.get("experiment_id")

    logger.info("Rewriting query for objective: %s", objective[:80])

    # Build context from upstream agents
    analysis_context = _build_analysis_context(state)

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(RewrittenQuery)

    prompt = QUERY_REWRITER_PROMPT.format(
        objective=objective,
        data_description=data_description,
        framework_preference=framework_preference,
        analysis_context=analysis_context,
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
