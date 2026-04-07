"""Plan writer node — generates a structured ML execution plan.

Uses the objective, search results, and upstream context to produce
both a structured ExecutionPlan and a human-readable markdown version.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage

from scientist_bin_backend.agents.plan.nodes._context import build_upstream_context
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
    lines.append(f"- **Cross-validation:** {plan.cv_strategy}")
    lines.append("")

    lines.append("## Algorithms")
    for i, algo in enumerate(plan.algorithms_to_try, 1):
        lines.append(f"{i}. {algo}")
    lines.append("")

    if plan.pipeline_preprocessing_steps:
        lines.append("## Pipeline Preprocessing")
        for i, step in enumerate(plan.pipeline_preprocessing_steps, 1):
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

    lines.append("## Hyperparameter Tuning")
    lines.append(plan.hyperparameter_tuning_approach)
    lines.append("")

    return "\n".join(lines)


async def write_plan(state: PlanState) -> dict:
    """Generate a structured execution plan from research and context.

    Produces both a structured ``ExecutionPlan`` (for machine consumption)
    and a markdown rendering (for human review via HITL).
    """
    objective = state.get("objective", "")
    search_results = state.get("search_results", "")
    data_description = state.get("data_description", "")
    framework_preference = state.get("framework_preference") or "scikit-learn"
    experiment_id = state.get("experiment_id")

    logger.info("Writing execution plan")

    upstream_context = build_upstream_context(state)

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(ExecutionPlan)

    prompt = PLAN_WRITER_PROMPT.format(
        objective=objective,
        search_results=search_results,
        data_description=data_description,
        framework_preference=framework_preference,
        upstream_context=upstream_context,
    )

    # Retry up to 3 times — Gemini occasionally returns empty/malformed JSON
    last_error = None
    plan: ExecutionPlan | None = None
    for attempt in range(3):
        try:
            plan = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            break
        except Exception as exc:
            last_error = exc
            logger.warning("Plan generation attempt %d failed: %s", attempt + 1, exc)
    if plan is None:
        raise last_error  # type: ignore[misc]

    plan_dict = plan.model_dump()
    plan_markdown = _plan_to_markdown(plan)

    logger.info(
        "Plan generated: %s (%d algorithms, %d preprocessing steps)",
        plan.problem_type,
        len(plan.algorithms_to_try),
        len(plan.pipeline_preprocessing_steps),
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
