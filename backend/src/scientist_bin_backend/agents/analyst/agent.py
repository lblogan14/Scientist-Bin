"""High-level wrapper around the analyst agent graph."""

from __future__ import annotations

import uuid

from scientist_bin_backend.agents.analyst.graph import build_analyst_graph


class AnalystAgent:
    """Runs the analyst pipeline: profile -> clean -> split -> report."""

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_analyst_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        data_file_path: str | None = None,
        execution_plan: dict | None = None,
        experiment_id: str | None = None,
    ) -> dict:
        """Execute the full analyst pipeline and return results.

        Args:
            objective: The ML task objective description.
            data_file_path: Path to the input CSV data file.
            execution_plan: Optional execution plan with target_column and other config.
            experiment_id: Unique experiment identifier (auto-generated if not provided).

        Returns:
            Dictionary with analysis_report, split_data_paths, data_profile,
            problem_type, and cleaned_data_path.
        """
        experiment_id = experiment_id or uuid.uuid4().hex[:12]

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_file_path": data_file_path,
            "execution_plan": execution_plan,
            "problem_type": None,
            "data_profile": None,
            "cleaning_code": None,
            "cleaning_output": None,
            "cleaned_data_path": None,
            "split_code": None,
            "split_output": None,
            "split_data_paths": None,
            "analysis_report": None,
            "experiment_id": experiment_id,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "analysis_report": result.get("analysis_report"),
            "split_data_paths": result.get("split_data_paths"),
            "data_profile": result.get("data_profile"),
            "problem_type": result.get("problem_type"),
            "cleaned_data_path": result.get("cleaned_data_path"),
        }
