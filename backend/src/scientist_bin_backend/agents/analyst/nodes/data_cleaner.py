"""Data cleaning node: LLM-generated cleaning script executed in subprocess.

Uses 1 LLM call to generate a cleaning script, then executes it via CodeRunner.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.analyst.prompts import CLEANING_PROMPT
from scientist_bin_backend.agents.analyst.states import AnalystState
from scientist_bin_backend.agents.analyst.utils import read_data_sample, resolve_run_subdir
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig
from scientist_bin_backend.execution.sandbox import get_framework_python
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model

logger = logging.getLogger(__name__)


def _resolve_output_dir(experiment_id: str) -> Path:
    return resolve_run_subdir(experiment_id, "data")


async def clean_data(state: AnalystState) -> dict:
    """Generate and execute a data cleaning script.

    Uses the LLM to produce a self-contained Python cleaning script based on
    the data profile, then executes it in a sandboxed subprocess.

    Returns partial state with cleaning_code, cleaning_output, and cleaned_data_path.
    """
    experiment_id = state.get("experiment_id", "analyst")
    data_file_path = state.get("data_file_path")
    data_profile = state.get("data_profile")
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "classification")

    if not data_file_path:
        return {
            "cleaning_code": None,
            "cleaning_output": None,
            "cleaned_data_path": None,
            "messages": [HumanMessage(content="No data file provided, skipping cleaning.")],
        }

    # --- Emit phase start ---
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "cleaning", "message": "Starting data cleaning"},
            ),
        )

    # --- Prepare output path ---
    output_dir = _resolve_output_dir(experiment_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = output_dir / "cleaned.csv"

    # --- Build cleaning prompt from data profile + upstream context ---
    profile = data_profile or {}
    task_analysis = state.get("task_analysis") or {}
    selected_framework = state.get("selected_framework") or "sklearn"
    data_sample = read_data_sample(data_file_path)

    prompt = CLEANING_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        data_file_path=str(Path(data_file_path).resolve()),
        output_path=str(cleaned_path.resolve()),
        selected_framework=selected_framework,
        shape=profile.get("shape", "unknown"),
        columns=profile.get("column_names", []),
        dtypes=profile.get("dtypes", {}),
        missing_counts=profile.get("missing_counts", {}),
        numeric_columns=profile.get("numeric_columns", []),
        categorical_columns=profile.get("categorical_columns", []),
        target_column=profile.get("target_column", "unknown"),
        data_quality_issues=profile.get("data_quality_issues", []),
        key_considerations=", ".join(task_analysis.get("key_considerations", [])) or "None",
        recommended_approach=task_analysis.get("recommended_approach", "None"),
        complexity_estimate=task_analysis.get("complexity_estimate", "unknown"),
        data_sample=data_sample,
    )

    # --- LLM call to generate cleaning code ---
    llm = get_agent_model("analyst")
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    raw_content = extract_text_content(response.content)

    # Extract code from markdown fences if present
    cleaning_code = _extract_code_block(raw_content)

    # --- Execute the cleaning script ---
    runner = CodeRunner(python_path=get_framework_python("analyst"))
    result = await runner.execute(
        RunConfig(
            experiment_id=experiment_id,
            code=cleaning_code,
            run_id="analyst_clean",
            timeout_seconds=120,
        )
    )

    if result.success:
        # Parse the cleaning summary from stdout
        cleaning_summary = result.stdout.strip()
        try:
            summary_data = json.loads(cleaning_summary)
            rows_before = summary_data.get("rows_before", "?")
            rows_after = summary_data.get("rows_after", "?")
            dupes = summary_data.get("duplicates_removed", 0)
            cols_dropped = len(summary_data.get("columns_dropped", []))
            summary_msg = (
                f"Cleaning completed: {rows_before} -> {rows_after} rows, "
                f"{dupes} duplicates removed, {cols_dropped} columns dropped"
            )
        except (json.JSONDecodeError, AttributeError):
            summary_msg = f"Cleaning completed. Output: {cleaning_summary[:300]}"

        if experiment_id:
            await event_bus.emit(
                experiment_id,
                ExperimentEvent(
                    event_type="phase_change",
                    data={"phase": "cleaning", "message": summary_msg},
                ),
            )

        return {
            "cleaning_code": cleaning_code,
            "cleaning_output": cleaning_summary,
            "cleaned_data_path": str(cleaned_path.resolve()),
            "messages": [HumanMessage(content=summary_msg)],
        }

    # Cleaning failed
    error_msg = result.stderr[:500] if result.stderr else "Unknown cleaning error"
    logger.warning("Data cleaning failed: %s", error_msg)

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="error",
                data={"phase": "cleaning", "message": f"Cleaning failed: {error_msg}"},
            ),
        )

    # Fall back to using the original data file as the "cleaned" path
    return {
        "cleaning_code": cleaning_code,
        "cleaning_output": error_msg,
        "cleaned_data_path": str(Path(data_file_path).resolve()),
        "error": f"Cleaning failed: {error_msg}",
        "messages": [
            HumanMessage(content=f"Cleaning failed: {error_msg}. Falling back to original data.")
        ],
    }


def _extract_code_block(text: str) -> str:
    """Extract Python code from markdown fenced code blocks.

    If the text contains ```python ... ``` fences, extract the content.
    Otherwise return the text as-is.
    """
    if "```python" in text:
        parts = text.split("```python", 1)
        if len(parts) > 1:
            code_part = parts[1]
            if "```" in code_part:
                return code_part.split("```", 1)[0].strip()
            return code_part.strip()
    if "```" in text:
        parts = text.split("```", 2)
        if len(parts) >= 3:
            return parts[1].strip()
    return text.strip()
