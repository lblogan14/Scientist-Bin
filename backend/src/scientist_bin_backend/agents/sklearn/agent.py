"""High-level wrapper around the sklearn subagent graph."""

from __future__ import annotations

from scientist_bin_backend.agents.sklearn.graph import build_sklearn_graph


class SklearnAgent:
    """Runs the sklearn plan → generate → evaluate pipeline."""

    def __init__(self) -> None:
        self.graph = build_sklearn_graph()

    async def run(
        self,
        objective: str,
        data_description: str = "",
        plan: str | None = None,
    ) -> dict:
        """Execute the sklearn graph and return results."""
        initial_state = {
            "messages": [],
            "objective": objective,
            "data_description": data_description,
            "plan": plan,
            "search_results": None,
            "generated_code": None,
            "evaluation_results": None,
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
        }
        result = await self.graph.ainvoke(initial_state)
        return {
            "plan": result.get("plan"),
            "generated_code": result.get("generated_code"),
            "evaluation_results": result.get("evaluation_results"),
        }
