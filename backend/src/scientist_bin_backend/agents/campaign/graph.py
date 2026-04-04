"""StateGraph definition for the campaign orchestrator agent.

The campaign graph wraps the existing 5-agent pipeline in an iterative loop:

    generate_hypotheses -> run_next_experiment -> extract_insights -> check_budget
                                                                        |
                                                              continue -> generate_hypotheses (loop)
                                                              stop -> END
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.campaign.nodes.budget_checker import check_budget
from scientist_bin_backend.agents.campaign.nodes.experiment_runner import (
    run_next_experiment,
)
from scientist_bin_backend.agents.campaign.nodes.hypothesis_generator import (
    generate_hypotheses,
)
from scientist_bin_backend.agents.campaign.nodes.insight_extractor import (
    extract_insights,
)
from scientist_bin_backend.agents.campaign.states import CampaignState


def build_campaign_graph(checkpointer=None):
    """Build and compile the campaign orchestrator graph.

    Flow:
        generate_hypotheses -> run_next_experiment -> extract_insights
        -> check_budget --(continue)--> generate_hypotheses (loop)
                        --(stop)------> END

    Args:
        checkpointer: LangGraph checkpointer for state persistence and
            resumability. Defaults to an in-memory checkpointer if not provided.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(CampaignState)

    # Add nodes
    builder.add_node("generate_hypotheses", generate_hypotheses)
    builder.add_node("run_next_experiment", run_next_experiment)
    builder.add_node("extract_insights", extract_insights)
    builder.add_node("check_budget", check_budget)

    # Linear edges
    builder.add_edge(START, "generate_hypotheses")
    builder.add_edge("generate_hypotheses", "run_next_experiment")
    builder.add_edge("run_next_experiment", "extract_insights")
    builder.add_edge("extract_insights", "check_budget")

    # Conditional loop-back or exit
    builder.add_conditional_edges(
        "check_budget",
        check_budget,
        {
            "continue": "generate_hypotheses",
            "stop": END,
        },
    )

    return builder.compile(checkpointer=checkpointer)


# Pre-built graph instance with in-memory checkpointer for convenience
campaign_graph = build_campaign_graph()
