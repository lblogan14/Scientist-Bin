"""Report generator node — produces a comprehensive markdown report.

Uses one LLM call with structured output to generate a SummaryReport,
then assembles it into a full markdown document and saves it to disk.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.summary.prompts import (
    REPORT_GENERATION_PROMPT,
)
from scientist_bin_backend.agents.summary.schemas import SummaryReport
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)

# Resolve output directory relative to the backend root
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
_OUTPUTS_DIR = _BACKEND_DIR / "outputs"


def _assemble_markdown(report: SummaryReport) -> str:
    """Assemble a SummaryReport into a full markdown document."""
    sections: list[str] = []

    sections.append(f"# {report.title}\n")

    sections.append("## Dataset Overview\n")
    sections.append(f"{report.dataset_overview}\n")

    sections.append("## Methodology\n")
    sections.append(f"{report.methodology}\n")

    sections.append("## Model Comparison\n")
    sections.append(f"{report.model_comparison_table}\n")

    sections.append("## Best Model Analysis\n")
    sections.append(f"{report.best_model_analysis}\n")

    sections.append("## Hyperparameter Analysis\n")
    sections.append(f"{report.hyperparameter_analysis}\n")

    sections.append("## Conclusions\n")
    sections.append(f"{report.conclusions}\n")

    sections.append("## Recommendations\n")
    for rec in report.recommendations:
        sections.append(f"- {rec}")
    sections.append("")

    sections.append("## Reproducibility Notes\n")
    sections.append(f"{report.reproducibility_notes}\n")

    return "\n".join(sections)


async def generate_report(state: dict) -> dict:
    """Generate a comprehensive markdown report from all experiment context.

    Uses all available context — objective, problem type, execution plan,
    analysis report, model comparison, and best model info — to produce
    a professional data-science report. Saves the report to disk under
    ``outputs/runs/{experiment_id}/summary/report.md``.
    """
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "unknown")
    execution_plan = state.get("execution_plan")
    analysis_report = state.get("analysis_report")
    model_comparison = state.get("model_comparison", [])
    best_model = state.get("best_model", "N/A")
    best_hyperparameters = state.get("best_hyperparameters", {})
    best_metrics = state.get("best_metrics", {})
    sklearn_results = state.get("sklearn_results")
    experiment_id = state.get("experiment_id")

    # Format inputs for the prompt
    execution_plan_str = (
        json.dumps(execution_plan, indent=2, default=str)
        if execution_plan
        else "No execution plan available."
    )
    analysis_report_str = analysis_report or "No analysis report available."
    comparison_str = json.dumps(model_comparison, indent=2, default=str)
    hyperparams_str = json.dumps(best_hyperparameters, indent=2, default=str)
    metrics_str = json.dumps(best_metrics, indent=2, default=str)
    sklearn_results_str = (
        json.dumps(sklearn_results, indent=2, default=str)
        if sklearn_results
        else "No sklearn results available."
    )

    # Build the prompt
    prompt = REPORT_GENERATION_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        execution_plan=execution_plan_str,
        analysis_report=analysis_report_str,
        model_comparison=comparison_str,
        best_model=best_model,
        best_hyperparameters=hyperparams_str,
        best_metrics=metrics_str,
        sklearn_results=sklearn_results_str,
    )

    # LLM call with structured output
    llm = get_agent_model("summary")
    structured_llm = llm.with_structured_output(SummaryReport)
    report: SummaryReport = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Assemble the full markdown document
    full_markdown = _assemble_markdown(report)

    # Save the report to disk
    if experiment_id:
        report_dir = _OUTPUTS_DIR / "runs" / experiment_id / "summary"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "report.md"
        report_path.write_text(full_markdown, encoding="utf-8")
        logger.info("Summary report saved to %s", report_path)

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
        "summary_report": full_markdown,
        "messages": [
            HumanMessage(
                content=f"Summary report generated for experiment {experiment_id or 'unknown'}."
            )
        ],
    }
