"""Tests for the analyst agent schemas and state."""

from __future__ import annotations

import pytest

from scientist_bin_backend.agents.analyst.nodes.data_splitter import _compute_split_ratios
from scientist_bin_backend.agents.analyst.schemas import (
    AnalysisReport,
    CleaningAction,
    SplitStatistics,
    ValidatedClassification,
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
# ValidatedClassification schema tests
# ---------------------------------------------------------------------------


def test_validated_classification_confirmed():
    vc = ValidatedClassification(
        problem_type="classification",
        confidence="confirmed",
        reasoning="Target column 'species' has 3 distinct categorical values.",
        target_column_guess="species",
        suggested_metrics=["accuracy", "f1_macro"],
    )
    assert vc.problem_type == "classification"
    assert vc.confidence == "confirmed"
    assert vc.target_column_guess == "species"
    assert vc.upstream_disagreement is None
    assert len(vc.suggested_metrics) == 2


def test_validated_classification_refined():
    vc = ValidatedClassification(
        problem_type="classification",
        confidence="refined",
        reasoning="Data confirms classification but target is binary, not multiclass.",
        target_column_guess="label",
        suggested_metrics=["accuracy", "f1", "roc_auc"],
        upstream_disagreement="Upstream said multiclass but target has only 2 classes.",
    )
    assert vc.confidence == "refined"
    assert vc.upstream_disagreement is not None


def test_validated_classification_overridden():
    vc = ValidatedClassification(
        problem_type="regression",
        confidence="overridden",
        reasoning="Target column 'price' is continuous numeric, not categorical.",
        target_column_guess="price",
        suggested_metrics=["rmse", "r2"],
        upstream_disagreement="Upstream classified as classification but target is continuous.",
    )
    assert vc.problem_type == "regression"
    assert vc.confidence == "overridden"
    assert "continuous" in vc.upstream_disagreement


def test_validated_classification_defaults():
    vc = ValidatedClassification(
        problem_type="clustering",
        confidence="confirmed",
        reasoning="No target column, clustering is appropriate.",
    )
    assert vc.target_column_guess is None
    assert vc.suggested_metrics == []
    assert vc.upstream_disagreement is None


def test_validated_classification_invalid_confidence():
    with pytest.raises(Exception):
        ValidatedClassification(
            problem_type="classification",
            confidence="maybe",
            reasoning="test",
        )


def test_validated_classification_serialization():
    """Verify round-trip serialization through model_dump/model_validate."""
    vc = ValidatedClassification(
        problem_type="classification",
        confidence="refined",
        reasoning="Binary, not multiclass",
        target_column_guess="target",
        suggested_metrics=["f1", "precision", "recall"],
        upstream_disagreement="Was marked as multiclass",
    )
    data = vc.model_dump()
    restored = ValidatedClassification.model_validate(data)
    assert restored.confidence == "refined"
    assert restored.upstream_disagreement == "Was marked as multiclass"
    assert restored.suggested_metrics == ["f1", "precision", "recall"]


# ---------------------------------------------------------------------------
# AnalystState tests
# ---------------------------------------------------------------------------


def test_analyst_state_creation():
    """AnalystState is a TypedDict; verify it can be constructed with expected keys."""
    state: AnalystState = {
        "objective": "Classify iris",
        "data_file_path": "data/iris.csv",
        "execution_plan": {"problem_type": "classification"},
        "task_analysis": None,
        "data_description": None,
        "selected_framework": None,
        "problem_type": None,
        "classification_confidence": None,
        "classification_reasoning": None,
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
    assert state["task_analysis"] is None
    assert state["classification_confidence"] is None


def test_analyst_state_with_upstream_context():
    """AnalystState accepts upstream context from the central orchestrator."""
    task_analysis = {
        "task_type": "classification",
        "key_considerations": ["class imbalance"],
        "complexity_estimate": "medium",
    }
    state: AnalystState = {
        "objective": "Classify fraud",
        "data_file_path": "data/fraud.csv",
        "task_analysis": task_analysis,
        "data_description": "Credit card transactions",
        "selected_framework": "sklearn",
    }
    assert state["task_analysis"]["task_type"] == "classification"
    assert state["data_description"] == "Credit card transactions"
    assert state["selected_framework"] == "sklearn"


# ---------------------------------------------------------------------------
# _compute_split_ratios tests
# ---------------------------------------------------------------------------


def test_compute_split_ratios_default():
    """No context gives default 70/15/15 ratios."""
    test_size, second = _compute_split_ratios(None, None)
    assert test_size == 0.30
    assert second == 0.50


def test_compute_split_ratios_high_complexity():
    """High complexity gives 60/20/20 ratios."""
    task_analysis = {"complexity_estimate": "high"}
    test_size, second = _compute_split_ratios(task_analysis, None)
    assert test_size == 0.40
    assert second == 0.50


def test_compute_split_ratios_medium_complexity():
    """Medium complexity gives default ratios."""
    task_analysis = {"complexity_estimate": "medium"}
    test_size, second = _compute_split_ratios(task_analysis, None)
    assert test_size == 0.30
    assert second == 0.50


def test_compute_split_ratios_low_complexity():
    """Low complexity gives default ratios."""
    task_analysis = {"complexity_estimate": "low"}
    test_size, second = _compute_split_ratios(task_analysis, None)
    assert test_size == 0.30
    assert second == 0.50


def test_compute_split_ratios_tiny_dataset():
    """Tiny dataset (<200 rows) gives 80/10/10 ratios."""
    data_profile = {"shape": [100, 5]}
    test_size, second = _compute_split_ratios(None, data_profile)
    assert test_size == 0.20
    assert second == 0.50


def test_compute_split_ratios_tiny_dataset_overrides_complexity():
    """Tiny dataset takes priority over high complexity."""
    task_analysis = {"complexity_estimate": "high"}
    data_profile = {"shape": [50, 10]}
    test_size, second = _compute_split_ratios(task_analysis, data_profile)
    assert test_size == 0.20  # Tiny dataset wins


def test_compute_split_ratios_large_dataset_high_complexity():
    """Large dataset with high complexity gives 60/20/20."""
    task_analysis = {"complexity_estimate": "high"}
    data_profile = {"shape": [10000, 50]}
    test_size, second = _compute_split_ratios(task_analysis, data_profile)
    assert test_size == 0.40


def test_compute_split_ratios_boundary_200_rows():
    """Dataset with exactly 200 rows is NOT considered tiny."""
    data_profile = {"shape": [200, 5]}
    test_size, second = _compute_split_ratios(None, data_profile)
    assert test_size == 0.30  # Default, not tiny


def test_compute_split_ratios_boundary_199_rows():
    """Dataset with 199 rows IS considered tiny."""
    data_profile = {"shape": [199, 5]}
    test_size, second = _compute_split_ratios(None, data_profile)
    assert test_size == 0.20  # Tiny


def test_compute_split_ratios_missing_shape():
    """data_profile without shape key gives default ratios."""
    data_profile = {"columns": ["a", "b"]}
    test_size, second = _compute_split_ratios(None, data_profile)
    assert test_size == 0.30


def test_compute_split_ratios_missing_complexity():
    """task_analysis without complexity_estimate gives default ratios."""
    task_analysis = {"task_type": "classification"}
    test_size, second = _compute_split_ratios(task_analysis, None)
    assert test_size == 0.30


def test_compute_split_ratios_train_never_below_60_percent():
    """All returned ratios ensure at least 60% training data."""
    cases = [
        (None, None),
        ({"complexity_estimate": "high"}, None),
        (None, {"shape": [50, 3]}),
        ({"complexity_estimate": "high"}, {"shape": [10000, 50]}),
    ]
    for task_analysis, data_profile in cases:
        test_size, _ = _compute_split_ratios(task_analysis, data_profile)
        train_ratio = 1.0 - test_size
        assert train_ratio >= 0.60, f"Train ratio {train_ratio} < 0.60 for {task_analysis}"
