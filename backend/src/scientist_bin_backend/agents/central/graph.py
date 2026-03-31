"""StateGraph definition for the central orchestrator agent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.central.nodes.analyzer import analyze
from scientist_bin_backend.agents.central.nodes.router import route, select_subagent
from scientist_bin_backend.agents.central.states import CentralState


async def _sklearn_delegate(state: CentralState) -> dict:
    """Delegate to the sklearn subagent and map results back."""
    from scientist_bin_backend.agents.sklearn.agent import SklearnAgent

    agent = SklearnAgent()
    result = await agent.run(
        objective=state["objective"],
        data_description=state.get("data_description", ""),
        data_file_path=state.get("data_file_path"),
        experiment_id=state.get("experiment_id"),
    )
    return {"agent_response": result}


def build_central_graph():
    """Build and compile the central orchestrator graph."""
    builder = StateGraph(CentralState)

    builder.add_node("analyze", analyze)
    builder.add_node("route", route)
    builder.add_node("sklearn", _sklearn_delegate)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "route")
    builder.add_conditional_edges("route", select_subagent, {"sklearn": "sklearn", END: END})
    builder.add_edge("sklearn", END)

    return builder.compile()
