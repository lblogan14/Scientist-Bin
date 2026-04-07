"""High-level wrapper around the FLAML AutoML subagent graph."""

from __future__ import annotations

import logging

from scientist_bin_backend.agents.base.agent import BaseFrameworkAgent
from scientist_bin_backend.agents.base.graph import build_framework_graph
from scientist_bin_backend.agents.frameworks.flaml.nodes.code_generator import (
    generate_code,
)
from scientist_bin_backend.agents.frameworks.flaml.nodes.error_researcher import (
    error_research,
)
from scientist_bin_backend.agents.frameworks.flaml.states import FlamlState

logger = logging.getLogger(__name__)


class FlamlAgent(BaseFrameworkAgent):
    """Runs the FLAML AutoML pipeline: generate -> validate -> execute -> analyze (iterative).

    FLAML handles model selection and hyperparameter tuning automatically within
    a time budget, trying estimators like LightGBM, XGBoost, CatBoost,
    RandomForest, and (for time series) Prophet/ARIMA/SARIMAX.
    """

    framework_name = "flaml"

    def _build_graph(self, checkpointer):
        return build_framework_graph(
            state_class=FlamlState,
            generate_code_node=generate_code,
            error_research_node=error_research,
            checkpointer=checkpointer,
        )


# ---------------------------------------------------------------------------
# Examples for isolated validation
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "name": "iris_classification_automl",
        "objective": "Classify iris species using petal and sepal measurements",
        "problem_type": "classification",
        "execution_plan": {
            "approach_summary": "Use FLAML AutoML to find the best classifier",
            "time_budget": 60,
            "estimator_list": ["lgbm", "xgboost", "rf", "extra_tree", "lrl1"],
            "evaluation_metrics": ["accuracy", "f1_weighted"],
            "success_criteria": {"accuracy": 0.90},
        },
    },
    {
        "name": "regression_automl",
        "objective": "Predict housing prices from structural features",
        "problem_type": "regression",
        "execution_plan": {
            "approach_summary": "Use FLAML AutoML for regression with automatic model selection",
            "time_budget": 120,
            "estimator_list": ["lgbm", "rf", "catboost", "xgboost", "extra_tree"],
            "evaluation_metrics": ["r2", "rmse"],
            "success_criteria": {"r2": 0.80},
        },
    },
    {
        "name": "ts_forecast_automl",
        "objective": "Forecast monthly airline passengers",
        "problem_type": "ts_forecast",
        "execution_plan": {
            "approach_summary": "Use FLAML AutoML for time series forecasting",
            "time_budget": 120,
            "estimator_list": ["lgbm", "xgboost", "prophet", "arima", "sarimax"],
            "evaluation_metrics": ["mape", "rmse"],
            "ts_period": 12,
            "success_criteria": {"mape": 0.10},
        },
    },
]


async def _run_examples() -> None:
    """Run examples for validation. Requires split data to be available."""
    import json

    agent = FlamlAgent()
    for ex in EXAMPLES:
        logger.info("=" * 60)
        logger.info("Example: %s", ex["name"])
        logger.info("Objective: %s", ex["objective"])
        logger.info("Plan:\n%s", json.dumps(ex["execution_plan"], indent=2))
        logger.info("=" * 60)
        logger.info("(Skipping execution -- requires split data files on disk)")
        logger.info("Agent framework: %s", agent.framework_name)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_run_examples())
