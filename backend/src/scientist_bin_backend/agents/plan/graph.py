"""StateGraph definition for the plan agent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.plan.nodes.plan_reviewer import (
    check_approval,
    review_plan,
    revise_plan,
)
from scientist_bin_backend.agents.plan.nodes.plan_writer import write_plan
from scientist_bin_backend.agents.plan.nodes.query_rewriter import rewrite_query
from scientist_bin_backend.agents.plan.nodes.researcher import research
from scientist_bin_backend.agents.plan.states import PlanState


def build_plan_graph(checkpointer=None):
    """Build and compile the plan agent graph.

    Flow::

        START -> rewrite_query -> research -> write_plan -> review_plan
            review_plan --(approved)--> END
            review_plan --(revise)----> revise_plan -> review_plan
    """
    builder = StateGraph(PlanState)

    # Register nodes
    builder.add_node("rewrite_query", rewrite_query)
    builder.add_node("research", research)
    builder.add_node("write_plan", write_plan)
    builder.add_node("review_plan", review_plan)
    builder.add_node("revise_plan", revise_plan)

    # Linear flow: rewrite -> research -> write
    builder.add_edge(START, "rewrite_query")
    builder.add_edge("rewrite_query", "research")
    builder.add_edge("research", "write_plan")
    builder.add_edge("write_plan", "review_plan")

    # Conditional: approve or revise
    builder.add_conditional_edges(
        "review_plan",
        check_approval,
        {
            "approved": END,
            "revise": "revise_plan",
        },
    )

    # After revision, loop back to review
    builder.add_edge("revise_plan", "review_plan")

    return builder.compile(checkpointer=checkpointer)
