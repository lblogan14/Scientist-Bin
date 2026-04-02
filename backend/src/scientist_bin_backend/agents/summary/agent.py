"""High-level wrapper around the summary agent graph."""

from __future__ import annotations

import asyncio
import logging

from scientist_bin_backend.agents.summary.graph import build_summary_graph
from scientist_bin_backend.utils.naming import generate_experiment_id

logger = logging.getLogger(__name__)


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
        data_profile: dict | None = None,
        plan_markdown: str | None = None,
        split_data_paths: dict | None = None,
        framework_results: dict | None = None,
        experiment_history: list[dict] | None = None,
        test_metrics: dict | None = None,
        test_diagnostics: dict | None = None,
        generated_code: str | None = None,
        test_evaluation_code: str | None = None,
        experiment_id: str | None = None,
    ) -> dict:
        """Execute the full summary pipeline and return results.

        Args:
            objective: The original ML objective.
            problem_type: Detected problem type (classification, regression, etc.).
            execution_plan: The strategy plan from the plan agent.
            analysis_report: Markdown EDA report from the analyst agent.
            data_profile: Structured data profile from the analyst agent.
            plan_markdown: Human-readable execution plan.
            split_data_paths: ``{"train": path, "val": path, "test": path}``.
            framework_results: Full results dict from the framework agent.
            experiment_history: List of per-iteration experiment records.
            test_metrics: Metrics from held-out test set evaluation.
            test_diagnostics: Enriched test results (confusion_matrix, etc.).
            generated_code: Final generated training code (for reproducibility).
            test_evaluation_code: Test evaluation code (for reproducibility).
            experiment_id: Experiment identifier (generated if not provided).

        Returns:
            Dict with summary_report, best_model, best_hyperparameters,
            best_metrics, model_rankings, selection_reasoning, and
            report_sections.
        """
        experiment_id = experiment_id or generate_experiment_id(objective)

        initial_state = {
            "messages": [],
            # Input from upstream agents
            "objective": objective,
            "problem_type": problem_type,
            "analysis_report": analysis_report,
            "data_profile": data_profile,
            "split_data_paths": split_data_paths,
            "execution_plan": execution_plan,
            "plan_markdown": plan_markdown,
            "framework_results": framework_results,
            "experiment_history": experiment_history or [],
            "test_metrics": test_metrics,
            "test_diagnostics": test_diagnostics,
            "generated_code": generated_code,
            "test_evaluation_code": test_evaluation_code,
            # Intermediate (populated by nodes)
            "summary_context": None,
            "diagnostics": None,
            # Analysis (populated by review_and_rank)
            "model_rankings": [],
            "best_model": None,
            "best_hyperparameters": None,
            "best_metrics": None,
            "selection_reasoning": None,
            # Output
            "summary_report": None,
            "report_sections": None,
            # Control
            "experiment_id": experiment_id,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "summary_report": result.get("summary_report"),
            "best_model": result.get("best_model"),
            "best_hyperparameters": result.get("best_hyperparameters"),
            "best_metrics": result.get("best_metrics"),
            "model_rankings": result.get("model_rankings", []),
            "selection_reasoning": result.get("selection_reasoning"),
            "report_sections": result.get("report_sections"),
        }


# ---------------------------------------------------------------------------
# Standalone validation
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "objective": "Classify iris species based on petal and sepal measurements",
        "problem_type": "classification",
        "execution_plan": {
            "approach_summary": "Train classifiers with cross-validation",
            "algorithms_to_try": ["LogisticRegression", "RandomForestClassifier"],
            "evaluation_metrics": ["accuracy", "f1_weighted"],
            "cv_strategy": "5-fold stratified",
            "success_criteria": {"val_accuracy": 0.90},
        },
        "analysis_report": "Dataset: 150 samples, 4 features, 3 classes (balanced).",
        "data_profile": {
            "shape": [150, 5],
            "column_names": [
                "sepal_length",
                "sepal_width",
                "petal_length",
                "petal_width",
                "species",
            ],
            "target_column": "species",
            "class_distribution": {"setosa": 50, "versicolor": 50, "virginica": 50},
        },
        "experiment_history": [
            {
                "iteration": 1,
                "algorithm": "LogisticRegression",
                "hyperparameters": {"C": 1.0, "solver": "lbfgs"},
                "metrics": {
                    "train_accuracy": 0.97,
                    "val_accuracy": 0.95,
                    "train_f1_weighted": 0.97,
                    "val_f1_weighted": 0.95,
                },
                "training_time_seconds": 0.5,
                "cv_fold_scores": {
                    "accuracy": [0.93, 0.96, 0.95, 0.94, 0.97],
                },
                "feature_importances": [
                    {"feature": "petal_length", "importance": 0.45},
                    {"feature": "petal_width", "importance": 0.42},
                    {"feature": "sepal_length", "importance": 0.08},
                    {"feature": "sepal_width", "importance": 0.05},
                ],
                "confusion_matrix": {
                    "labels": ["setosa", "versicolor", "virginica"],
                    "matrix": [[10, 0, 0], [0, 9, 1], [0, 1, 9]],
                },
            },
            {
                "iteration": 2,
                "algorithm": "RandomForestClassifier",
                "hyperparameters": {"n_estimators": 100, "max_depth": 5},
                "metrics": {
                    "train_accuracy": 1.0,
                    "val_accuracy": 0.96,
                    "train_f1_weighted": 1.0,
                    "val_f1_weighted": 0.96,
                },
                "training_time_seconds": 2.1,
                "cv_fold_scores": {
                    "accuracy": [0.95, 0.97, 0.96, 0.95, 0.97],
                },
                "feature_importances": [
                    {"feature": "petal_width", "importance": 0.48},
                    {"feature": "petal_length", "importance": 0.44},
                    {"feature": "sepal_length", "importance": 0.05},
                    {"feature": "sepal_width", "importance": 0.03},
                ],
                "confusion_matrix": {
                    "labels": ["setosa", "versicolor", "virginica"],
                    "matrix": [[10, 0, 0], [0, 10, 0], [0, 1, 9]],
                },
            },
        ],
        "test_metrics": {"test_accuracy": 0.93, "test_f1_weighted": 0.93},
    },
]


async def _run_examples() -> None:
    agent = SummaryAgent()
    for i, example in enumerate(EXAMPLES, 1):
        logger.info("=" * 60)
        logger.info("Example %d: %s", i, example["objective"])
        logger.info("=" * 60)
        result = await agent.run(**example)
        logger.info("Best model: %s", result["best_model"])
        logger.info("Best metrics: %s", result["best_metrics"])
        logger.info("Selection reasoning: %s", result["selection_reasoning"])
        report = result.get("summary_report", "")
        logger.info(
            "Report preview (first 500 chars):\n%s",
            report[:500] if report else "No report generated",
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_run_examples())
