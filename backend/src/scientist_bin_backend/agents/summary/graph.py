"""StateGraph definition for the summary agent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.summary.nodes.artifact_saver import save_artifacts
from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context
from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
    compute_diagnostics,
)
from scientist_bin_backend.agents.summary.nodes.report_generator import generate_report
from scientist_bin_backend.agents.summary.nodes.reviewer import review_and_rank
from scientist_bin_backend.agents.summary.states import SummaryState


def build_summary_graph(checkpointer=None):
    """Build and compile the summary agent graph.

    Flow:
        collect_context → compute_diagnostics → review_and_rank
        → generate_report → save_artifacts → END

    The graph is a 5-node pipeline (2 LLM calls):
    1. Collect and normalize all upstream data (0 LLM)
    2. Compute diagnostics: CV stability, overfitting, sensitivity, Pareto (0 LLM)
    3. Rank models and select best with reasoning (1 LLM)
    4. Generate comprehensive markdown report (1 LLM)
    5. Save report and chart data to disk (0 LLM)
    """
    builder = StateGraph(SummaryState)

    builder.add_node("collect_context", collect_context)
    builder.add_node("compute_diagnostics", compute_diagnostics)
    builder.add_node("review_and_rank", review_and_rank)
    builder.add_node("generate_report", generate_report)
    builder.add_node("save_artifacts", save_artifacts)

    builder.add_edge(START, "collect_context")
    builder.add_edge("collect_context", "compute_diagnostics")
    builder.add_edge("compute_diagnostics", "review_and_rank")
    builder.add_edge("review_and_rank", "generate_report")
    builder.add_edge("generate_report", "save_artifacts")
    builder.add_edge("save_artifacts", END)

    return builder.compile(checkpointer=checkpointer)
