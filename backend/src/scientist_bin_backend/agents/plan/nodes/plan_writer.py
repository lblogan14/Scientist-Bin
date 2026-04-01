"""Plan writer node — generates a structured ML execution plan.

Uses the rewritten query, search results, and data context to produce
both a structured ExecutionPlan and a human-readable markdown version.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage

from scientist_bin_backend.agents.plan.prompts.templates import PLAN_WRITER_PROMPT
from scientist_bin_backend.agents.plan.schemas import ExecutionPlan
from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


def _plan_to_markdown(plan: ExecutionPlan) -> str:
    """Convert a structured ExecutionPlan to human-readable markdown."""
    lines: list[str] = []

    lines.append("# Execution Plan")
    lines.append("")
    lines.append("## Summary")
    lines.append(plan.approach_summary)
    lines.append("")

    lines.append("## Problem Details")
    lines.append(f"- **Problem type:** {plan.problem_type}")
    if plan.target_column:
        lines.append(f"- **Target column:** {plan.target_column}")
    lines.append(f"- **Data split:** {plan.data_split_strategy}")
    lines.append(f"- **Cross-validation:** {plan.cv_strategy}")
    lines.append("")

    lines.append("## Algorithms")
    for i, algo in enumerate(plan.algorithms_to_try, 1):
        lines.append(f"{i}. {algo}")
    lines.append("")

    if plan.preprocessing_steps:
        lines.append("## Preprocessing Steps")
        for i, step in enumerate(plan.preprocessing_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    if plan.feature_engineering_steps:
        lines.append("## Feature Engineering")
        for i, step in enumerate(plan.feature_engineering_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    lines.append("## Evaluation Metrics")
    for metric in plan.evaluation_metrics:
        lines.append(f"- {metric}")
    lines.append("")

    if plan.success_criteria:
        lines.append("## Success Criteria")
        for metric, threshold in plan.success_criteria.items():
            lines.append(f"- **{metric}** >= {threshold}")
        lines.append("")

    return "\n".join(lines)


async def write_plan(state: PlanState) -> dict:
    """Generate a structured execution plan from research and context.

    Produces both a structured ``ExecutionPlan`` (for machine consumption)
    and a markdown rendering (for human review via HITL).
    """
    rewritten_query = state.get("rewritten_query", "")
    search_results = state.get("search_results", "")
    data_description = state.get("data_description", "")
    framework_preference = state.get("framework_preference") or "no preference"
    experiment_id = state.get("experiment_id")

    logger.info("Writing execution plan")

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(ExecutionPlan)

    prompt = PLAN_WRITER_PROMPT.format(
        rewritten_query=rewritten_query,
        search_results=search_results,
        data_description=data_description,
        framework_preference=framework_preference,
    )

    plan: ExecutionPlan = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    plan_dict = plan.model_dump()
    plan_markdown = _plan_to_markdown(plan)

    logger.info(
        "Plan generated: %s (%d algorithms, %d preprocessing steps)",
        plan.problem_type,
        len(plan.algorithms_to_try),
        len(plan.preprocessing_steps),
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "agent": "plan",
                    "node": "write_plan",
                    "problem_type": plan.problem_type,
                    "algorithms": plan.algorithms_to_try,
                    "metrics": plan.evaluation_metrics,
                },
            ),
        )

    return {
        "execution_plan": plan_dict,
        "plan_markdown": plan_markdown,
        "messages": [
            AIMessage(content=f"Execution plan generated:\n{plan_markdown}"),
        ],
    }
