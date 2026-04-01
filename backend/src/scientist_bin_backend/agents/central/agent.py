"""High-level wrapper around the central orchestrator graph."""

from __future__ import annotations

from scientist_bin_backend.agents.central.graph import build_central_graph
from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest
from scientist_bin_backend.agents.central.utils import build_initial_state


class CentralAgent:
    """Entrypoint for running the full agent pipeline.

    The pipeline is:
        analyze → route → analyst → plan (HITL) → framework → summary → END
    """

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_central_graph(checkpointer=checkpointer)

    async def run(
        self, request: TrainRequest, *, experiment_id: str | None = None
    ) -> AgentResponse:
        """Execute the graph end-to-end and return a structured response."""
        initial_state = build_initial_state(request, experiment_id=experiment_id)
        final_state = await self.graph.ainvoke(initial_state)

        agent_resp = final_state.get("agent_response") or {}
        return AgentResponse(
            framework=final_state.get("selected_framework") or "sklearn",
            plan=agent_resp.get("plan"),
            plan_markdown=final_state.get("plan_markdown"),
            generated_code=agent_resp.get("generated_code"),
            evaluation_results=agent_resp.get("evaluation_results"),
            experiment_history=agent_resp.get("experiment_history", []),
            data_profile=final_state.get("data_profile"),
            problem_type=final_state.get("problem_type"),
            iterations=agent_resp.get("iterations", 0),
            analysis_report=final_state.get("analysis_report"),
            summary_report=final_state.get("summary_report"),
            best_model=agent_resp.get("best_model"),
            best_hyperparameters=agent_resp.get("best_hyperparameters"),
            status="failed" if final_state.get("error") else "completed",
        )
