"""Tests for the summary agent schemas and state."""

from __future__ import annotations

from scientist_bin_backend.agents.summary.schemas import (
    BestModelSelection,
    ModelRanking,
    ModelRankingList,
    SummaryReport,
)
from scientist_bin_backend.agents.summary.states import SummaryState

# ---------------------------------------------------------------------------
# ModelRanking schema tests
# ---------------------------------------------------------------------------


def test_model_ranking_required_fields():
    ranking = ModelRanking(
        rank=1,
        algorithm="RandomForestClassifier",
    )
    assert ranking.rank == 1
    assert ranking.algorithm == "RandomForestClassifier"
    assert ranking.hyperparameters == {}
    assert ranking.train_metrics == {}
    assert ranking.val_metrics == {}
    assert ranking.test_metrics is None
    assert ranking.training_time_seconds == 0.0
    assert ranking.strengths == []
    assert ranking.weaknesses == []


def test_model_ranking_full():
    ranking = ModelRanking(
        rank=1,
        algorithm="GradientBoostingClassifier",
        hyperparameters={"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1},
        train_metrics={"accuracy": 0.99, "f1_weighted": 0.99},
        val_metrics={"accuracy": 0.96, "f1_weighted": 0.95},
        test_metrics={"accuracy": 0.95, "f1_weighted": 0.94},
        training_time_seconds=12.5,
        strengths=["High accuracy", "Robust to overfitting"],
        weaknesses=["Slower training", "Less interpretable"],
    )
    assert ranking.hyperparameters["n_estimators"] == 200
    assert ranking.val_metrics["accuracy"] == 0.96
    assert ranking.test_metrics["accuracy"] == 0.95
    assert ranking.training_time_seconds == 12.5
    assert len(ranking.strengths) == 2
    assert len(ranking.weaknesses) == 2


# ---------------------------------------------------------------------------
# ModelRankingList schema tests
# ---------------------------------------------------------------------------


def test_model_ranking_list():
    rankings = ModelRankingList(
        rankings=[
            ModelRanking(rank=1, algorithm="RandomForest"),
            ModelRanking(rank=2, algorithm="LogisticRegression"),
            ModelRanking(rank=3, algorithm="SVM"),
        ]
    )
    assert len(rankings.rankings) == 3
    assert rankings.rankings[0].algorithm == "RandomForest"
    assert rankings.rankings[2].rank == 3


# ---------------------------------------------------------------------------
# BestModelSelection schema tests
# ---------------------------------------------------------------------------


def test_best_model_selection():
    selection = BestModelSelection(
        algorithm="RandomForestClassifier",
        hyperparameters={"n_estimators": 100, "max_depth": 10},
        primary_metric_name="accuracy",
        primary_metric_value=0.96,
        reasoning="Best overall accuracy with robust cross-validation",
    )
    assert selection.algorithm == "RandomForestClassifier"
    assert selection.primary_metric_name == "accuracy"
    assert selection.primary_metric_value == 0.96
    assert "robust" in selection.reasoning


def test_best_model_selection_defaults():
    selection = BestModelSelection(
        algorithm="LinearRegression",
        primary_metric_name="rmse",
        primary_metric_value=0.15,
        reasoning="Lowest RMSE",
    )
    assert selection.hyperparameters == {}


# ---------------------------------------------------------------------------
# SummaryReport schema tests
# ---------------------------------------------------------------------------


def test_summary_report_required_fields():
    report = SummaryReport(
        title="Iris Classification Report",
        dataset_overview="The Iris dataset has 150 samples with 4 features",
        methodology="Used a 5-fold CV pipeline with 3 algorithms",
        model_comparison_table="| Model | Accuracy |\n|---|---|\n| RF | 0.96 |",
        best_model_analysis="RandomForest achieved best results",
        hyperparameter_analysis="n_estimators had highest impact",
        conclusions="Classification task is well-suited for tree methods",
        reproducibility_notes="Set random_state=42 for reproducibility",
    )
    assert report.title == "Iris Classification Report"
    assert report.recommendations == []
    assert "RandomForest" in report.best_model_analysis


def test_summary_report_full():
    report = SummaryReport(
        title="Full Report",
        dataset_overview="Overview",
        methodology="Methodology",
        model_comparison_table="| Model | Accuracy |",
        best_model_analysis="Best model analysis",
        hyperparameter_analysis="Hyperparameter analysis",
        conclusions="Conclusions",
        recommendations=["Try XGBoost", "Collect more data", "Feature engineering"],
        reproducibility_notes="Use provided requirements.txt",
    )
    assert len(report.recommendations) == 3
    assert report.reproducibility_notes == "Use provided requirements.txt"


def test_summary_report_serialization():
    """Verify round-trip serialization through model_dump/model_validate."""
    report = SummaryReport(
        title="Test Report",
        dataset_overview="Test overview",
        methodology="Test method",
        model_comparison_table="| A | B |",
        best_model_analysis="Test analysis",
        hyperparameter_analysis="Test hyper",
        conclusions="Test conclusions",
        recommendations=["rec1"],
        reproducibility_notes="Test notes",
    )
    data = report.model_dump()
    restored = SummaryReport.model_validate(data)
    assert restored.title == "Test Report"
    assert restored.recommendations == ["rec1"]


# ---------------------------------------------------------------------------
# SummaryState tests
# ---------------------------------------------------------------------------


def test_summary_state_creation():
    """SummaryState is a TypedDict; verify it can be constructed with expected keys."""
    state: SummaryState = {
        "objective": "Classify iris species",
        "problem_type": "classification",
        "execution_plan": {"algorithms_to_try": ["RF", "LR"]},
        "analysis_report": "Dataset is clean",
        "sklearn_results": {"best_model": "RF"},
        "experiment_history": [{"algorithm": "RF", "metrics": {"accuracy": 0.95}}],
        "runs": [],
        "best_model": None,
        "best_hyperparameters": None,
        "best_metrics": None,
        "model_comparison": [],
        "summary_report": None,
        "experiment_id": "test-123",
        "error": None,
    }
    assert state["objective"] == "Classify iris species"
    assert state["problem_type"] == "classification"
    assert state["sklearn_results"]["best_model"] == "RF"
    assert state["summary_report"] is None
