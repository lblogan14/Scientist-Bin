"""Report writer node: LLM-generated analysis report.

Uses 1 LLM call to produce a comprehensive Markdown report.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.analyst.prompts.templates import REPORT_PROMPT
from scientist_bin_backend.agents.analyst.states import AnalystState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model

logger = logging.getLogger(__name__)


def _resolve_output_dir(experiment_id: str) -> Path:
    """Resolve the data output directory for an experiment."""
    backend_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    return backend_root / "outputs" / "runs" / experiment_id / "data"


def _format_profile(data_profile: dict | None) -> str:
    """Format the data profile dict into a readable string."""
    if not data_profile:
        return "No data profile available."

    lines = []
    lines.append(f"Shape: {data_profile.get('shape', 'unknown')}")
    lines.append(f"Columns: {data_profile.get('column_names', [])}")
    lines.append(f"Dtypes: {data_profile.get('dtypes', {})}")
    lines.append(f"Numeric columns: {data_profile.get('numeric_columns', [])}")
    lines.append(f"Categorical columns: {data_profile.get('categorical_columns', [])}")
    lines.append(f"Target column: {data_profile.get('target_column', 'unknown')}")

    missing = data_profile.get("missing_counts", {})
    if missing:
        lines.append(f"Missing values: {missing}")

    issues = data_profile.get("data_quality_issues", [])
    if issues:
        lines.append(f"Quality issues: {issues}")

    class_dist = data_profile.get("class_distribution")
    if class_dist:
        lines.append(f"Class distribution: {class_dist}")

    target_stats = data_profile.get("target_stats")
    if target_stats:
        lines.append(f"Target statistics: {target_stats}")

    summary = data_profile.get("statistics_summary")
    if summary:
        lines.append(f"\n{summary}")

    return "\n".join(lines)


def _format_cleaning_summary(cleaning_output: str | None) -> str:
    """Format the cleaning output into a readable string."""
    if not cleaning_output:
        return "No cleaning was performed."

    try:
        summary = json.loads(cleaning_output)
        lines = []
        lines.append(f"Rows: {summary.get('rows_before', '?')} -> {summary.get('rows_after', '?')}")
        lines.append(f"Duplicates removed: {summary.get('duplicates_removed', 0)}")

        dropped = summary.get("columns_dropped", [])
        if dropped:
            lines.append(f"Columns dropped: {dropped}")

        filled = summary.get("missing_filled", {})
        if filled:
            lines.append(f"Missing value strategies: {filled}")

        encoded = summary.get("encoding_applied", [])
        if encoded:
            lines.append(f"Encoding applied to: {encoded}")

        return "\n".join(lines)
    except (json.JSONDecodeError, AttributeError):
        return cleaning_output[:500]


def _format_split_summary(split_output: str | None) -> str:
    """Format the split output into a readable string."""
    if not split_output:
        return "No split was performed."

    try:
        stats = json.loads(split_output)
        lines = []
        lines.append(
            f"Train: {stats.get('train_samples', '?')} samples ({stats.get('train_ratio', 0):.1%})"
        )
        lines.append(
            f"Validation: {stats.get('val_samples', '?')} samples ({stats.get('val_ratio', 0):.1%})"
        )
        lines.append(
            f"Test: {stats.get('test_samples', '?')} samples ({stats.get('test_ratio', 0):.1%})"
        )
        lines.append(f"Stratified: {stats.get('stratified', False)}")
        return "\n".join(lines)
    except (json.JSONDecodeError, AttributeError):
        return split_output[:500]


async def write_report(state: AnalystState) -> dict:
    """Generate a comprehensive Markdown analysis report.

    Uses 1 LLM call to synthesize profiling, cleaning, and splitting results
    into a human-readable report. Saves the report to disk.

    Returns partial state with analysis_report.
    """
    experiment_id = state.get("experiment_id", "analyst")
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "classification")
    data_profile = state.get("data_profile")
    cleaning_output = state.get("cleaning_output")
    split_output = state.get("split_output")

    # --- Emit phase start ---
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "reporting", "message": "Generating analysis report"},
            ),
        )

    # --- Build the report prompt ---
    prompt = REPORT_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        data_profile=_format_profile(data_profile),
        cleaning_summary=_format_cleaning_summary(cleaning_output),
        split_summary=_format_split_summary(split_output),
    )

    # --- LLM call ---
    llm = get_agent_model("analyst")
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    report_text = extract_text_content(response.content)

    # --- Save report to disk ---
    output_dir = _resolve_output_dir(experiment_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "analysis_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    logger.info("Analysis report saved to %s", report_path)

    # --- Emit completion ---
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="analysis_completed",
                data={
                    "phase": "reporting",
                    "message": "Analysis report generated",
                    "report_path": str(report_path),
                },
            ),
        )

    return {
        "analysis_report": report_text,
        "messages": [HumanMessage(content="Analysis report generated successfully.")],
    }
