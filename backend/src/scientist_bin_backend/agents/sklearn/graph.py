"""StateGraph definition for the scikit-learn subagent.

The sklearn agent receives a pre-built execution plan and split data from the
plan and analyst agents.  Its graph focuses on the generate → execute → analyze
iteration loop with an error-research side-path.

Flow:
    generate_code → execute_code → analyze_results
        → (refine_params | try_new_algo | feature_engineer) → generate_code  (loop)
        → fix_error → error_research → generate_code  (error path)
        → (accept | abort) → finalize → END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.base.nodes.code_executor import execute_code
from scientist_bin_backend.agents.base.nodes.results_analyzer import (
    analyze_results,
    finalize,
)
from scientist_bin_backend.agents.sklearn.nodes.code_generator import generate_code
from scientist_bin_backend.agents.sklearn.nodes.error_researcher import error_research
from scientist_bin_backend.agents.sklearn.states import SklearnState


def _route_decision(state: dict) -> str:
    """Route based on the analyze_results decision.

    - accept / abort → finalize
    - fix_error → error_research (web search before regenerating)
    - refine_params / try_new_algo / feature_engineer → generate_code
    """
    next_action = state.get("next_action", "abort")
    if next_action in ("accept", "abort"):
        return "finalize"
    if next_action == "fix_error":
        return "error_research"
    return "generate_code"


def build_sklearn_graph(checkpointer=None):
    """Build and compile the sklearn subagent graph."""
    builder = StateGraph(SklearnState)

    builder.add_node("generate_code", generate_code)
    builder.add_node("execute_code", execute_code)
    builder.add_node("analyze_results", analyze_results)
    builder.add_node("error_research", error_research)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "generate_code")
    builder.add_edge("generate_code", "execute_code")
    builder.add_edge("execute_code", "analyze_results")
    builder.add_conditional_edges(
        "analyze_results",
        _route_decision,
        {
            "generate_code": "generate_code",
            "error_research": "error_research",
            "finalize": "finalize",
        },
    )
    builder.add_edge("error_research", "generate_code")
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
