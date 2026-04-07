"""Data profiling node: validate/classify problem type + deterministic EDA.

When upstream TaskAnalysis is available, validates the classification against
actual data (1 LLM call). Otherwise falls back to classifying from scratch.
Always runs deterministic EDA via subprocess.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.analyst.prompts import (
    CLASSIFY_PROBLEM_PROMPT,
    VALIDATE_CLASSIFICATION_PROMPT,
)
from scientist_bin_backend.agents.analyst.schemas import ValidatedClassification
from scientist_bin_backend.agents.analyst.states import AnalystState
from scientist_bin_backend.agents.analyst.utils import read_data_sample
from scientist_bin_backend.agents.base.schemas import ProblemClassification
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig
from scientist_bin_backend.execution.sandbox import get_framework_python
from scientist_bin_backend.execution.templates import EDA_TEMPLATE
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


def _read_data_sample(data_file_path: str, n_lines: int = 6) -> str:
    """Read the first n lines of a data file for LLM context (with prefix)."""
    sample = read_data_sample(data_file_path, n_lines)
    if sample.startswith("("):
        return sample
    return f"First rows of the dataset:\n{sample}"


async def _validate_classification(
    llm,
    objective: str,
    task_analysis: dict,
    data_sample: str,
) -> tuple[str, str | None, str, str, list[str], str | None]:
    """Validate upstream classification using actual data.

    Returns (problem_type, target_column, confidence, reasoning, metrics, disagreement).
    """
    data_chars = task_analysis.get("data_characteristics", {})

    structured_llm = llm.with_structured_output(ValidatedClassification)
    prompt = VALIDATE_CLASSIFICATION_PROMPT.format(
        objective=objective,
        upstream_task_type=task_analysis.get("task_type", "unknown"),
        upstream_task_subtype=task_analysis.get("task_subtype", ""),
        upstream_key_considerations=", ".join(task_analysis.get("key_considerations", [])),
        upstream_recommended_approach=task_analysis.get("recommended_approach", ""),
        upstream_data_characteristics=str(data_chars),
        data_sample=data_sample,
    )
    result: ValidatedClassification = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    return (
        result.problem_type,
        result.target_column_guess,
        result.confidence,
        result.reasoning,
        result.suggested_metrics,
        result.upstream_disagreement,
    )


async def _classify_from_scratch(
    llm,
    objective: str,
    data_sample: str,
) -> tuple[str, str | None, str, str, list[str], str | None]:
    """Classify problem type from scratch (standalone fallback).

    Returns (problem_type, target_column, confidence, reasoning, metrics, disagreement).
    """
    structured_llm = llm.with_structured_output(ProblemClassification)
    prompt = CLASSIFY_PROBLEM_PROMPT.format(
        objective=objective,
        data_sample=data_sample,
    )
    result: ProblemClassification = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    return (
        result.problem_type,
        result.target_column_guess,
        "confirmed",  # No upstream to disagree with
        result.reasoning,
        result.suggested_metrics,
        None,
    )


async def profile_data(state: AnalystState) -> dict:
    """Classify/validate the ML problem and run deterministic EDA on the dataset.

    1. Reads a small data sample for context.
    2. If task_analysis is present: validate upstream classification (structured output).
       Otherwise: classify from scratch (fallback for standalone CLI).
    3. Runs the EDA template script in a subprocess to build a data profile.

    Returns partial state with problem_type, classification_confidence,
    classification_reasoning, data_profile, and messages.
    """
    experiment_id = state.get("experiment_id", "analyst")
    objective = state["objective"]
    data_file_path = state.get("data_file_path")
    task_analysis = state.get("task_analysis")

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
        data_sample = _read_data_sample(data_file_path)

    # --- Step 1: LLM classification (validate or classify from scratch) ---
    llm = get_agent_model("analyst")

    if task_analysis:
        logger.info("Validating upstream classification against actual data")
        (
            problem_type,
            target_column,
            confidence,
            reasoning,
            metrics,
            disagreement,
        ) = await _validate_classification(llm, objective, task_analysis, data_sample)
    else:
        logger.info("No upstream task_analysis; classifying from scratch")
        (
            problem_type,
            target_column,
            confidence,
            reasoning,
            metrics,
            disagreement,
        ) = await _classify_from_scratch(llm, objective, data_sample)

    classification_msg = f"Classified as {problem_type} (confidence: {confidence})"
    if disagreement:
        classification_msg += f" — disagreement: {disagreement}"

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={
                    "phase": "classify",
                    "problem_type": problem_type,
                    "confidence": confidence,
                    "message": classification_msg,
                },
            ),
        )

    # --- Step 2: Deterministic EDA via subprocess ---
    if not data_file_path:
        return {
            "problem_type": problem_type,
            "classification_confidence": confidence,
            "classification_reasoning": reasoning,
            "data_profile": None,
            "messages": [
                HumanMessage(
                    content=f"{classification_msg}. "
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

    runner = CodeRunner(python_path=get_framework_python("analyst"))
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
                "classification_confidence": confidence,
                "classification_reasoning": reasoning,
                "data_profile": data_profile,
                "messages": [
                    HumanMessage(
                        content=f"{classification_msg}. "
                        f"Target column: {target_column}. "
                        f"Metrics: {', '.join(metrics)}\n\n"
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
        "classification_confidence": confidence,
        "classification_reasoning": reasoning,
        "data_profile": None,
        "error": f"EDA failed: {error_msg}",
        "messages": [
            HumanMessage(
                content=f"{classification_msg}. "
                f"EDA encountered issues: {error_msg}. Proceeding with available info."
            )
        ],
    }
