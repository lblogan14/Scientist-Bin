"""Reusable graph topology factory for all ML framework subagents.

The graph structure is the same for every framework:
    classify_problem -> analyze_data -> plan_strategy -> generate_code
    -> execute_code -> analyze_results -> (route) -> finalize | generate_code

Framework-specific subagents provide their own plan_strategy and generate_code
functions while reusing the base nodes for everything else.
"""

from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.base.nodes.code_executor import execute_code
from scientist_bin_backend.agents.base.nodes.data_analyzer import (
    analyze_data,
    classify_problem,
)
from scientist_bin_backend.agents.base.nodes.results_analyzer import (
    analyze_results,
    finalize,
    route_decision,
)


def build_ml_graph(
    *,
    plan_strategy_fn: Callable,
    generate_code_fn: Callable,
    state_schema: type,
    classify_problem_fn: Callable | None = None,
    analyze_data_fn: Callable | None = None,
    execute_code_fn: Callable | None = None,
    analyze_results_fn: Callable | None = None,
    finalize_fn: Callable | None = None,
    checkpointer: object | None = None,
):
    """Build and compile the standard ML pipeline graph.

    Args:
        plan_strategy_fn: Framework-specific strategy planning node.
        generate_code_fn: Framework-specific code generation node.
        state_schema: The TypedDict state class for this framework.
        classify_problem_fn: Override for problem classification (default: base).
        analyze_data_fn: Override for data analysis (default: base).
        execute_code_fn: Override for code execution (default: base).
        analyze_results_fn: Override for results analysis (default: base).
        finalize_fn: Override for finalization (default: base).
        checkpointer: Optional LangGraph checkpointer for persistence.

    Returns:
        Compiled LangGraph StateGraph.
    """
    builder = StateGraph(state_schema)

    # Register nodes (use base defaults unless overridden)
    builder.add_node("classify_problem", classify_problem_fn or classify_problem)
    builder.add_node("analyze_data", analyze_data_fn or analyze_data)
    builder.add_node("plan_strategy", plan_strategy_fn)
    builder.add_node("generate_code", generate_code_fn)
    builder.add_node("execute_code", execute_code_fn or execute_code)
    builder.add_node("analyze_results", analyze_results_fn or analyze_results)
    builder.add_node("finalize", finalize_fn or finalize)

    # Linear flow through phases
    builder.add_edge(START, "classify_problem")
    builder.add_edge("classify_problem", "analyze_data")
    builder.add_edge("analyze_data", "plan_strategy")
    builder.add_edge("plan_strategy", "generate_code")
    builder.add_edge("generate_code", "execute_code")
    builder.add_edge("execute_code", "analyze_results")

    # Conditional routing from analyze_results
    builder.add_conditional_edges(
        "analyze_results",
        route_decision,
        {
            "generate_code": "generate_code",
            "finalize": "finalize",
        },
    )
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
