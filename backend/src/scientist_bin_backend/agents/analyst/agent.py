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
        task_analysis: dict | None = None,
        data_description: str | None = None,
        selected_framework: str | None = None,
    ) -> dict:
        """Execute the full analyst pipeline and return results.

        Args:
            objective: The ML task objective description.
            data_file_path: Path to the input CSV data file.
            execution_plan: Optional execution plan with target_column and other config.
            experiment_id: Unique experiment identifier (auto-generated if not provided).
            task_analysis: Upstream TaskAnalysis from the central orchestrator.
            data_description: Original user dataset description.
            selected_framework: Framework chosen by the central router.

        Returns:
            Dictionary with analysis_report, split_data_paths, data_profile,
            problem_type, cleaned_data_path, classification_confidence,
            and classification_reasoning.
        """
        experiment_id = experiment_id or uuid.uuid4().hex[:12]

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_file_path": data_file_path,
            "execution_plan": execution_plan,
            "task_analysis": task_analysis,
            "data_description": data_description,
            "selected_framework": selected_framework,
            "problem_type": None,
            "classification_confidence": None,
            "classification_reasoning": None,
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
            "classification_confidence": result.get("classification_confidence"),
            "classification_reasoning": result.get("classification_reasoning"),
        }


# ---------------------------------------------------------------------------
# Example use cases — run with: uv run python -m scientist_bin_backend.agents.analyst.agent
# ---------------------------------------------------------------------------

# Each tuple: (objective, data_file_path, task_analysis, selected_framework)
# task_analysis simulates what the central orchestrator's analyze node produces.
EXAMPLES: list[tuple[str, str | None, dict | None, str | None]] = [
    # 1. Full pipeline context: orchestrator provides task_analysis
    (
        "Classify iris species from petal and sepal measurements",
        "data/iris_data/Iris.csv",
        {
            "task_type": "classification",
            "task_subtype": "multiclass",
            "data_characteristics": {
                "estimated_features": "4",
                "estimated_samples": "150",
                "data_types": ["numeric"],
                "target_column_hint": "Species",
                "has_missing_values": False,
                "has_class_imbalance": False,
            },
            "recommended_approach": (
                "Start with logistic regression and random forest. "
                "Use stratified k-fold cross-validation."
            ),
            "complexity_estimate": "low",
            "key_considerations": ["small dataset", "balanced classes"],
            "suggested_frameworks": ["sklearn"],
        },
        "sklearn",
    ),
    # 2. Standalone mode: no task_analysis (e.g. CLI `analyze` command)
    (
        "Classify iris species from petal and sepal measurements",
        "data/iris_data/Iris.csv",
        None,
        None,
    ),
    # 3. Override scenario: upstream says regression, but data is classification
    (
        "Predict iris species from measurements",
        "data/iris_data/Iris.csv",
        {
            "task_type": "regression",
            "task_subtype": None,
            "data_characteristics": {
                "estimated_features": "4",
                "estimated_samples": "150",
                "data_types": ["numeric"],
                "target_column_hint": "Species",
            },
            "recommended_approach": "Use linear regression.",
            "complexity_estimate": "low",
            "key_considerations": [],
            "suggested_frameworks": ["sklearn"],
        },
        "sklearn",
    ),
    # 4. High complexity context (no real data file)
    (
        "Detect fraudulent credit card transactions",
        None,
        {
            "task_type": "classification",
            "task_subtype": "binary",
            "data_characteristics": {
                "estimated_features": "30",
                "estimated_samples": "284807",
                "data_types": ["numeric"],
                "target_column_hint": "Class",
                "has_missing_values": False,
                "has_class_imbalance": True,
            },
            "recommended_approach": (
                "Use imbalance-aware metrics (F1, ROC-AUC). Consider SMOTE or class weights."
            ),
            "complexity_estimate": "high",
            "key_considerations": [
                "severe class imbalance",
                "threshold tuning",
                "cost-sensitive learning",
            ],
            "suggested_frameworks": ["sklearn"],
        },
        "sklearn",
    ),
]


async def _run_examples() -> None:
    """Run the analyst pipeline on each example and print results."""
    import json
    from pathlib import Path

    backend_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    separator = "=" * 72

    for i, (objective, data_file, task_analysis, framework) in enumerate(EXAMPLES, 1):
        print(f"\n{separator}")
        print(f"  EXAMPLE {i}: {objective[:60]}")
        if task_analysis:
            print(f"  Upstream task_type: {task_analysis['task_type']}")
            print(f"  Complexity: {task_analysis.get('complexity_estimate', '?')}")
        else:
            print("  Standalone mode (no upstream task_analysis)")
        print(separator)

        # Resolve data file path relative to backend root
        resolved_path = None
        if data_file:
            resolved_path = str(backend_root / data_file)

        agent = AnalystAgent()
        result = await agent.run(
            objective=objective,
            data_file_path=resolved_path,
            task_analysis=task_analysis,
            selected_framework=framework,
        )

        print(f"\n  Problem type: {result.get('problem_type')}")
        print(f"  Classification confidence: {result.get('classification_confidence')}")
        print(f"  Reasoning: {result.get('classification_reasoning', '')[:120]}")

        profile = result.get("data_profile")
        if profile:
            print(f"  Data shape: {profile.get('shape')}")
            print(f"  Target column: {profile.get('target_column')}")

        splits = result.get("split_data_paths")
        if splits:
            print(f"  Split paths: {json.dumps(splits, indent=4)}")

        report = result.get("analysis_report")
        if report:
            # Print just the first few lines of the report
            lines = report.strip().splitlines()[:8]
            print("\n  Report preview:\n    " + "\n    ".join(lines))

        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_examples())
