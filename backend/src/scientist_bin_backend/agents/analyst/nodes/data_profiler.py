"""Data profiling node: classify problem type + deterministic EDA.

Combines the classify_problem and analyze_data steps into a single node.
Uses 1 LLM call (for classification) + 1 subprocess (for EDA).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.analyst.prompts import CLASSIFY_PROBLEM_PROMPT
from scientist_bin_backend.agents.analyst.states import AnalystState
from scientist_bin_backend.agents.base.schemas import ProblemClassification
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig
from scientist_bin_backend.execution.templates import EDA_TEMPLATE
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


async def profile_data(state: AnalystState) -> dict:
    """Classify the ML problem and run deterministic EDA on the dataset.

    1. Reads a small data sample for context.
    2. LLM call to classify the problem type (structured output).
    3. Runs the EDA template script in a subprocess to build a data profile.

    Returns partial state with problem_type, data_profile, and messages.
    """
    experiment_id = state.get("experiment_id", "analyst")
    objective = state["objective"]
    data_file_path = state.get("data_file_path")

    # --- Emit phase start ---
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "profiling", "message": "Starting data profiling"},
            ),
        )

    # --- Read a small data sample for classification context ---
    data_sample = ""
    if data_file_path and Path(data_file_path).exists():
        try:
            # Read raw lines to avoid importing pandas in the main process
            with open(data_file_path, encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(6)]  # header + 5 rows
            data_sample = f"First rows of the dataset:\n{''.join(lines)}"
        except Exception:
            data_sample = "(Could not read data sample)"

    # --- Step 1: LLM classification ---
    llm = get_agent_model("analyst")
    structured_llm = llm.with_structured_output(ProblemClassification)
    prompt = CLASSIFY_PROBLEM_PROMPT.format(
        objective=objective,
        data_sample=data_sample,
    )
    classification: ProblemClassification = await structured_llm.ainvoke(
        [HumanMessage(content=prompt)]
    )

    problem_type = classification.problem_type
    target_column = classification.target_column_guess

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "classify",
                    "problem_type": problem_type,
                    "message": f"Classified as {problem_type}",
                },
            ),
        )

    # --- Step 2: Deterministic EDA via subprocess ---
    if not data_file_path:
        return {
            "problem_type": problem_type,
            "data_profile": None,
            "messages": [
                HumanMessage(
                    content=f"Problem classified as {problem_type}. "
                    f"Target column: {target_column}. "
                    f"No data file provided, skipping EDA."
                )
            ],
        }

    eda_code = EDA_TEMPLATE.format(
        data_file=str(Path(data_file_path).resolve()),
        target_column=target_column,
        problem_type=problem_type,
    )

    runner = CodeRunner()
    result = await runner.execute(
        RunConfig(
            experiment_id=experiment_id,
            code=eda_code,
            run_id="analyst_eda",
            timeout_seconds=60,
        )
    )

    if result.success:
        try:
            data_profile = json.loads(result.stdout.strip())
            summary = data_profile.get("statistics_summary", "EDA completed")

            if experiment_id:
                await event_bus.emit(
                    experiment_id,
                    ExperimentEvent(
                        event_type="phase_change",
                        data={"phase": "eda", "message": summary},
                    ),
                )

            return {
                "problem_type": problem_type,
                "data_profile": data_profile,
                "messages": [
                    HumanMessage(
                        content=f"Problem classified as {problem_type}. "
                        f"Target column: {target_column}. "
                        f"Metrics: {', '.join(classification.suggested_metrics)}\n\n"
                        f"EDA completed:\n{summary}"
                    )
                ],
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse EDA output as JSON: %s", result.stdout[:200])

    # EDA failed -- return classification results with error info
    error_msg = result.stderr[:500] if result.stderr else "Unknown EDA error"
    logger.warning("EDA execution failed: %s", error_msg)

    return {
        "problem_type": problem_type,
        "data_profile": None,
        "error": f"EDA failed: {error_msg}",
        "messages": [
            HumanMessage(
                content=f"Problem classified as {problem_type}. "
                f"EDA encountered issues: {error_msg}. Proceeding with available info."
            )
        ],
    }
