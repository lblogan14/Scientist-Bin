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


# ---------------------------------------------------------------------------
# Example use cases — run with: uv run python -m scientist_bin_backend.agents.central.agent
# ---------------------------------------------------------------------------

EXAMPLES = [
    TrainRequest(
        objective="Classify iris species from petal and sepal measurements",
        data_description=(
            "150 samples, 4 numeric features (sepal_length, sepal_width, "
            "petal_length, petal_width), 3 balanced classes (setosa, "
            "versicolor, virginica). No missing values."
        ),
    ),
    TrainRequest(
        objective="Predict house prices from property features",
        data_description=(
            "20,000 rows, 80 features including lot area, year built, "
            "overall quality, garage size, neighborhood (categorical). "
            "Target: SalePrice (continuous). Some features have up to "
            "20% missing values."
        ),
    ),
    TrainRequest(
        objective="Segment customers into groups based on purchasing behavior",
        data_description=(
            "5,000 customers with features: total_spend, frequency, "
            "recency, avg_order_value, product_categories (one-hot). "
            "No target column — unsupervised task."
        ),
    ),
    TrainRequest(
        objective="Detect fraudulent credit card transactions",
        data_description=(
            "284,807 transactions with 30 numeric features (PCA-transformed). "
            "Target: Class (0=normal, 1=fraud). Highly imbalanced — only "
            "0.17% are fraud. No missing values."
        ),
    ),
    TrainRequest(
        objective="Build a text classifier for sentiment analysis on movie reviews",
        data_description="50,000 IMDB reviews, binary labels (positive/negative).",
        framework_preference="transformers",
    ),
]


async def _run_examples() -> None:
    """Run analyze + route on each example and print results."""
    import json

    from scientist_bin_backend.agents.central.nodes.analyzer import analyze
    from scientist_bin_backend.agents.central.nodes.router import route
    from scientist_bin_backend.agents.central.utils import build_initial_state

    separator = "=" * 72

    for i, request in enumerate(EXAMPLES, 1):
        print(f"\n{separator}")
        print(f"  EXAMPLE {i}: {request.objective[:60]}")
        if request.framework_preference:
            print(f"  Framework preference: {request.framework_preference}")
        print(separator)

        state = build_initial_state(request)

        # --- Step 1: Analyze ---
        print("\n--- Analyzer Output ---")
        analysis_update = await analyze(state)
        task_analysis = analysis_update["task_analysis"]
        print(json.dumps(task_analysis, indent=2))

        # Apply the analysis update to state for the router
        state = {**state, **analysis_update}

        # --- Step 2: Route ---
        print("\n--- Router Output ---")
        route_update = await route(state)
        selected = route_update.get("selected_framework")
        msg = route_update["messages"][0].content
        print(f"Selected framework: {selected}")
        print(f"Reasoning: {msg}")

        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_examples())
