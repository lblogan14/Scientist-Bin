"""Shared graph builder for ML framework subagents.

Builds the standard generate → validate → execute → analyze iteration loop
with error-research side-path and test evaluation on acceptance.

Flow::

    START → generate_code → validate_code → [route_validation]
        validation_ok  → execute_code → analyze_results → [route_decision]
        validation_fail → generate_code  (loop, max retries then execute anyway)

    route_decision:
        accept / abort  → evaluate_on_test → finalize → END
        fix_error       → error_research → generate_code
        refine / new_algo / feature_eng → generate_code
"""

from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.base.nodes.code_executor import execute_code
from scientist_bin_backend.agents.base.nodes.code_validator import (
    MAX_VALIDATION_ATTEMPTS,
    validate_code,
)
from scientist_bin_backend.agents.base.nodes.results_analyzer import (
    analyze_results,
    finalize,
)
from scientist_bin_backend.agents.base.nodes.test_evaluator import evaluate_on_test


def _route_validation(state: dict) -> str:
    """Route after code validation.

    - No error → proceed to execution.
    - Error but under retry limit → regenerate code.
    - Error and at retry limit → proceed to execution anyway (let it fail
      with a real error message).
    """
    validation_error = state.get("validation_error")
    validation_attempts = state.get("validation_attempts", 0)

    if not validation_error:
        return "execute_code"
    if validation_attempts >= MAX_VALIDATION_ATTEMPTS:
        return "execute_code"
    return "generate_code"


def _route_decision(state: dict) -> str:
    """Route based on the analyze_results decision.

    - accept / abort → evaluate_on_test (then finalize)
    - fix_error → error_research (web search before regenerating)
    - refine_params / try_new_algo / feature_engineer → generate_code
    """
    next_action = state.get("next_action", "abort")
    if next_action in ("accept", "abort"):
        return "evaluate_on_test"
    if next_action == "fix_error":
        return "error_research"
    return "generate_code"


def build_framework_graph(
    state_class: type,
    generate_code_node: Callable,
    error_research_node: Callable | None = None,
    checkpointer=None,
) -> object:
    """Build and compile the standard framework subagent graph.

    Args:
        state_class: The TypedDict state schema for the graph.
        generate_code_node: Framework-specific code generation node function.
        error_research_node: Framework-specific error research node function.
            If ``None``, the ``fix_error`` path routes directly to
            ``generate_code`` (error context is still available via state).
        checkpointer: Optional LangGraph checkpointer for persistence.

    Returns:
        Compiled LangGraph ``StateGraph``.
    """
    builder = StateGraph(state_class)

    # Register nodes
    builder.add_node("generate_code", generate_code_node)
    builder.add_node("validate_code", validate_code)
    builder.add_node("execute_code", execute_code)
    builder.add_node("analyze_results", analyze_results)
    builder.add_node("evaluate_on_test", evaluate_on_test)
    builder.add_node("finalize", finalize)

    if error_research_node is not None:
        builder.add_node("error_research", error_research_node)

    # Edges: START → generate_code → validate_code → (routing)
    builder.add_edge(START, "generate_code")
    builder.add_edge("generate_code", "validate_code")

    # Validation routing
    builder.add_conditional_edges(
        "validate_code",
        _route_validation,
        {
            "execute_code": "execute_code",
            "generate_code": "generate_code",
        },
    )

    # execute → analyze → (routing)
    builder.add_edge("execute_code", "analyze_results")

    # Decision routing after analysis
    if error_research_node is not None:
        builder.add_conditional_edges(
            "analyze_results",
            _route_decision,
            {
                "generate_code": "generate_code",
                "error_research": "error_research",
                "evaluate_on_test": "evaluate_on_test",
            },
        )
        builder.add_edge("error_research", "generate_code")
    else:
        # Without error research, fix_error routes directly to generate_code
        def _route_decision_no_research(state: dict) -> str:
            next_action = state.get("next_action", "abort")
            if next_action in ("accept", "abort"):
                return "evaluate_on_test"
            return "generate_code"

        builder.add_conditional_edges(
            "analyze_results",
            _route_decision_no_research,
            {
                "generate_code": "generate_code",
                "evaluate_on_test": "evaluate_on_test",
            },
        )

    # evaluate_on_test → finalize → END
    builder.add_edge("evaluate_on_test", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
