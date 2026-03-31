"""StateGraph definition for the scikit-learn subagent.

Uses the base ML graph topology with sklearn-specific plan_strategy
and generate_code nodes.
"""

from __future__ import annotations

from scientist_bin_backend.agents.base.graph import build_ml_graph
from scientist_bin_backend.agents.sklearn.nodes.code_generator import generate_code
from scientist_bin_backend.agents.sklearn.nodes.planner import plan_strategy
from scientist_bin_backend.agents.sklearn.states import SklearnState


def build_sklearn_graph(checkpointer=None):
    """Build and compile the sklearn subagent graph.

    Flow:
        classify_problem -> analyze_data -> plan_strategy -> generate_code
        -> execute_code -> analyze_results -> (route) -> finalize | generate_code
    """
    return build_ml_graph(
        plan_strategy_fn=plan_strategy,
        generate_code_fn=generate_code,
        state_schema=SklearnState,
        checkpointer=checkpointer,
    )
