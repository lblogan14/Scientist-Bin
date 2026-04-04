"""High-level wrapper around the campaign orchestrator graph."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from scientist_bin_backend.agents.campaign.graph import build_campaign_graph
from scientist_bin_backend.agents.campaign.schemas import CampaignResult

logger = logging.getLogger(__name__)


class CampaignAgent:
    """Autonomous research campaign that iteratively runs the inner ML pipeline.

    Generates hypotheses, executes experiments via the 5-agent pipeline,
    extracts insights, and loops until the budget is exhausted or results
    converge.
    """

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_campaign_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        data_file_path: str,
        data_description: str = "",
        budget_max_iterations: int = 10,
        budget_time_limit_seconds: float = 14400.0,
    ) -> CampaignResult:
        """Execute the campaign loop and return a structured result.

        Args:
            objective: High-level research objective.
            data_file_path: Absolute path to the dataset file.
            data_description: Free-text description of the dataset.
            budget_max_iterations: Maximum number of experiments to run.
            budget_time_limit_seconds: Wall-clock time limit (default 4 hours).

        Returns:
            :class:`CampaignResult` with summary of all experiments.
        """
        start = time.time()
        thread_id = uuid.uuid4().hex[:12]

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_file_path": data_file_path,
            "data_description": data_description,
            "budget_max_iterations": budget_max_iterations,
            "budget_time_limit_seconds": budget_time_limit_seconds,
            "current_iteration": 0,
            "start_time": start,
            "hypotheses": [],
            "completed_experiments": [],
            "findings_summary": "",
            "best_result": {},
            "campaign_status": "running",
        }

        config = {"configurable": {"thread_id": thread_id}}
        final_state = await self.graph.ainvoke(initial_state, config=config)

        elapsed = time.time() - start
        completed = final_state.get("completed_experiments", [])
        best = final_state.get("best_result", {})

        logger.info(
            "Campaign finished: %d experiments in %.1fs",
            len(completed),
            elapsed,
        )

        return CampaignResult(
            total_iterations=len(completed),
            total_time_seconds=elapsed,
            best_experiment_id=best.get("experiment_id"),
            best_algorithm=best.get("algorithm"),
            best_metrics=best.get("metrics", {}),
            hypotheses_tested=len(completed),
            key_findings=_extract_key_findings(final_state.get("findings_summary", "")),
        )


def _extract_key_findings(findings_summary: str) -> list[str]:
    """Parse the findings memory into a list of individual findings.

    Splits on numbered list patterns (``1. ...``, ``2. ...``) or newlines,
    returning non-empty lines.
    """
    if not findings_summary:
        return []

    import re

    # Try splitting on numbered-list patterns first
    items = re.split(r"\n\d+\.\s+", findings_summary)
    # Fall back to plain newline splitting
    if len(items) <= 1:
        items = findings_summary.strip().split("\n")

    return [item.strip() for item in items if item.strip()]


# ---------------------------------------------------------------------------
# Standalone validation
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "objective": "Find the best classifier for iris species",
        "data_file_path": "data/iris_data/Iris.csv",
        "data_description": (
            "150 samples, 4 numeric features (sepal_length, sepal_width, "
            "petal_length, petal_width), 3 balanced classes."
        ),
        "budget_max_iterations": 2,
        "budget_time_limit_seconds": 300.0,
    },
    {
        "objective": "Predict house sale prices with minimal RMSE",
        "data_file_path": "data/housing/train.csv",
        "data_description": (
            "1,460 samples, 80 features (mix of numeric and categorical), "
            "target is SalePrice. Some columns have up to 20% missing values."
        ),
        "budget_max_iterations": 3,
        "budget_time_limit_seconds": 600.0,
    },
]


async def _run_examples() -> None:
    """Run the campaign agent on each example and log results."""
    agent = CampaignAgent()
    for i, example in enumerate(EXAMPLES, 1):
        logger.info("=" * 60)
        logger.info("Example %d: %s", i, example["objective"])
        logger.info("=" * 60)
        result = await agent.run(**example)
        logger.info("Total iterations: %d", result.total_iterations)
        logger.info("Total time: %.1fs", result.total_time_seconds)
        logger.info("Best algorithm: %s", result.best_algorithm)
        logger.info("Best metrics: %s", result.best_metrics)
        logger.info("Key findings: %s", result.key_findings)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_run_examples())
