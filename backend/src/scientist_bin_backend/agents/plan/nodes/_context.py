"""Shared upstream context builder for plan agent nodes.

Consolidates context from the central agent's task_analysis and the
analyst agent's data_profile / analysis_report into a single text block
that can be injected into prompts.
"""

from __future__ import annotations

import json


def build_upstream_context(state: dict) -> str:
    """Build a formatted context string from upstream agent outputs.

    Combines task_analysis (from central), data_profile, analysis_report,
    and problem_type (from analyst) into a prompt-ready text block.
    """
    parts: list[str] = []

    # Task analysis from central agent
    task_analysis = state.get("task_analysis")
    if task_analysis:
        parts.append("== Pre-Analysis (from central orchestrator) ==")
        parts.append(f"Task type: {task_analysis.get('task_type', 'unknown')}")
        subtype = task_analysis.get("task_subtype")
        if subtype:
            parts.append(f"Subtype: {subtype}")
        parts.append(f"Complexity: {task_analysis.get('complexity_estimate', 'unknown')}")
        considerations = task_analysis.get("key_considerations", [])
        if considerations:
            parts.append(f"Key considerations: {', '.join(considerations)}")
        approach = task_analysis.get("recommended_approach")
        if approach:
            parts.append(f"Recommended approach: {approach}")
        chars = task_analysis.get("data_characteristics", {})
        if chars:
            parts.append(f"Estimated features: {chars.get('estimated_features', 'unknown')}")
            parts.append(f"Estimated samples: {chars.get('estimated_samples', 'unknown')}")

    # Data profile from analyst agent (real data characteristics)
    data_profile = state.get("data_profile")
    if data_profile:
        parts.append("")
        parts.append("== Actual Data Profile (from analyst agent) ==")
        parts.append(f"Shape: {data_profile.get('shape', 'unknown')}")
        parts.append(f"Columns: {data_profile.get('column_names', [])}")
        parts.append(f"Numeric columns: {data_profile.get('numeric_columns', [])}")
        parts.append(f"Categorical columns: {data_profile.get('categorical_columns', [])}")
        parts.append(f"Target column: {data_profile.get('target_column', 'unknown')}")
        missing = data_profile.get("missing_counts", {})
        if missing:
            parts.append(f"Missing values: {json.dumps(missing)}")
        class_dist = data_profile.get("class_distribution")
        if class_dist:
            parts.append(f"Class distribution: {json.dumps(class_dist)}")
        issues = data_profile.get("data_quality_issues", [])
        if issues:
            parts.append(f"Quality issues: {issues}")

    # Analysis report from analyst (truncated for prompt context)
    analysis_report = state.get("analysis_report")
    if analysis_report:
        parts.append("")
        parts.append("== Data Analysis Report (from analyst agent) ==")
        parts.append(analysis_report[:3000])

    # Confirmed problem type
    problem_type = state.get("problem_type")
    if problem_type:
        parts.append(f"\nConfirmed problem type: {problem_type}")

    return "\n".join(parts) if parts else "No upstream analysis available."
