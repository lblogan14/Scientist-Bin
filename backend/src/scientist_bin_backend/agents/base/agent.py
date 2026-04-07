"""Base class for ML framework subagents.

Provides the common ``run()`` interface that all framework agents share,
handling initial state construction, graph invocation, and output extraction.
Framework-specific subagents extend this and implement ``_build_graph()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from scientist_bin_backend.utils.naming import generate_experiment_id


class BaseFrameworkAgent(ABC):
    """Abstract base for framework subagents (sklearn, pytorch, …).

    Subclasses must set ``framework_name`` and implement ``_build_graph()``.
    The ``run()`` method is shared: it constructs initial state, invokes the
    compiled graph, and extracts standardised output.
    """

    framework_name: str = ""

    def __init__(self, checkpointer=None) -> None:
        self.graph = self._build_graph(checkpointer)

    @abstractmethod
    def _build_graph(self, checkpointer):
        """Build and return the compiled LangGraph StateGraph."""
        ...

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
        """Execute the framework training pipeline and return results.

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
            Dict with experiment_history, evaluation_results, generated_code,
            iterations, test_metrics, etc.
        """
        experiment_id = experiment_id or generate_experiment_id(objective)

        # Derive strategy fields from execution plan
        candidate_algorithms: list[str] = []
        hyperparameter_spaces: dict | None = None
        success_criteria: dict | None = None
        if execution_plan:
            candidate_algorithms = execution_plan.get("algorithms_to_try", [])
            success_criteria = execution_plan.get("success_criteria")

        initial_state = {
            "messages": [],
            # Input from upstream pipeline
            "objective": objective,
            "execution_plan": execution_plan,
            "analysis_report": analysis_report,
            "split_data_paths": split_data_paths or {},
            "problem_type": problem_type,
            "data_profile": data_profile,
            # Strategy (derived from execution_plan)
            "strategy": execution_plan,
            "candidate_algorithms": candidate_algorithms,
            "hyperparameter_spaces": hyperparameter_spaces,
            "success_criteria": success_criteria,
            # Code generation & execution
            "generated_code": None,
            "validation_error": None,
            "validation_attempts": 0,
            "execution_output": None,
            "execution_results_json": None,
            "execution_success": False,
            "execution_error": None,
            "execution_metrics": [],
            # Duration estimation
            "estimated_duration_seconds": None,
            "dynamic_timeout": None,
            # Iteration & tracking
            "experiment_history": [],
            "best_experiment": None,
            "current_iteration": 0,
            "max_iterations": max_iterations,
            "error_retry_count": 0,
            "max_error_retries": 3,
            "next_action": None,
            "refinement_context": None,
            # Test evaluation
            "test_metrics": None,
            "test_evaluation_code": None,
            # Error research
            "search_results": None,
            # Reflection & learning
            "reflection": None,
            "learned_heuristics": [],
            # Summary output
            "hyperparameters_summary": [],
            # Control
            "phase": "execution",
            "experiment_id": experiment_id,
            "framework_name": self.framework_name,
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
            "test_metrics": result.get("test_metrics"),
            "test_evaluation_code": result.get("test_evaluation_code"),
            "test_diagnostics": result.get("test_diagnostics"),
        }
