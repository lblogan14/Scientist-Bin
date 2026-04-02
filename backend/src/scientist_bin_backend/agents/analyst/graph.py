"""StateGraph definition for the analyst agent.

Flow: START -> profile_data -> clean_data -> split_data -> write_report -> END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.analyst.nodes.data_cleaner import clean_data
from scientist_bin_backend.agents.analyst.nodes.data_profiler import profile_data
from scientist_bin_backend.agents.analyst.nodes.data_splitter import split_data
from scientist_bin_backend.agents.analyst.nodes.report_writer import write_report
from scientist_bin_backend.agents.analyst.states import AnalystState


def build_analyst_graph(checkpointer=None):
    """Build and compile the analyst agent graph.

    Linear pipeline:
        profile_data -> clean_data -> split_data -> write_report
    """
    graph = StateGraph(AnalystState)

    # Add nodes
    graph.add_node("profile_data", profile_data)
    graph.add_node("clean_data", clean_data)
    graph.add_node("split_data", split_data)
    graph.add_node("write_report", write_report)

    # Add edges
    graph.add_edge(START, "profile_data")
    graph.add_edge("profile_data", "clean_data")
    graph.add_edge("clean_data", "split_data")
    graph.add_edge("split_data", "write_report")
    graph.add_edge("write_report", END)

    return graph.compile(checkpointer=checkpointer)
