"""High-level wrapper around the central orchestrator graph."""

from __future__ import annotations

from scientist_bin_backend.agents.central.graph import build_central_graph
from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest
from scientist_bin_backend.agents.central.utils import build_initial_state


class CentralAgent:
    """Entrypoint for running the full agent pipeline."""

    def __init__(self) -> None:
        self.graph = build_central_graph()

    async def run(self, request: TrainRequest) -> AgentResponse:
        """Execute the graph end-to-end and return a structured response."""
        initial_state = build_initial_state(request)
        final_state = await self.graph.ainvoke(initial_state)

        agent_resp = final_state.get("agent_response") or {}
        return AgentResponse(
            framework=final_state.get("selected_framework") or "sklearn",
            plan=agent_resp.get("plan"),
            generated_code=agent_resp.get("generated_code"),
            evaluation_results=agent_resp.get("evaluation_results"),
            experiment_history=agent_resp.get("experiment_history", []),
            data_profile=agent_resp.get("data_profile"),
            problem_type=agent_resp.get("problem_type"),
            iterations=agent_resp.get("iterations", 0),
            status="failed" if final_state.get("error") else "completed",
        )
