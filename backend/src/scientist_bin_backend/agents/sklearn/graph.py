"""StateGraph definition for the scikit-learn subagent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.sklearn.nodes.code_generator import generate_code
from scientist_bin_backend.agents.sklearn.nodes.evaluator import evaluate, should_retry
from scientist_bin_backend.agents.sklearn.nodes.planner import plan
from scientist_bin_backend.agents.sklearn.states import SklearnState


def build_sklearn_graph():
    """Build and compile the sklearn subagent graph.

    Flow: plan → generate_code → evaluate → (retry generate_code | END)
    """
    builder = StateGraph(SklearnState)

    builder.add_node("plan", plan)
    builder.add_node("generate_code", generate_code)
    builder.add_node("evaluate", evaluate)

    builder.add_edge(START, "plan")
    builder.add_edge("plan", "generate_code")
    builder.add_edge("generate_code", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        should_retry,
        {"generate_code": "generate_code", END: END},
    )

    return builder.compile()
