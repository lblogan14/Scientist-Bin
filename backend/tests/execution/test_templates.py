"""Tests for execution/templates.py."""

from __future__ import annotations

from scientist_bin_backend.execution.templates import (
    COMPLETION_SENTINEL,
    EDA_TEMPLATE,
    METRICS_REPORTER_HARNESS,
)


def test_metrics_reporter_harness_defines_report_metric():
    """Harness defines the report_metric function."""
    assert "def report_metric" in METRICS_REPORTER_HARNESS


def test_metrics_reporter_harness_is_valid_python():
    """Harness is syntactically valid Python."""
    compile(METRICS_REPORTER_HARNESS, "<test-harness>", "exec")


def test_completion_sentinel_value():
    """Completion sentinel has the expected value."""
    assert COMPLETION_SENTINEL == "===RESULTS==="


def test_eda_template_is_formattable():
    """EDA template can be formatted with expected parameters."""
    result = EDA_TEMPLATE.format(
        data_file="test.csv",
        target_column="target",
        problem_type="classification",
    )
    assert "test.csv" in result
    assert "target" in result
    assert "classification" in result


def test_eda_template_uses_pandas():
    """EDA template imports pandas."""
    result = EDA_TEMPLATE.format(
        data_file="data.csv",
        target_column="y",
        problem_type="regression",
    )
    assert "import pandas" in result


def test_eda_template_is_valid_python():
    """Formatted EDA template is syntactically valid Python."""
    result = EDA_TEMPLATE.format(
        data_file="data.csv",
        target_column="y",
        problem_type="classification",
    )
    compile(result, "<test-eda>", "exec")
