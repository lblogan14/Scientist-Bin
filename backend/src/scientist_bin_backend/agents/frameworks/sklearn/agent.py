"""High-level wrapper around the sklearn subagent graph."""

from __future__ import annotations

from scientist_bin_backend.agents.base.agent import BaseFrameworkAgent
from scientist_bin_backend.agents.base.graph import build_framework_graph
from scientist_bin_backend.agents.frameworks.sklearn.nodes.code_generator import (
    generate_code,
)
from scientist_bin_backend.agents.frameworks.sklearn.nodes.error_researcher import (
    error_research,
)
from scientist_bin_backend.agents.frameworks.sklearn.states import SklearnState


class SklearnAgent(BaseFrameworkAgent):
    """Runs the sklearn ML pipeline: generate -> validate -> execute -> analyze (iterative)."""

    framework_name = "sklearn"

    def _build_graph(self, checkpointer):
        return build_framework_graph(
            state_class=SklearnState,
            generate_code_node=generate_code,
            error_research_node=error_research,
            checkpointer=checkpointer,
        )


# ---------------------------------------------------------------------------
# Examples for isolated validation
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "name": "iris_classification",
        "objective": "Classify iris species using petal and sepal measurements",
        "problem_type": "classification",
        "execution_plan": {
            "approach_summary": "Try logistic regression and random forest with grid search",
            "algorithms_to_try": ["LogisticRegression", "RandomForestClassifier"],
            "evaluation_metrics": ["accuracy", "f1_weighted"],
            "cv_strategy": "5-fold stratified",
            "success_criteria": {"accuracy": 0.90},
            "pipeline_preprocessing_steps": ["StandardScaler on numeric features"],
            "feature_engineering_steps": [],
            "hyperparameter_tuning_approach": "GridSearchCV",
        },
    },
    {
        "name": "regression_basic",
        "objective": "Predict housing prices from structural features",
        "problem_type": "regression",
        "execution_plan": {
            "approach_summary": "Try linear regression and gradient boosting",
            "algorithms_to_try": ["Ridge", "GradientBoostingRegressor"],
            "evaluation_metrics": ["mse", "r2"],
            "cv_strategy": "5-fold",
            "success_criteria": {"r2": 0.80},
            "pipeline_preprocessing_steps": ["StandardScaler"],
            "feature_engineering_steps": [],
            "hyperparameter_tuning_approach": "GridSearchCV",
        },
    },
]


async def _run_examples() -> None:
    """Run examples for validation. Requires split data to be available."""
    import json

    agent = SklearnAgent()
    for ex in EXAMPLES:
        print(f"\n{'=' * 60}")
        print(f"Example: {ex['name']}")
        print(f"Objective: {ex['objective']}")
        print(f"Plan: {json.dumps(ex['execution_plan'], indent=2)}")
        print(f"{'=' * 60}")
        print("(Skipping execution -- requires split data files on disk)")
        print(f"Agent framework: {agent.framework_name}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_examples())
