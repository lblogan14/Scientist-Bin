"""Report generator node — produces a comprehensive markdown report.

Uses one LLM call with structured output to generate a SummaryReport.
The prompt includes pre-computed diagnostics so the LLM focuses on
narrative and interpretation, not computation.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.summary.prompts import REPORT_GENERATION_PROMPT
from scientist_bin_backend.agents.summary.schemas import SummaryReport
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Markdown assembly
# ---------------------------------------------------------------------------


def _assemble_markdown(report: SummaryReport) -> str:
    """Assemble a SummaryReport into a full markdown document."""
    sections: list[str] = []

    sections.append(f"# {report.title}\n")

    sections.append("## Executive Summary\n")
    sections.append(f"{report.executive_summary}\n")

    sections.append("## Dataset Overview\n")
    sections.append(f"{report.dataset_overview}\n")

    sections.append("## Methodology\n")
    sections.append(f"{report.methodology}\n")

    sections.append("## Model Comparison\n")
    sections.append(f"{report.model_comparison_table}\n")

    sections.append("## Cross-Validation Stability Analysis\n")
    sections.append(f"{report.cv_stability_analysis}\n")

    sections.append("## Best Model Analysis\n")
    sections.append(f"{report.best_model_analysis}\n")

    sections.append("## Feature Importance Analysis\n")
    sections.append(f"{report.feature_importance_analysis}\n")

    sections.append("## Hyperparameter Analysis\n")
    sections.append(f"{report.hyperparameter_analysis}\n")

    sections.append("## Error Analysis\n")
    sections.append(f"{report.error_analysis}\n")

    sections.append("## Conclusions\n")
    sections.append(f"{report.conclusions}\n")

    sections.append("## Recommendations\n")
    for rec in report.recommendations:
        sections.append(f"- {rec}")
    sections.append("")

    sections.append("## Reproducibility Notes\n")
    sections.append(f"{report.reproducibility_notes}\n")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Diagnostics formatting helpers
# ---------------------------------------------------------------------------


def _format_cv_stability(diagnostics: dict) -> str:
    """Format CV stability data for the report prompt."""
    entries = diagnostics.get("cv_stability", [])
    if not entries:
        return "No cross-validation fold data was extracted."

    lines: list[str] = []
    for e in entries:
        lines.append(
            f"- {e['algorithm']} ({e['metric_name']}): "
            f"mean={e['mean']:.4f} +/- {e['std']:.4f}, "
            f"CV coeff={e['cv_coefficient_of_variation']:.4f}, "
            f"range=[{e['min_fold']:.4f}, {e['max_fold']:.4f}]"
        )
    return "\n".join(lines)


def _format_overfit(diagnostics: dict) -> str:
    """Format overfitting analysis for the report prompt."""
    entries = diagnostics.get("overfit_analyses", [])
    if not entries:
        return "No train/val metric pairs found for overfitting analysis."

    lines: list[str] = []
    for e in entries:
        lines.append(
            f"- {e['algorithm']} ({e['metric_name']}): "
            f"train={e['train_value']:.4f}, val={e['val_value']:.4f}, "
            f"gap={e['gap']:.4f} ({e['gap_percentage']:.1f}%), "
            f"risk={e['overfit_risk']}"
        )
    return "\n".join(lines)


def _format_feature_importances(ctx: dict) -> str:
    """Format feature importances for the report prompt."""
    importances = ctx.get("feature_importances", {})
    if not importances:
        return "No feature importances were extracted from the models."

    lines: list[str] = []
    for algo, features in importances.items():
        lines.append(f"Algorithm: {algo}")
        for f in features[:15]:
            lines.append(f"  - {f.get('feature', '?')}: {f.get('importance', 0):.4f}")
    return "\n".join(lines)


def _format_error_data(ctx: dict, problem_type: str) -> str:
    """Format confusion matrices or residual stats for the report prompt."""
    lines: list[str] = []

    if problem_type == "classification":
        matrices = ctx.get("confusion_matrices", {})
        if not matrices:
            return "No confusion matrices were extracted."
        for algo, cm in matrices.items():
            label = "Test set" if algo == "__test__" else algo
            labels = cm.get("labels", [])
            matrix = cm.get("matrix", [])
            lines.append(f"Confusion matrix for {label}:")
            lines.append(f"  Labels: {labels}")
            for row in matrix:
                lines.append(f"  {row}")
    else:
        stats = ctx.get("residual_stats", {})
        if not stats:
            return "No residual statistics were extracted."
        for algo, rs in stats.items():
            label = "Test set" if algo == "__test__" else algo
            lines.append(
                f"Residuals for {label}: "
                f"mean={rs.get('mean_residual', 'N/A')}, "
                f"std={rs.get('std_residual', 'N/A')}, "
                f"max_abs={rs.get('max_abs_residual', 'N/A')}, "
                f"percentiles={rs.get('residual_percentiles', {})}"
            )

    return "\n".join(lines) if lines else "No error analysis data available."


def _format_hyperparam_sensitivity(diagnostics: dict) -> str:
    """Format hyperparameter sensitivity for the report prompt."""
    entries = diagnostics.get("hyperparam_sensitivities", [])
    if not entries:
        return "No hyperparameter search data was extracted."

    lines: list[str] = []
    for e in entries[:10]:
        lines.append(
            f"- {e['algorithm']}.{e['param_name']}: "
            f"score_range={e['score_range']:.4f}, "
            f"best={e['best_value']}, "
            f"values_tried={e['values_tried']}"
        )
    return "\n".join(lines)


def _format_pareto(diagnostics: dict) -> str:
    """Format Pareto-optimal models for the report prompt."""
    pareto = diagnostics.get("pareto_optimal_models", [])
    if not pareto:
        return "Could not compute Pareto frontier."
    return ", ".join(pareto)


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


async def generate_report(state: dict) -> dict:
    """Generate the enriched markdown report. 1 LLM call."""
    objective = state.get("objective", "")
    problem_type = state.get("problem_type", "unknown")
    execution_plan = state.get("execution_plan")
    analysis_report = state.get("analysis_report")
    data_profile = state.get("data_profile")
    model_rankings = state.get("model_rankings", [])
    best_model = state.get("best_model", "N/A")
    best_hyperparameters = state.get("best_hyperparameters", {})
    best_metrics = state.get("best_metrics", {})
    selection_reasoning = state.get("selection_reasoning", "")
    test_metrics = state.get("test_metrics")
    diagnostics = state.get("diagnostics") or {}
    summary_context = state.get("summary_context") or {}
    split_data_paths = state.get("split_data_paths")
    generated_code = state.get("generated_code")

    # Format inputs
    execution_plan_str = (
        json.dumps(execution_plan, indent=2, default=str)
        if execution_plan
        else "No execution plan available."
    )
    analysis_report_str = analysis_report or "No analysis report available."
    data_profile_str = (
        json.dumps(data_profile, indent=2, default=str)
        if data_profile
        else "No data profile available."
    )
    rankings_str = json.dumps(model_rankings, indent=2, default=str)
    hyperparams_str = json.dumps(best_hyperparameters, indent=2, default=str)
    metrics_str = json.dumps(best_metrics, indent=2, default=str)
    test_metrics_str = (
        json.dumps(test_metrics, indent=2, default=str)
        if test_metrics
        else "No test set evaluation was performed."
    )
    split_paths_str = (
        json.dumps(split_data_paths, indent=2, default=str)
        if split_data_paths
        else "Not available."
    )
    code_length = str(len(generated_code)) if generated_code else "N/A"

    prompt = REPORT_GENERATION_PROMPT.format(
        objective=objective,
        problem_type=problem_type,
        execution_plan=execution_plan_str,
        analysis_report=analysis_report_str,
        data_profile=data_profile_str,
        model_rankings=rankings_str,
        best_model=best_model,
        best_hyperparameters=hyperparams_str,
        best_metrics=metrics_str,
        selection_reasoning=selection_reasoning,
        cv_stability_summary=_format_cv_stability(diagnostics),
        overfit_summary=_format_overfit(diagnostics),
        feature_importance_summary=_format_feature_importances(summary_context),
        error_data_summary=_format_error_data(summary_context, problem_type),
        hyperparam_sensitivity_summary=_format_hyperparam_sensitivity(diagnostics),
        pareto_summary=_format_pareto(diagnostics),
        test_metrics=test_metrics_str,
        split_data_paths=split_paths_str,
        code_length=code_length,
    )

    llm = get_agent_model("summary")
    structured_llm = llm.with_structured_output(SummaryReport)
    report: SummaryReport = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    full_markdown = _assemble_markdown(report)

    # Build report_sections for frontend consumption
    report_sections = report.model_dump()
    report_sections["chart_data"] = diagnostics.get("chart_data", {})

    logger.info("Summary report generated (%d characters)", len(full_markdown))

    return {
        "summary_report": full_markdown,
        "report_sections": report_sections,
        "messages": [HumanMessage(content="Summary report generated.")],
    }
