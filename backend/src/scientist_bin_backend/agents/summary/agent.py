"""High-level wrapper around the summary agent graph."""

from __future__ import annotations

from scientist_bin_backend.agents.summary.graph import build_summary_graph
from scientist_bin_backend.utils.naming import generate_experiment_id


class SummaryAgent:
    """Reviews experiment results, selects the best model, and generates a report."""

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_summary_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        problem_type: str | None = None,
        execution_plan: dict | None = None,
        analysis_report: str | None = None,
        sklearn_results: dict | None = None,
        experiment_history: list[dict] | None = None,
        runs: list[dict] | None = None,
        experiment_id: str | None = None,
    ) -> dict:
        """Execute the full summary pipeline and return results.

        Args:
            objective: The original ML objective.
            problem_type: Detected problem type (classification, regression, etc.).
            execution_plan: The strategy plan used by the sklearn subagent.
            analysis_report: Data analysis / EDA report text.
            sklearn_results: Full results dict from the sklearn subagent.
            experiment_history: List of per-iteration experiment records.
            runs: List of raw run detail dicts.
            experiment_id: Experiment identifier (generated if not provided).

        Returns:
            Dict with summary_report, best_model, best_hyperparameters,
            best_metrics, and model_comparison.
        """
        experiment_id = experiment_id or generate_experiment_id(objective)

        initial_state = {
            "messages": [],
            "objective": objective,
            "problem_type": problem_type,
            "execution_plan": execution_plan,
            "analysis_report": analysis_report,
            "sklearn_results": sklearn_results,
            "experiment_history": experiment_history or [],
            "runs": runs or [],
            "best_model": None,
            "best_hyperparameters": None,
            "best_metrics": None,
            "model_comparison": [],
            "summary_report": None,
            "experiment_id": experiment_id,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "summary_report": result.get("summary_report"),
            "best_model": result.get("best_model"),
            "best_hyperparameters": result.get("best_hyperparameters"),
            "best_metrics": result.get("best_metrics"),
            "model_comparison": result.get("model_comparison", []),
        }
