"""Plan writer node — generates a structured ML execution plan.

Uses the rewritten query, search results, and data context to produce
both a structured ExecutionPlan and a human-readable markdown version.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage

from scientist_bin_backend.agents.plan.prompts import PLAN_WRITER_PROMPT
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


def _build_data_context(state: PlanState) -> str:
    """Build a data context string from analyst outputs for the plan writer."""
    parts: list[str] = []

    data_profile = state.get("data_profile")
    if data_profile:
        parts.append("== Actual Data Profile ==")
        parts.append(f"Shape: {data_profile.get('shape', 'unknown')}")
        parts.append(f"Columns: {data_profile.get('column_names', [])}")
        parts.append(f"Numeric columns: {data_profile.get('numeric_columns', [])}")
        parts.append(f"Categorical columns: {data_profile.get('categorical_columns', [])}")
        parts.append(f"Target column: {data_profile.get('target_column', 'unknown')}")
        missing = data_profile.get("missing_counts", {})
        if missing:
            import json

            parts.append(f"Missing values: {json.dumps(missing)}")
        class_dist = data_profile.get("class_distribution")
        if class_dist:
            import json

            parts.append(f"Class distribution: {json.dumps(class_dist)}")
        issues = data_profile.get("data_quality_issues", [])
        if issues:
            parts.append(f"Quality issues: {issues}")

    analysis_report = state.get("analysis_report")
    if analysis_report:
        parts.append("")
        parts.append("== Data Analysis Report (from analyst agent) ==")
        parts.append(analysis_report[:3000])

    problem_type = state.get("problem_type")
    if problem_type:
        parts.append(f"\nConfirmed problem type: {problem_type}")

    return "\n".join(parts) if parts else "No data analysis available."


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

    # Build data context from analyst outputs
    data_context = _build_data_context(state)

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(ExecutionPlan)

    prompt = PLAN_WRITER_PROMPT.format(
        rewritten_query=rewritten_query,
        search_results=search_results,
        data_description=data_description,
        framework_preference=framework_preference,
        data_context=data_context,
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
