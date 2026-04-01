"""Artifact saver node — saves report and chart data to disk.

Zero LLM calls. Extracted from the former report_generator node for
single-responsibility and testability.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

logger = logging.getLogger(__name__)

# Resolve output directory relative to the backend root
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
_OUTPUTS_DIR = _BACKEND_DIR / "outputs"


async def save_artifacts(state: dict) -> dict:
    """Save the summary report and chart data to disk. Zero LLM calls."""
    experiment_id = state.get("experiment_id")
    summary_report = state.get("summary_report")
    report_sections = state.get("report_sections")
    best_model = state.get("best_model")

    if not experiment_id or not summary_report:
        return {
            "messages": [
                HumanMessage(content="Skipping artifact save: no experiment_id or report.")
            ],
        }

    report_dir = _OUTPUTS_DIR / "runs" / experiment_id / "summary"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Save markdown report
    report_path = report_dir / "report.md"
    report_path.write_text(summary_report, encoding="utf-8")
    logger.info("Summary report saved to %s", report_path)

    # Save structured chart data as JSON for frontend consumption
    if report_sections and report_sections.get("chart_data"):
        chart_path = report_dir / "chart_data.json"
        chart_path.write_text(
            json.dumps(report_sections["chart_data"], indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Chart data saved to %s", chart_path)

    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="summary_completed",
            data={
                "phase": "summary_report",
                "report_path": str(report_path),
                "best_model": best_model,
            },
        ),
    )

    return {
        "messages": [
            HumanMessage(content=f"Summary artifacts saved for experiment {experiment_id}.")
        ],
    }
