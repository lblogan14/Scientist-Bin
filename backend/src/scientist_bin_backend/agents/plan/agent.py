"""High-level wrapper around the plan agent graph."""

from __future__ import annotations

import logging

from scientist_bin_backend.agents.plan.graph import build_plan_graph
from scientist_bin_backend.utils.naming import generate_experiment_id

logger = logging.getLogger(__name__)


class PlanAgent:
    """Runs the planning pipeline: research -> plan -> review -> save.

    The review step uses ``interrupt()`` for human-in-the-loop approval.
    When ``auto_approve=True`` the interrupt is skipped and the plan is
    accepted immediately.
    """

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_plan_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        data_description: str = "",
        data_file_path: str | None = None,
        framework_preference: str | None = None,
        experiment_id: str | None = None,
        auto_approve: bool = False,
        max_revisions: int = 3,
        task_analysis: dict | None = None,
        analysis_report: str | None = None,
        data_profile: dict | None = None,
        problem_type: str | None = None,
    ) -> dict:
        """Execute the full planning pipeline and return results.

        Args:
            objective: The user's ML objective in natural language.
            data_description: Free-text description of the dataset.
            data_file_path: Absolute path to the data file, if any.
            framework_preference: Preferred ML framework (e.g. "sklearn").
            experiment_id: Existing experiment ID, or auto-generated.
            auto_approve: When ``True``, skip human review and approve
                the plan automatically.
            max_revisions: Maximum number of plan revisions before
                auto-approving.
            task_analysis: Structured analysis from the central agent.
            analysis_report: Data analysis report from the analyst agent.
            data_profile: Data profile dict from the analyst agent.
            problem_type: ML problem type from the analyst agent.

        Returns:
            A dict with ``execution_plan``, ``plan_markdown``,
            ``plan_approved``, and ``search_results``.
        """
        experiment_id = experiment_id or generate_experiment_id(objective)

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_description": data_description,
            "data_file_path": data_file_path,
            "framework_preference": framework_preference,
            "task_analysis": task_analysis,
            "analysis_report": analysis_report,
            "data_profile": data_profile,
            "problem_type": problem_type,
            "search_results": None,
            "execution_plan": None,
            "plan_markdown": None,
            "human_feedback": None,
            "plan_approved": auto_approve,
            "revision_count": 0,
            "max_revisions": max_revisions,
            "experiment_id": experiment_id,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "execution_plan": result.get("execution_plan"),
            "plan_markdown": result.get("plan_markdown"),
            "plan_approved": result.get("plan_approved", False),
            "search_results": result.get("search_results"),
        }


# ---------------------------------------------------------------------------
# Example use cases — run with: uv run python -m scientist_bin_backend.agents.plan.agent
# ---------------------------------------------------------------------------

# Each tuple: (objective, data_description, task_analysis, data_profile, problem_type, framework)
EXAMPLES: list[tuple[str, str, dict | None, dict | None, str | None, str | None]] = [
    # 1. Full pipeline context: all upstream signals available
    (
        "Classify iris species from petal and sepal measurements",
        "Fisher's Iris dataset with 150 samples and 4 numeric features",
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
        {
            "shape": [150, 5],
            "column_names": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
                "Species",
            ],
            "numeric_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "categorical_columns": [],
            "target_column": "Species",
            "missing_counts": {},
            "class_distribution": {
                "Iris-setosa": 50,
                "Iris-versicolor": 50,
                "Iris-virginica": 50,
            },
            "data_quality_issues": [],
        },
        "classification",
        "sklearn",
    ),
    # 2. Minimal context: objective + problem type only (standalone CLI)
    (
        "Predict house prices from property features",
        "Tabular housing dataset with numeric and categorical features",
        None,
        None,
        "regression",
        "sklearn",
    ),
    # 3. High complexity: imbalanced binary classification
    (
        "Detect fraudulent credit card transactions",
        "Large transaction dataset with severe class imbalance",
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
                "Use imbalance-aware metrics (F1, ROC-AUC). Consider class weights."
            ),
            "complexity_estimate": "high",
            "key_considerations": [
                "severe class imbalance",
                "threshold tuning",
                "cost-sensitive learning",
            ],
            "suggested_frameworks": ["sklearn"],
        },
        {
            "shape": [284807, 31],
            "column_names": [f"V{i}" for i in range(1, 29)] + ["Time", "Amount", "Class"],
            "numeric_columns": [f"V{i}" for i in range(1, 29)] + ["Time", "Amount"],
            "categorical_columns": [],
            "target_column": "Class",
            "missing_counts": {},
            "class_distribution": {"0": 284315, "1": 492},
            "data_quality_issues": ["severe class imbalance (0.17% positive)"],
        },
        "classification",
        "sklearn",
    ),
]


async def _run_examples() -> None:
    """Run the plan pipeline on each example and log results."""
    separator = "=" * 72

    for i, (objective, data_desc, task_analysis, data_profile, problem_type, fw) in enumerate(
        EXAMPLES, 1
    ):
        logger.info("\n%s", separator)
        logger.info("  EXAMPLE %d: %s", i, objective[:60])
        logger.info("  Problem type: %s", problem_type)
        if task_analysis:
            logger.info("  Complexity: %s", task_analysis.get("complexity_estimate", "?"))
        else:
            logger.info("  No upstream task_analysis")
        logger.info(separator)

        agent = PlanAgent()
        result = await agent.run(
            objective=objective,
            data_description=data_desc,
            framework_preference=fw,
            auto_approve=True,
            task_analysis=task_analysis,
            data_profile=data_profile,
            problem_type=problem_type,
        )

        plan = result.get("execution_plan") or {}
        logger.info("  Approach: %s", plan.get("approach_summary", "N/A")[:120])
        logger.info("  Algorithms: %s", plan.get("algorithms_to_try", []))
        logger.info("  Metrics: %s", plan.get("evaluation_metrics", []))
        logger.info("  CV: %s", plan.get("cv_strategy", "N/A"))
        logger.info("  Tuning: %s", plan.get("hyperparameter_tuning_approach", "N/A")[:100])
        logger.info("  Success criteria: %s", plan.get("success_criteria", {}))
        logger.info("  Plan approved: %s", result.get("plan_approved"))

        md = result.get("plan_markdown")
        if md:
            lines = md.strip().splitlines()[:10]
            logger.info("  Plan preview:\n    %s", "\n    ".join(lines))


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_run_examples())
