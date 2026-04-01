"""Plan reviewer nodes — human-in-the-loop plan approval and revision.

Uses ``langgraph.types.interrupt()`` to pause the graph and present the
plan to a human reviewer. The reviewer can approve the plan or provide
feedback for revision.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt

from scientist_bin_backend.agents.plan.prompts import PLAN_REVISER_PROMPT
from scientist_bin_backend.agents.plan.schemas import ExecutionPlan
from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)

# Responses that count as approval
_APPROVAL_TOKENS = frozenset({"approve", "approved", "yes", "ok", "lgtm", "looks good"})


async def review_plan(state: PlanState) -> dict:
    """Pause the graph for human review of the execution plan.

    If ``plan_approved`` is already ``True`` (e.g. auto-approve mode),
    this node is a no-op and the graph continues immediately.

    Otherwise, calls ``interrupt()`` to present the plan markdown to the
    caller. When the graph is resumed with feedback, the node returns
    either an approval or the feedback text for revision.
    """
    # Short-circuit when auto-approve is set
    if state.get("plan_approved"):
        logger.info("Plan auto-approved, skipping human review")
        return {"plan_approved": True}

    plan_md = state.get("plan_markdown", "")
    experiment_id = state.get("experiment_id")

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="plan_review_pending",
                data={
                    "plan_markdown": plan_md,
                    "revision_count": state.get("revision_count", 0),
                },
            ),
        )

    # Pause execution and wait for human input
    feedback = interrupt(
        {
            "type": "plan_review",
            "plan": plan_md,
            "message": (
                "Please review the execution plan. "
                "Reply 'approve' to proceed, or provide feedback for revision."
            ),
        }
    )

    # Determine if the response is an approval or feedback
    is_approved = isinstance(feedback, str) and feedback.lower().strip() in _APPROVAL_TOKENS

    if is_approved:
        logger.info("Plan approved by reviewer")
        if experiment_id:
            await event_bus.emit(
                experiment_id,
                ExperimentEvent(
                    event_type="plan_review_submitted",
                    data={"approved": True},
                ),
            )
        return {
            "plan_approved": True,
            "human_feedback": None,
        }

    # Feedback provided — route to revision
    feedback_str = feedback if isinstance(feedback, str) else str(feedback)
    revision_count = state.get("revision_count", 0) + 1
    logger.info("Plan revision requested (revision %d): %s", revision_count, feedback_str[:100])

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="plan_review_submitted",
                data={
                    "approved": False,
                    "feedback": feedback_str[:200],
                    "revision_count": revision_count,
                },
            ),
        )

    return {
        "plan_approved": False,
        "human_feedback": feedback_str,
        "revision_count": revision_count,
    }


async def revise_plan(state: PlanState) -> dict:
    """Revise the execution plan based on human feedback.

    Uses the LLM to rewrite the plan, addressing the reviewer's
    concerns while preserving the parts that were not criticised.
    """
    plan_markdown = state.get("plan_markdown", "")
    human_feedback = state.get("human_feedback", "")
    rewritten_query = state.get("rewritten_query", "")
    data_description = state.get("data_description", "")
    experiment_id = state.get("experiment_id")

    logger.info("Revising plan based on feedback: %s", human_feedback[:100])

    llm = get_agent_model("plan")
    structured_llm = llm.with_structured_output(ExecutionPlan)

    prompt = PLAN_REVISER_PROMPT.format(
        plan_markdown=plan_markdown,
        human_feedback=human_feedback,
        rewritten_query=rewritten_query,
        data_description=data_description,
    )

    revised_plan: ExecutionPlan = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Re-generate markdown from revised structured plan
    from scientist_bin_backend.agents.plan.nodes.plan_writer import _plan_to_markdown

    revised_dict = revised_plan.model_dump()
    revised_markdown = _plan_to_markdown(revised_plan)

    logger.info(
        "Plan revised: %s (%d algorithms)",
        revised_plan.problem_type,
        len(revised_plan.algorithms_to_try),
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "agent": "plan",
                    "node": "revise_plan",
                    "problem_type": revised_plan.problem_type,
                    "algorithms": revised_plan.algorithms_to_try,
                    "revision_count": state.get("revision_count", 0),
                },
            ),
        )

    return {
        "execution_plan": revised_dict,
        "plan_markdown": revised_markdown,
        "human_feedback": None,
        "messages": [
            AIMessage(content=f"Plan revised:\n{revised_markdown}"),
        ],
    }


def check_approval(state: PlanState) -> str:
    """Routing function: decide whether to approve or revise the plan.

    Returns ``"approved"`` if the plan is approved or the maximum number
    of revisions has been reached. Returns ``"revise"`` otherwise.
    """
    if state.get("plan_approved"):
        return "approved"

    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)

    if revision_count >= max_revisions:
        logger.warning(
            "Maximum revisions (%d) reached, auto-approving plan",
            max_revisions,
        )
        return "approved"

    return "revise"
