"""High-level wrapper around the sklearn subagent graph."""

from __future__ import annotations

import uuid

from scientist_bin_backend.agents.sklearn.graph import build_sklearn_graph


class SklearnAgent:
    """Runs the sklearn ML pipeline: classify -> EDA -> plan -> generate -> execute -> analyze."""

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_sklearn_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        data_description: str = "",
        data_file_path: str | None = None,
        max_iterations: int = 5,
        experiment_id: str | None = None,
    ) -> dict:
        """Execute the full sklearn pipeline and return results."""
        experiment_id = experiment_id or uuid.uuid4().hex[:12]

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_description": data_description,
            "data_file_path": data_file_path,
            "problem_type": None,
            "data_profile": None,
            "eda_code": None,
            "eda_output": None,
            "strategy": None,
            "candidate_algorithms": [],
            "preprocessing_plan": [],
            "feature_engineering_plan": [],
            "hyperparameter_spaces": None,
            "cv_strategy": None,
            "success_criteria": None,
            "generated_code": None,
            "execution_output": None,
            "execution_success": False,
            "execution_error": None,
            "execution_metrics": [],
            "estimated_duration_seconds": None,
            "dynamic_timeout": None,
            "data_subset_size": None,
            "experiment_history": [],
            "best_experiment": None,
            "current_iteration": 0,
            "max_iterations": max_iterations,
            "next_action": None,
            "refinement_context": None,
            "reflection": None,
            "learned_heuristics": [],
            "phase": "classify",
            "experiment_id": experiment_id,
            "error": None,
            "progress_events": [],
            "search_results": None,
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
        }
