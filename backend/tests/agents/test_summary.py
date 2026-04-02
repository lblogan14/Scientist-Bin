"""Tests for the summary agent schemas, state, diagnostics, and formatting."""

from __future__ import annotations

import json

from scientist_bin_backend.agents.summary.schemas import (
    ChartData,
    CVFoldScores,
    FeatureImportanceItem,
    ModelRanking,
    ReviewAndRankResult,
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
# ReviewAndRankResult schema tests
# ---------------------------------------------------------------------------


def test_review_and_rank_result():
    result = ReviewAndRankResult(
        rankings=[
            ModelRanking(rank=1, algorithm="RandomForest"),
            ModelRanking(rank=2, algorithm="LogisticRegression"),
            ModelRanking(rank=3, algorithm="SVM"),
        ],
        best_algorithm="RandomForest",
        best_hyperparameters={"n_estimators": 100, "max_depth": 10},
        primary_metric_name="accuracy",
        primary_metric_value=0.96,
        selection_reasoning="Best overall accuracy with robust cross-validation",
    )
    assert len(result.rankings) == 3
    assert result.rankings[0].algorithm == "RandomForest"
    assert result.best_algorithm == "RandomForest"
    assert result.primary_metric_name == "accuracy"
    assert result.primary_metric_value == 0.96
    assert "robust" in result.selection_reasoning


def test_review_and_rank_result_defaults():
    result = ReviewAndRankResult(
        rankings=[ModelRanking(rank=1, algorithm="LinearRegression")],
        best_algorithm="LinearRegression",
        primary_metric_name="rmse",
        primary_metric_value=0.15,
        selection_reasoning="Lowest RMSE",
    )
    assert result.best_hyperparameters == {}


# ---------------------------------------------------------------------------
# SummaryReport schema tests
# ---------------------------------------------------------------------------


def _make_report(**overrides) -> SummaryReport:
    """Helper to create a SummaryReport with all required fields."""
    defaults = {
        "title": "Iris Classification Report",
        "executive_summary": "We classified iris species with 96% accuracy.",
        "dataset_overview": "The Iris dataset has 150 samples with 4 features",
        "methodology": "Used a 5-fold CV pipeline with 3 algorithms",
        "model_comparison_table": "| Model | Accuracy |\n|---|---|\n| RF | 0.96 |",
        "cv_stability_analysis": "All models showed low CV variance.",
        "best_model_analysis": "RandomForest achieved best results",
        "feature_importance_analysis": "Petal length was the most important feature.",
        "hyperparameter_analysis": "n_estimators had highest impact",
        "error_analysis": "Confusion matrix shows clean separation for setosa.",
        "conclusions": "Classification task is well-suited for tree methods",
        "reproducibility_notes": "Set random_state=42 for reproducibility",
    }
    return SummaryReport(**{**defaults, **overrides})


def test_summary_report_required_fields():
    report = _make_report()
    assert report.title == "Iris Classification Report"
    assert report.recommendations == []
    assert "RandomForest" in report.best_model_analysis
    assert report.executive_summary.startswith("We classified")
    assert "CV variance" in report.cv_stability_analysis
    assert "Petal length" in report.feature_importance_analysis
    assert "setosa" in report.error_analysis


def test_summary_report_full():
    report = _make_report(
        recommendations=["Try XGBoost", "Collect more data", "Feature engineering"],
    )
    assert len(report.recommendations) == 3
    assert report.reproducibility_notes == "Set random_state=42 for reproducibility"


def test_summary_report_serialization():
    """Verify round-trip serialization through model_dump/model_validate."""
    report = _make_report(recommendations=["rec1"])
    data = report.model_dump()
    restored = SummaryReport.model_validate(data)
    assert restored.title == "Iris Classification Report"
    assert restored.recommendations == ["rec1"]
    assert restored.executive_summary == report.executive_summary


# ---------------------------------------------------------------------------
# ChartData schema tests
# ---------------------------------------------------------------------------


def test_chart_data_defaults():
    cd = ChartData()
    assert cd.model_comparison == []
    assert cd.cv_fold_scores == {}
    assert cd.feature_importances is None
    assert cd.confusion_matrices is None
    assert cd.training_times == []
    assert cd.hyperparam_search == {}
    assert cd.residual_stats == {}


def test_chart_data_with_cv_fold_scores():
    cd = ChartData(
        cv_fold_scores={
            "RandomForest": {
                "accuracy": CVFoldScores(scores=[0.95, 0.96, 0.94], mean=0.95),
            }
        },
    )
    assert cd.cv_fold_scores["RandomForest"]["accuracy"].mean == 0.95
    assert len(cd.cv_fold_scores["RandomForest"]["accuracy"].scores) == 3


def test_feature_importance_item():
    item = FeatureImportanceItem(feature="petal_width", importance=0.42)
    assert item.feature == "petal_width"
    assert item.importance == 0.42


def test_chart_data_serialization():
    cd = ChartData(
        model_comparison=[{"algorithm": "SVM", "accuracy": 0.93}],
        training_times=[{"algorithm": "SVM", "time_seconds": 12.5}],
    )
    data = cd.model_dump()
    assert data["model_comparison"][0]["algorithm"] == "SVM"
    assert data["training_times"][0]["time_seconds"] == 12.5


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
        "data_profile": {"shape": [150, 5]},
        "framework_results": {"best_model": "RF"},
        "experiment_history": [{"algorithm": "RF", "metrics": {"accuracy": 0.95}}],
        "model_rankings": [],
        "best_model": None,
        "best_hyperparameters": None,
        "best_metrics": None,
        "selection_reasoning": None,
        "summary_report": None,
        "report_sections": None,
        "experiment_id": "test-123",
        "error": None,
    }
    assert state["objective"] == "Classify iris species"
    assert state["problem_type"] == "classification"
    assert state["framework_results"]["best_model"] == "RF"
    assert state["summary_report"] is None


# ---------------------------------------------------------------------------
# Diagnostics computation tests
# ---------------------------------------------------------------------------


def test_compute_cv_stability():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_cv_stability,
    )

    cv_fold_scores = {
        "RandomForest": {"accuracy": [0.95, 0.96, 0.94, 0.97, 0.96]},
        "LogisticRegression": {"accuracy": [0.80, 0.90, 0.85, 0.88, 0.82]},
    }
    results = _compute_cv_stability(cv_fold_scores)
    assert len(results) == 2

    # RandomForest should have lower std than LogisticRegression
    rf = next(r for r in results if r["algorithm"] == "RandomForest")
    lr = next(r for r in results if r["algorithm"] == "LogisticRegression")
    assert rf["std"] < lr["std"]
    assert rf["mean"] > lr["mean"]
    assert rf["min_fold"] == 0.94
    assert rf["max_fold"] == 0.97


def test_compute_cv_stability_empty():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_cv_stability,
    )

    assert _compute_cv_stability({}) == []


def test_compute_overfit_analysis():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_overfit_analysis,
    )

    history = [
        {
            "algorithm": "RandomForest",
            "metrics": {"train_accuracy": 1.0, "val_accuracy": 0.96},
        },
        {
            "algorithm": "LogisticRegression",
            "metrics": {"train_accuracy": 0.92, "val_accuracy": 0.90},
        },
    ]
    results = _compute_overfit_analysis(history)
    assert len(results) == 2

    rf = next(r for r in results if r["algorithm"] == "RandomForest")
    lr = next(r for r in results if r["algorithm"] == "LogisticRegression")

    # RF has higher overfit risk (4% gap)
    assert rf["gap"] > lr["gap"]
    assert rf["overfit_risk"] == "low"  # 4% < 5%
    assert lr["overfit_risk"] == "low"  # 2.17% < 5%


def test_compute_overfit_analysis_high_risk():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_overfit_analysis,
    )

    history = [
        {
            "algorithm": "Overfit",
            "metrics": {"train_accuracy": 1.0, "val_accuracy": 0.70},
        },
    ]
    results = _compute_overfit_analysis(history)
    assert len(results) == 1
    assert results[0]["overfit_risk"] == "high"


def test_compute_pareto_frontier():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_pareto_frontier,
    )

    history = [
        {
            "algorithm": "Fast",
            "metrics": {"val_accuracy": 0.90},
            "training_time_seconds": 1.0,
        },
        {
            "algorithm": "Slow",
            "metrics": {"val_accuracy": 0.95},
            "training_time_seconds": 10.0,
        },
        {
            "algorithm": "Dominated",
            "metrics": {"val_accuracy": 0.89},
            "training_time_seconds": 5.0,
        },
    ]
    pareto = _compute_pareto_frontier(history, "classification")
    # "Dominated" is dominated by "Fast" (lower time, higher accuracy)
    assert "Fast" in pareto
    assert "Slow" in pareto
    assert "Dominated" not in pareto


def test_compute_hyperparam_sensitivity():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_hyperparam_sensitivity,
    )

    cv_results = {
        "RandomForest": [
            {"params": {"n_estimators": 50, "max_depth": 5}, "mean_score": 0.90, "rank": 3},
            {"params": {"n_estimators": 100, "max_depth": 5}, "mean_score": 0.95, "rank": 1},
            {"params": {"n_estimators": 200, "max_depth": 5}, "mean_score": 0.94, "rank": 2},
        ],
    }
    results = _compute_hyperparam_sensitivity(cv_results)
    assert len(results) >= 1

    # n_estimators should have higher sensitivity than max_depth (which is constant)
    n_est = next((r for r in results if r["param_name"] == "n_estimators"), None)
    assert n_est is not None
    assert n_est["score_range"] > 0


# ---------------------------------------------------------------------------
# Context collector tests
# ---------------------------------------------------------------------------


async def test_collect_context_extracts_enriched_data():
    from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context

    state = {
        "experiment_history": [
            {
                "algorithm": "RF",
                "metrics": {"val_accuracy": 0.95},
                "training_time_seconds": 2.0,
                "cv_fold_scores": {"accuracy": [0.94, 0.95, 0.96]},
                "feature_importances": [{"feature": "x1", "importance": 0.5}],
                "confusion_matrix": {"labels": ["a", "b"], "matrix": [[9, 1], [0, 10]]},
            },
        ],
        "test_metrics": {"test_accuracy": 0.93},
        "test_diagnostics": None,
    }
    result = await collect_context(state)
    ctx = result["summary_context"]

    assert "RF" in ctx["cv_fold_scores"]
    assert "RF" in ctx["feature_importances"]
    assert "RF" in ctx["confusion_matrices"]
    assert ctx["total_training_time"] == 2.0
    assert ctx["algorithms_tried"] == ["RF"]


async def test_collect_context_empty_history():
    """Context collector handles empty experiment history gracefully."""
    from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context

    state = {"experiment_history": [], "test_metrics": None, "test_diagnostics": None}
    result = await collect_context(state)
    ctx = result["summary_context"]

    assert ctx["cv_fold_scores"] == {}
    assert ctx["feature_importances"] == {}
    assert ctx["confusion_matrices"] == {}
    assert ctx["total_training_time"] == 0
    assert ctx["algorithms_tried"] == []
    assert ctx["total_iterations"] == 0


async def test_collect_context_missing_enriched_fields():
    """Context collector handles records without enriched fields."""
    from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context

    state = {
        "experiment_history": [
            {
                "algorithm": "SVM",
                "metrics": {"val_accuracy": 0.88},
                "training_time_seconds": 1.0,
                # No enriched fields at all
            },
        ],
        "test_metrics": None,
        "test_diagnostics": None,
    }
    result = await collect_context(state)
    ctx = result["summary_context"]

    assert ctx["cv_fold_scores"] == {}
    assert ctx["feature_importances"] == {}
    assert ctx["confusion_matrices"] == {}
    assert ctx["algorithms_tried"] == ["SVM"]
    assert ctx["total_iterations"] == 1


async def test_collect_context_test_diagnostics_merged():
    """Context collector merges test_diagnostics under __test__ key."""
    from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context

    state = {
        "experiment_history": [],
        "test_metrics": {"test_accuracy": 0.91},
        "test_diagnostics": {
            "confusion_matrix": {"labels": ["a", "b"], "matrix": [[8, 2], [1, 9]]},
            "residual_stats": {"mean_residual": 0.01, "std_residual": 0.5},
        },
    }
    result = await collect_context(state)
    ctx = result["summary_context"]

    assert "__test__" in ctx["confusion_matrices"]
    assert ctx["confusion_matrices"]["__test__"]["labels"] == ["a", "b"]
    assert "__test__" in ctx["residual_stats"]
    assert ctx["residual_stats"]["__test__"]["mean_residual"] == 0.01


async def test_collect_context_deduplicates_algorithms():
    """Context collector deduplicates algorithm names preserving order."""
    from scientist_bin_backend.agents.summary.nodes.context_collector import collect_context

    state = {
        "experiment_history": [
            {"algorithm": "RF", "metrics": {}, "training_time_seconds": 1.0},
            {"algorithm": "LR", "metrics": {}, "training_time_seconds": 2.0},
            {"algorithm": "RF", "metrics": {}, "training_time_seconds": 3.0},
        ],
        "test_metrics": None,
        "test_diagnostics": None,
    }
    result = await collect_context(state)
    ctx = result["summary_context"]

    assert ctx["algorithms_tried"] == ["RF", "LR"]
    assert ctx["total_training_time"] == 6.0
    assert ctx["total_iterations"] == 3


# ---------------------------------------------------------------------------
# compute_diagnostics node tests
# ---------------------------------------------------------------------------


async def test_compute_diagnostics_full_node():
    """Test the full compute_diagnostics node with enriched data."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        compute_diagnostics,
    )

    state = {
        "problem_type": "classification",
        "summary_context": {
            "experiment_history": [
                {
                    "algorithm": "RF",
                    "metrics": {
                        "train_accuracy": 0.99,
                        "val_accuracy": 0.95,
                    },
                    "training_time_seconds": 2.0,
                },
                {
                    "algorithm": "LR",
                    "metrics": {
                        "train_accuracy": 0.90,
                        "val_accuracy": 0.88,
                    },
                    "training_time_seconds": 0.5,
                },
            ],
            "cv_fold_scores": {
                "RF": {"accuracy": [0.94, 0.95, 0.96, 0.95, 0.96]},
            },
            "cv_results": {
                "RF": [
                    {"params": {"n_estimators": 100}, "mean_score": 0.95, "rank": 1},
                    {"params": {"n_estimators": 50}, "mean_score": 0.92, "rank": 2},
                ],
            },
            "feature_importances": {},
            "confusion_matrices": {},
            "residual_stats": {},
            "algorithms_tried": ["RF", "LR"],
        },
    }
    result = await compute_diagnostics(state)
    diag = result["diagnostics"]

    assert "cv_stability" in diag
    assert "overfit_analyses" in diag
    assert "hyperparam_sensitivities" in diag
    assert "pareto_optimal_models" in diag
    assert "chart_data" in diag

    # CV stability should have RF entry
    assert len(diag["cv_stability"]) == 1
    assert diag["cv_stability"][0]["algorithm"] == "RF"

    # Overfit should have both RF and LR
    assert len(diag["overfit_analyses"]) == 2

    # Pareto should include at least one model
    assert len(diag["pareto_optimal_models"]) >= 1


async def test_compute_diagnostics_empty_context():
    """compute_diagnostics handles empty summary_context gracefully."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        compute_diagnostics,
    )

    state = {"problem_type": "classification", "summary_context": {}}
    result = await compute_diagnostics(state)
    diag = result["diagnostics"]

    assert diag["cv_stability"] == []
    assert diag["overfit_analyses"] == []
    assert diag["hyperparam_sensitivities"] == []
    assert diag["pareto_optimal_models"] == []
    assert isinstance(diag["chart_data"], dict)


# ---------------------------------------------------------------------------
# _build_chart_data tests
# ---------------------------------------------------------------------------


def test_build_chart_data_model_comparison():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    ctx = {
        "experiment_history": [
            {"algorithm": "RF", "metrics": {"val_accuracy": 0.95}, "training_time_seconds": 2.0},
            {"algorithm": "LR", "metrics": {"val_accuracy": 0.88}, "training_time_seconds": 0.5},
        ],
        "cv_fold_scores": {},
        "feature_importances": {},
        "confusion_matrices": {},
        "residual_stats": {},
        "cv_results": {},
        "algorithms_tried": ["RF", "LR"],
    }
    charts = _build_chart_data(ctx, "classification")

    assert len(charts["model_comparison"]) == 2
    assert charts["model_comparison"][0]["algorithm"] == "RF"
    assert charts["model_comparison"][0]["val_accuracy"] == 0.95

    assert len(charts["training_times"]) == 2
    assert charts["training_times"][0]["time_seconds"] == 2.0


def test_build_chart_data_with_cv_fold_scores():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    ctx = {
        "experiment_history": [],
        "cv_fold_scores": {"RF": {"accuracy": [0.94, 0.95, 0.96]}},
        "feature_importances": {},
        "confusion_matrices": {},
        "residual_stats": {},
        "cv_results": {},
        "algorithms_tried": ["RF"],
    }
    charts = _build_chart_data(ctx, "classification")

    assert "cv_fold_scores" in charts
    assert "RF" in charts["cv_fold_scores"]
    assert charts["cv_fold_scores"]["RF"]["accuracy"]["scores"] == [0.94, 0.95, 0.96]


def test_build_chart_data_with_feature_importances():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    features = [{"feature": f"f{i}", "importance": 1.0 / (i + 1)} for i in range(20)]
    ctx = {
        "experiment_history": [],
        "cv_fold_scores": {},
        "feature_importances": {"RF": features},
        "confusion_matrices": {},
        "residual_stats": {},
        "cv_results": {},
        "algorithms_tried": ["RF"],
    }
    charts = _build_chart_data(ctx, "classification")

    assert "feature_importances" in charts
    # Should be capped at 15
    assert len(charts["feature_importances"]["features"]) == 15
    assert charts["feature_importances"]["algorithm"] == "RF"


def test_build_chart_data_with_confusion_matrices():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    ctx = {
        "experiment_history": [],
        "cv_fold_scores": {},
        "feature_importances": {},
        "confusion_matrices": {"RF": {"labels": ["a", "b"], "matrix": [[9, 1], [0, 10]]}},
        "residual_stats": {},
        "cv_results": {},
        "algorithms_tried": [],
    }
    charts = _build_chart_data(ctx, "classification")

    assert "confusion_matrices" in charts
    assert "RF" in charts["confusion_matrices"]


def test_build_chart_data_with_residual_stats():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    ctx = {
        "experiment_history": [],
        "cv_fold_scores": {},
        "feature_importances": {},
        "confusion_matrices": {},
        "residual_stats": {"LR": {"mean_residual": 0.02, "std_residual": 1.5}},
        "cv_results": {},
        "algorithms_tried": [],
    }
    charts = _build_chart_data(ctx, "regression")

    assert "residual_stats" in charts
    assert "LR" in charts["residual_stats"]


def test_build_chart_data_empty_context():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _build_chart_data,
    )

    ctx = {
        "experiment_history": [],
        "cv_fold_scores": {},
        "feature_importances": {},
        "confusion_matrices": {},
        "residual_stats": {},
        "cv_results": {},
        "algorithms_tried": [],
    }
    charts = _build_chart_data(ctx, "classification")

    assert charts["model_comparison"] == []
    assert charts["training_times"] == []
    assert "cv_fold_scores" not in charts
    assert "feature_importances" not in charts


# ---------------------------------------------------------------------------
# _assemble_markdown tests
# ---------------------------------------------------------------------------


def test_assemble_markdown_all_sections():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _assemble_markdown

    report = _make_report(recommendations=["rec1", "rec2"])
    md = _assemble_markdown(report)

    assert md.startswith("# Iris Classification Report")
    assert "## Executive Summary" in md
    assert "## Dataset Overview" in md
    assert "## Methodology" in md
    assert "## Model Comparison" in md
    assert "## Cross-Validation Stability Analysis" in md
    assert "## Best Model Analysis" in md
    assert "## Feature Importance Analysis" in md
    assert "## Hyperparameter Analysis" in md
    assert "## Error Analysis" in md
    assert "## Conclusions" in md
    assert "## Recommendations" in md
    assert "- rec1" in md
    assert "- rec2" in md
    assert "## Reproducibility Notes" in md


def test_assemble_markdown_empty_recommendations():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _assemble_markdown

    report = _make_report()
    md = _assemble_markdown(report)

    assert "## Recommendations" in md
    # No bullet points since recommendations is empty
    assert "- " not in md.split("## Recommendations")[1].split("## Reproducibility")[0]


def test_assemble_markdown_section_order():
    """Sections appear in the expected order."""
    from scientist_bin_backend.agents.summary.nodes.report_generator import _assemble_markdown

    report = _make_report()
    md = _assemble_markdown(report)

    sections = [
        "# Iris Classification Report",
        "## Executive Summary",
        "## Dataset Overview",
        "## Methodology",
        "## Model Comparison",
        "## Cross-Validation Stability Analysis",
        "## Best Model Analysis",
        "## Feature Importance Analysis",
        "## Hyperparameter Analysis",
        "## Error Analysis",
        "## Conclusions",
        "## Recommendations",
        "## Reproducibility Notes",
    ]
    positions = [md.index(s) for s in sections]
    assert positions == sorted(positions), "Sections are not in expected order"


# ---------------------------------------------------------------------------
# save_artifacts node tests
# ---------------------------------------------------------------------------


async def test_save_artifacts_saves_report(tmp_path, monkeypatch):
    """save_artifacts writes report.md to disk."""
    from scientist_bin_backend.agents.summary.nodes import artifact_saver

    monkeypatch.setattr(artifact_saver, "_OUTPUTS_DIR", tmp_path)

    state = {
        "experiment_id": "test-exp-001",
        "summary_report": "# Test Report\n\nContent here.",
        "report_sections": {"chart_data": {"model_comparison": []}},
        "best_model": "RF",
    }
    await artifact_saver.save_artifacts(state)

    report_path = tmp_path / "runs" / "test-exp-001" / "summary" / "report.md"
    assert report_path.exists()
    assert "# Test Report" in report_path.read_text(encoding="utf-8")


async def test_save_artifacts_saves_chart_data(tmp_path, monkeypatch):
    """save_artifacts writes chart_data.json to disk."""
    from scientist_bin_backend.agents.summary.nodes import artifact_saver

    monkeypatch.setattr(artifact_saver, "_OUTPUTS_DIR", tmp_path)

    chart_data = {"model_comparison": [{"algorithm": "RF", "val_accuracy": 0.95}]}
    state = {
        "experiment_id": "test-exp-002",
        "summary_report": "# Report",
        "report_sections": {"chart_data": chart_data},
        "best_model": "RF",
    }
    await artifact_saver.save_artifacts(state)

    chart_path = tmp_path / "runs" / "test-exp-002" / "summary" / "chart_data.json"
    assert chart_path.exists()
    parsed = json.loads(chart_path.read_text(encoding="utf-8"))
    assert parsed["model_comparison"][0]["algorithm"] == "RF"


async def test_save_artifacts_skips_without_experiment_id():
    """save_artifacts returns gracefully when no experiment_id."""
    from scientist_bin_backend.agents.summary.nodes.artifact_saver import save_artifacts

    state = {"experiment_id": None, "summary_report": "# Report"}
    result = await save_artifacts(state)
    assert "messages" in result


async def test_save_artifacts_skips_without_report():
    """save_artifacts returns gracefully when no summary_report."""
    from scientist_bin_backend.agents.summary.nodes.artifact_saver import save_artifacts

    state = {"experiment_id": "test-001", "summary_report": None}
    result = await save_artifacts(state)
    assert "messages" in result


async def test_save_artifacts_no_chart_data(tmp_path, monkeypatch):
    """save_artifacts saves report but skips chart_data if not present."""
    from scientist_bin_backend.agents.summary.nodes import artifact_saver

    monkeypatch.setattr(artifact_saver, "_OUTPUTS_DIR", tmp_path)

    state = {
        "experiment_id": "test-exp-003",
        "summary_report": "# Report",
        "report_sections": None,
        "best_model": "RF",
    }
    await artifact_saver.save_artifacts(state)

    report_path = tmp_path / "runs" / "test-exp-003" / "summary" / "report.md"
    chart_path = tmp_path / "runs" / "test-exp-003" / "summary" / "chart_data.json"
    assert report_path.exists()
    assert not chart_path.exists()


# ---------------------------------------------------------------------------
# Format helper tests (report_generator.py)
# ---------------------------------------------------------------------------


def test_format_cv_stability_with_data():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_cv_stability

    diagnostics = {
        "cv_stability": [
            {
                "algorithm": "RF",
                "metric_name": "accuracy",
                "mean": 0.95,
                "std": 0.01,
                "cv_coefficient_of_variation": 0.0105,
                "min_fold": 0.94,
                "max_fold": 0.96,
            }
        ]
    }
    result = _format_cv_stability(diagnostics)
    assert "RF" in result
    assert "0.9500" in result
    assert "0.0100" in result


def test_format_cv_stability_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_cv_stability

    result = _format_cv_stability({})
    assert "No cross-validation fold data" in result


def test_format_overfit_with_data():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_overfit

    diagnostics = {
        "overfit_analyses": [
            {
                "algorithm": "RF",
                "metric_name": "accuracy",
                "train_value": 0.99,
                "val_value": 0.95,
                "gap": 0.04,
                "gap_percentage": 4.04,
                "overfit_risk": "low",
            }
        ]
    }
    result = _format_overfit(diagnostics)
    assert "RF" in result
    assert "low" in result


def test_format_overfit_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_overfit

    result = _format_overfit({})
    assert "No train/val metric pairs" in result


def test_format_feature_importances_with_data():
    from scientist_bin_backend.agents.summary.nodes.report_generator import (
        _format_feature_importances,
    )

    ctx = {
        "feature_importances": {
            "RF": [
                {"feature": "petal_width", "importance": 0.48},
                {"feature": "petal_length", "importance": 0.44},
            ]
        }
    }
    result = _format_feature_importances(ctx)
    assert "RF" in result
    assert "petal_width" in result
    assert "0.4800" in result


def test_format_feature_importances_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import (
        _format_feature_importances,
    )

    result = _format_feature_importances({})
    assert "No feature importances" in result


def test_format_feature_importances_truncates_top_15():
    from scientist_bin_backend.agents.summary.nodes.report_generator import (
        _format_feature_importances,
    )

    features = [{"feature": f"f{i}", "importance": 1.0 / (i + 1)} for i in range(25)]
    ctx = {"feature_importances": {"RF": features}}
    result = _format_feature_importances(ctx)
    # Count feature lines (indented with "  - ")
    feature_lines = [line for line in result.split("\n") if line.strip().startswith("- f")]
    assert len(feature_lines) == 15


def test_format_error_data_classification():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_error_data

    ctx = {
        "confusion_matrices": {
            "RF": {"labels": ["a", "b"], "matrix": [[9, 1], [0, 10]]},
        }
    }
    result = _format_error_data(ctx, "classification")
    assert "RF" in result
    assert "[9, 1]" in result
    assert "['a', 'b']" in result


def test_format_error_data_regression():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_error_data

    ctx = {
        "residual_stats": {
            "LR": {"mean_residual": 0.02, "std_residual": 1.5, "max_abs_residual": 5.3},
        }
    }
    result = _format_error_data(ctx, "regression")
    assert "LR" in result
    assert "0.02" in result


def test_format_error_data_classification_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_error_data

    result = _format_error_data({}, "classification")
    assert "No confusion matrices" in result


def test_format_error_data_regression_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_error_data

    result = _format_error_data({}, "regression")
    assert "No residual statistics" in result


def test_format_error_data_test_set_label():
    """Test set diagnostics stored under __test__ key show 'Test set' label."""
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_error_data

    ctx = {
        "confusion_matrices": {
            "__test__": {"labels": ["a", "b"], "matrix": [[8, 2], [1, 9]]},
        }
    }
    result = _format_error_data(ctx, "classification")
    assert "Test set" in result


def test_format_hyperparam_sensitivity_with_data():
    from scientist_bin_backend.agents.summary.nodes.report_generator import (
        _format_hyperparam_sensitivity,
    )

    diagnostics = {
        "hyperparam_sensitivities": [
            {
                "algorithm": "RF",
                "param_name": "n_estimators",
                "score_range": 0.05,
                "best_value": "100",
                "values_tried": 3,
            }
        ]
    }
    result = _format_hyperparam_sensitivity(diagnostics)
    assert "n_estimators" in result
    assert "0.0500" in result


def test_format_hyperparam_sensitivity_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import (
        _format_hyperparam_sensitivity,
    )

    result = _format_hyperparam_sensitivity({})
    assert "No hyperparameter search data" in result


def test_format_pareto_with_data():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_pareto

    diagnostics = {"pareto_optimal_models": ["RF", "LR"]}
    result = _format_pareto(diagnostics)
    assert "RF" in result
    assert "LR" in result


def test_format_pareto_empty():
    from scientist_bin_backend.agents.summary.nodes.report_generator import _format_pareto

    result = _format_pareto({})
    assert "Could not compute" in result


# ---------------------------------------------------------------------------
# Format diagnostics summary tests (reviewer.py)
# ---------------------------------------------------------------------------


def test_format_diagnostics_summary_full():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_diagnostics_summary

    diagnostics = {
        "cv_stability": [
            {
                "algorithm": "RF",
                "metric_name": "accuracy",
                "mean": 0.95,
                "std": 0.01,
                "cv_coefficient_of_variation": 0.0105,
                "min_fold": 0.94,
                "max_fold": 0.96,
            }
        ],
        "overfit_analyses": [
            {
                "algorithm": "RF",
                "metric_name": "accuracy",
                "train_value": 0.99,
                "val_value": 0.95,
                "gap": 0.04,
                "gap_percentage": 4.0,
                "overfit_risk": "low",
            }
        ],
        "pareto_optimal_models": ["RF"],
        "hyperparam_sensitivities": [
            {
                "algorithm": "RF",
                "param_name": "n_estimators",
                "score_range": 0.05,
                "best_value": "100",
                "values_tried": 3,
            }
        ],
    }
    result = _format_diagnostics_summary(diagnostics)
    assert "CV Stability" in result
    assert "Overfitting Analysis" in result
    assert "Pareto-optimal" in result
    assert "Hyperparameter Sensitivities" in result
    assert "RF" in result


def test_format_diagnostics_summary_empty():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_diagnostics_summary

    result = _format_diagnostics_summary({})
    assert "No diagnostics available" in result


def test_format_diagnostics_summary_none():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_diagnostics_summary

    result = _format_diagnostics_summary(None)
    assert "No diagnostics available" in result


# ---------------------------------------------------------------------------
# Format experiment history tests (reviewer.py)
# ---------------------------------------------------------------------------


def test_format_experiment_history():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_experiment_history

    history = [
        {
            "algorithm": "RF",
            "metrics": {"val_accuracy": 0.95},
            "hyperparameters": {"n_estimators": 100},
            "training_time_seconds": 2.0,
        },
    ]
    result = _format_experiment_history(history)
    assert "RF" in result
    assert "val_accuracy=0.95" in result
    assert "2.0s" in result


def test_format_experiment_history_empty():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_experiment_history

    result = _format_experiment_history([])
    assert "No experiment history" in result


def test_format_experiment_history_with_error():
    from scientist_bin_backend.agents.summary.nodes.reviewer import _format_experiment_history

    history = [
        {
            "algorithm": "SVM",
            "metrics": {},
            "error": "Convergence failed",
        },
    ]
    result = _format_experiment_history(history)
    assert "Convergence failed" in result


# ---------------------------------------------------------------------------
# ExperimentRecord enriched fields tests
# ---------------------------------------------------------------------------


def test_experiment_record_with_all_enriched_fields():
    """ExperimentRecord TypedDict accepts all enriched diagnostic fields."""
    from scientist_bin_backend.agents.base.states import ExperimentRecord

    record: ExperimentRecord = {
        "iteration": 1,
        "algorithm": "RandomForest",
        "hyperparameters": {"n_estimators": 100},
        "metrics": {"val_accuracy": 0.95},
        "training_time_seconds": 2.5,
        "timestamp": "2026-04-01T10:00:00",
        "cv_fold_scores": {"accuracy": [0.94, 0.95, 0.96]},
        "cv_results_top_n": [
            {"params": {"n_estimators": 100}, "mean_score": 0.95, "rank": 1},
        ],
        "feature_importances": [
            {"feature": "petal_width", "importance": 0.48},
        ],
        "confusion_matrix": {
            "labels": ["setosa", "versicolor"],
            "matrix": [[10, 0], [1, 9]],
        },
        "residual_stats": None,
    }
    assert record["cv_fold_scores"]["accuracy"] == [0.94, 0.95, 0.96]
    assert record["feature_importances"][0]["feature"] == "petal_width"
    assert record["confusion_matrix"]["labels"] == ["setosa", "versicolor"]
    assert record["residual_stats"] is None


def test_experiment_record_without_enriched_fields():
    """ExperimentRecord works without any enriched fields (backward compat)."""
    from scientist_bin_backend.agents.base.states import ExperimentRecord

    record: ExperimentRecord = {
        "iteration": 1,
        "algorithm": "SVM",
        "hyperparameters": {},
        "metrics": {"val_accuracy": 0.88},
        "training_time_seconds": 1.0,
        "timestamp": "2026-04-01T10:00:00",
    }
    assert record["algorithm"] == "SVM"
    # Enriched fields simply don't exist in the dict (total=False)
    assert "cv_fold_scores" not in record
    assert "feature_importances" not in record


# ---------------------------------------------------------------------------
# Edge case tests for diagnostics
# ---------------------------------------------------------------------------


def test_compute_cv_stability_single_fold():
    """Single fold is skipped (need at least 2 for stdev)."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_cv_stability,
    )

    result = _compute_cv_stability({"RF": {"accuracy": [0.95]}})
    assert result == []


def test_compute_overfit_no_matching_pairs():
    """No train/val metric pairs means empty result."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_overfit_analysis,
    )

    history = [
        {"algorithm": "RF", "metrics": {"val_accuracy": 0.95}},  # No train_accuracy
    ]
    result = _compute_overfit_analysis(history)
    assert result == []


def test_compute_overfit_moderate_risk():
    """Gap between 5% and 15% is moderate risk."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_overfit_analysis,
    )

    history = [
        {"algorithm": "RF", "metrics": {"train_accuracy": 1.0, "val_accuracy": 0.90}},
    ]
    result = _compute_overfit_analysis(history)
    assert result[0]["overfit_risk"] == "moderate"  # 10% gap


def test_compute_pareto_empty_history():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_pareto_frontier,
    )

    assert _compute_pareto_frontier([], "classification") == []


def test_compute_pareto_single_model():
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_pareto_frontier,
    )

    history = [
        {"algorithm": "RF", "metrics": {"val_accuracy": 0.95}, "training_time_seconds": 2.0},
    ]
    assert _compute_pareto_frontier(history, "classification") == ["RF"]


def test_compute_hyperparam_sensitivity_single_entry():
    """Single entry can't compute sensitivity (need at least 2)."""
    from scientist_bin_backend.agents.summary.nodes.diagnostics_computer import (
        _compute_hyperparam_sensitivity,
    )

    cv_results = {"RF": [{"params": {"n_estimators": 100}, "mean_score": 0.95, "rank": 1}]}
    result = _compute_hyperparam_sensitivity(cv_results)
    assert result == []


# ---------------------------------------------------------------------------
# AgentResponse schema tests
# ---------------------------------------------------------------------------


def test_agent_response_includes_new_fields():
    """AgentResponse schema includes selection_reasoning and report_sections."""
    from scientist_bin_backend.agents.central.schemas import AgentResponse

    resp = AgentResponse(
        framework="sklearn",
        best_model="RF",
        selection_reasoning="Best balance of accuracy and speed",
        report_sections={"chart_data": {"model_comparison": []}},
    )
    assert resp.selection_reasoning == "Best balance of accuracy and speed"
    assert resp.report_sections["chart_data"]["model_comparison"] == []


def test_agent_response_new_fields_default_to_none():
    """New AgentResponse fields default to None."""
    from scientist_bin_backend.agents.central.schemas import AgentResponse

    resp = AgentResponse(framework="sklearn")
    assert resp.selection_reasoning is None
    assert resp.report_sections is None
