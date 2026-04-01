"""StateGraph definition for the summary agent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.summary.nodes.experiment_reviewer import (
    review_experiments,
)
from scientist_bin_backend.agents.summary.nodes.model_selector import select_best
from scientist_bin_backend.agents.summary.nodes.report_generator import (
    generate_report,
)
from scientist_bin_backend.agents.summary.states import SummaryState


def build_summary_graph(checkpointer=None):
    """Build and compile the summary agent graph.

    Flow:
        review_experiments -> select_best -> generate_report -> END

    The graph is a simple linear pipeline:
    1. Review all experiment runs and rank models
    2. Select the best model with reasoning
    3. Generate a comprehensive markdown report
    """
    builder = StateGraph(SummaryState)

    builder.add_node("review_experiments", review_experiments)
    builder.add_node("select_best", select_best)
    builder.add_node("generate_report", generate_report)

    builder.add_edge(START, "review_experiments")
    builder.add_edge("review_experiments", "select_best")
    builder.add_edge("select_best", "generate_report")
    builder.add_edge("generate_report", END)

    return builder.compile(checkpointer=checkpointer)
