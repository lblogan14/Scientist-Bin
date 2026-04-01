"""Tests for the analyst agent schemas and state."""

from __future__ import annotations

from scientist_bin_backend.agents.analyst.schemas import (
    AnalysisReport,
    CleaningAction,
    SplitStatistics,
)
from scientist_bin_backend.agents.analyst.states import AnalystState

# ---------------------------------------------------------------------------
# CleaningAction schema tests
# ---------------------------------------------------------------------------


def test_cleaning_action_required_fields():
    action = CleaningAction(
        action="impute",
        description="Impute missing values with median",
    )
    assert action.action == "impute"
    assert action.column is None
    assert action.description == "Impute missing values with median"


def test_cleaning_action_with_column():
    action = CleaningAction(
        action="drop",
        column="id",
        description="Drop the ID column",
    )
    assert action.column == "id"


# ---------------------------------------------------------------------------
# SplitStatistics schema tests
# ---------------------------------------------------------------------------


def test_split_statistics():
    stats = SplitStatistics(
        train_samples=105,
        val_samples=22,
        test_samples=23,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )
    assert stats.train_samples == 105
    assert stats.val_samples == 22
    assert stats.test_samples == 23
    assert stats.train_ratio == 0.70
    assert stats.val_ratio == 0.15
    assert stats.test_ratio == 0.15


def test_split_statistics_ratios_sum():
    """Sanity check that typical split ratios sum close to 1.0."""
    stats = SplitStatistics(
        train_samples=700,
        val_samples=150,
        test_samples=150,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )
    total = stats.train_ratio + stats.val_ratio + stats.test_ratio
    assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# AnalysisReport schema tests
# ---------------------------------------------------------------------------


def test_analysis_report_required_fields():
    report = AnalysisReport(
        dataset_summary="Iris dataset with 150 samples",
        shape=[150, 5],
    )
    assert report.dataset_summary == "Iris dataset with 150 samples"
    assert report.shape == [150, 5]
    assert report.columns == []
    assert report.data_quality_issues == []
    assert report.cleaning_actions == []
    assert report.split_statistics is None
    assert report.recommendations == []


def test_analysis_report_full():
    report = AnalysisReport(
        dataset_summary="Iris dataset with 150 samples",
        shape=[150, 5],
        columns=["sepal_length", "sepal_width", "petal_length", "petal_width", "species"],
        data_quality_issues=["No missing values found"],
        cleaning_actions=[
            CleaningAction(
                action="drop",
                column="Id",
                description="Drop the ID column",
            ),
        ],
        split_statistics=SplitStatistics(
            train_samples=105,
            val_samples=22,
            test_samples=23,
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
        ),
        recommendations=["Consider feature scaling", "Try ensemble methods"],
    )
    assert len(report.columns) == 5
    assert len(report.cleaning_actions) == 1
    assert report.cleaning_actions[0].column == "Id"
    assert report.split_statistics is not None
    assert report.split_statistics.train_samples == 105
    assert len(report.recommendations) == 2


def test_analysis_report_serialization():
    """Verify round-trip serialization through model_dump/model_validate."""
    report = AnalysisReport(
        dataset_summary="Test",
        shape=[100, 3],
        cleaning_actions=[
            CleaningAction(action="encode", column="color", description="One-hot encode"),
        ],
        split_statistics=SplitStatistics(
            train_samples=70,
            val_samples=15,
            test_samples=15,
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
        ),
    )
    data = report.model_dump()
    restored = AnalysisReport.model_validate(data)
    assert restored.dataset_summary == "Test"
    assert restored.split_statistics.train_samples == 70
    assert restored.cleaning_actions[0].action == "encode"


# ---------------------------------------------------------------------------
# AnalystState tests
# ---------------------------------------------------------------------------


def test_analyst_state_creation():
    """AnalystState is a TypedDict; verify it can be constructed with expected keys."""
    state: AnalystState = {
        "objective": "Classify iris",
        "data_file_path": "data/iris.csv",
        "execution_plan": {"problem_type": "classification"},
        "problem_type": None,
        "data_profile": None,
        "cleaning_code": None,
        "cleaning_output": None,
        "cleaned_data_path": None,
        "split_code": None,
        "split_output": None,
        "split_data_paths": None,
        "analysis_report": None,
        "experiment_id": "test-123",
        "error": None,
    }
    assert state["objective"] == "Classify iris"
    assert state["data_file_path"] == "data/iris.csv"
    assert state["experiment_id"] == "test-123"
    assert state["analysis_report"] is None
