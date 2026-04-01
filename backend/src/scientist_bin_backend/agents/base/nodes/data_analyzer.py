"""Data analysis nodes: classify_problem and analyze_data.

classify_problem: 1 LLM call to determine problem type.
analyze_data: 0 LLM calls — deterministic EDA via sandbox execution.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.base.prompts.templates import CLASSIFY_PROBLEM_PROMPT
from scientist_bin_backend.agents.base.schemas import ProblemClassification
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig
from scientist_bin_backend.execution.templates import EDA_TEMPLATE
from scientist_bin_backend.utils.llm import get_chat_model

logger = logging.getLogger(__name__)


async def classify_problem(state: dict) -> dict:
    """Determine the ML problem type from objective and data sample.

    Uses 1 LLM call with structured output.
    """
    objective = state["objective"]
    data_description = state.get("data_description", "")
    data_file_path = state.get("data_file_path")

    # Try to read a small data sample for better classification
    data_sample = ""
    if data_file_path and Path(data_file_path).exists():
        try:
            import pandas as pd

            df = pd.read_csv(data_file_path, nrows=5)
            cols = list(df.columns)
            data_sample = f"First 5 rows of the dataset:\n{df.to_string()}\n\nColumns: {cols}"
        except Exception:
            data_sample = "(Could not read data sample)"

    llm = get_chat_model()
    structured_llm = llm.with_structured_output(ProblemClassification)
    prompt = CLASSIFY_PROBLEM_PROMPT.format(
        objective=objective,
        data_description=data_description,
        data_sample=data_sample,
    )
    result: ProblemClassification = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "classify",
                    "problem_type": result.problem_type,
                    "message": f"Classified as {result.problem_type}",
                },
            ),
        )

    return {
        "problem_type": result.problem_type,
        "phase": "eda",
        "progress_events": [
            {
                "event_type": "phase_change",
                "data": {
                    "phase": "classify_problem",
                    "problem_type": result.problem_type,
                    "reasoning": result.reasoning,
                    "target_column": result.target_column_guess,
                },
            }
        ],
        "messages": [
            HumanMessage(
                content=f"Problem classified as {result.problem_type}. "
                f"Target column: {result.target_column_guess}. "
                f"Metrics: {', '.join(result.suggested_metrics)}"
            )
        ],
    }


async def analyze_data(state: dict) -> dict:
    """Perform automated EDA by executing a deterministic template script.

    Uses 0 LLM calls — all analysis is done by pandas in a subprocess.
    """
    experiment_id = state.get("experiment_id")
    data_file_path = state.get("data_file_path")
    if not data_file_path:
        return {
            "data_profile": None,
            "phase": "planning",
            "progress_events": [
                {
                    "event_type": "phase_change",
                    "data": {"phase": "eda", "message": "No data file provided, skipping EDA"},
                }
            ],
            "messages": [HumanMessage(content="No data file provided. Skipping EDA.")],
        }

    problem_type = state.get("problem_type", "classification")

    # Determine target column from classification result or data description
    target_column = None
    # Check if classify_problem provided a guess via messages
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "content") and "Target column:" in msg.content:
            # Extract target column from message
            try:
                target_column = msg.content.split("Target column:")[1].split(".")[0].strip()
                if target_column.lower() == "none":
                    target_column = None
            except (IndexError, AttributeError):
                pass
            break

    # Generate and execute EDA script
    eda_code = EDA_TEMPLATE.format(
        data_file=str(Path(data_file_path).resolve()),
        target_column=target_column,
        problem_type=problem_type,
    )

    experiment_id = state.get("experiment_id", "eda")
    runner = CodeRunner()
    result = await runner.execute(
        RunConfig(
            experiment_id=experiment_id,
            code=eda_code,
            run_id="eda",
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
                "data_profile": data_profile,
                "eda_code": eda_code,
                "eda_output": result.stdout[:2000],
                "phase": "planning",
                "progress_events": [
                    {
                        "event_type": "phase_change",
                        "data": {"phase": "eda", "message": summary},
                    }
                ],
                "messages": [HumanMessage(content=f"EDA completed:\n{summary}")],
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse EDA output as JSON: %s", result.stdout[:200])

    # EDA failed — provide what we can
    error_msg = result.stderr[:500] if result.stderr else "Unknown EDA error"
    return {
        "data_profile": None,
        "eda_code": eda_code,
        "eda_output": error_msg,
        "phase": "planning",
        "progress_events": [
            {
                "event_type": "error",
                "data": {"phase": "eda", "message": f"EDA failed: {error_msg}"},
            }
        ],
        "messages": [
            HumanMessage(
                content=f"EDA encountered issues: {error_msg}. Proceeding with available info."
            )
        ],
    }
