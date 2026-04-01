"""High-level wrapper around the sklearn subagent graph."""

from __future__ import annotations

import uuid

from scientist_bin_backend.agents.sklearn.graph import build_sklearn_graph


class SklearnAgent:
    """Runs the sklearn ML pipeline: generate → execute → analyze (iterative)."""

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_sklearn_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        execution_plan: dict | None = None,
        analysis_report: str | None = None,
        split_data_paths: dict | None = None,
        problem_type: str | None = None,
        data_profile: dict | None = None,
        max_iterations: int = 5,
        experiment_id: str | None = None,
    ) -> dict:
        """Execute the sklearn training pipeline and return results.

        Args:
            objective: The training objective.
            execution_plan: Structured plan from the plan agent.
            analysis_report: Markdown report from the analyst agent.
            split_data_paths: ``{"train": path, "val": path, "test": path}``.
            problem_type: Classification, regression, clustering, etc.
            data_profile: Data profile dict from the analyst agent.
            max_iterations: Maximum generate-execute-analyze cycles.
            experiment_id: Unique experiment identifier.

        Returns:
            Dict with experiment_history, evaluation_results, generated_code, iterations, etc.
        """
        experiment_id = experiment_id or uuid.uuid4().hex[:12]

        # Derive strategy fields from execution plan
        candidate_algorithms: list[str] = []
        hyperparameter_spaces: dict | None = None
        success_criteria: dict | None = None
        if execution_plan:
            candidate_algorithms = execution_plan.get("algorithms_to_try", [])
            success_criteria = execution_plan.get("success_criteria")

        initial_state = {
            "messages": [],
            "objective": objective,
            "execution_plan": execution_plan,
            "analysis_report": analysis_report,
            "split_data_paths": split_data_paths or {},
            "problem_type": problem_type,
            "data_profile": data_profile,
            "strategy": execution_plan,
            "candidate_algorithms": candidate_algorithms,
            "hyperparameter_spaces": hyperparameter_spaces,
            "generated_code": None,
            "execution_output": None,
            "execution_success": False,
            "execution_error": None,
            "execution_metrics": [],
            "estimated_duration_seconds": None,
            "dynamic_timeout": None,
            "experiment_history": [],
            "best_experiment": None,
            "current_iteration": 0,
            "max_iterations": max_iterations,
            "next_action": None,
            "refinement_context": None,
            "search_results": None,
            "hyperparameters_summary": [],
            "reflection": None,
            "learned_heuristics": [],
            "success_criteria": success_criteria,
            "phase": "execution",
            "experiment_id": experiment_id,
            "error": None,
            "progress_events": [],
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "plan": result.get("strategy"),
            "generated_code": result.get("generated_code"),
            "evaluation_results": result.get("best_experiment"),
            "experiment_history": result.get("experiment_history", []),
            "data_profile": result.get("data_profile"),
            "problem_type": result.get("problem_type"),
            "iterations": result.get("current_iteration", 0),
            "hyperparameters_summary": result.get("hyperparameters_summary", []),
        }
