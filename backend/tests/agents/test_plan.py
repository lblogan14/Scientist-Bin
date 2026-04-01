"""Tests for the plan agent schemas, state, helpers, and routing logic."""

from __future__ import annotations

from pathlib import Path

from scientist_bin_backend.agents.plan.nodes._context import build_upstream_context
from scientist_bin_backend.agents.plan.nodes.plan_reviewer import check_approval
from scientist_bin_backend.agents.plan.nodes.plan_saver import _resolve_output_dir
from scientist_bin_backend.agents.plan.nodes.plan_writer import _plan_to_markdown
from scientist_bin_backend.agents.plan.nodes.researcher import _build_search_query
from scientist_bin_backend.agents.plan.schemas import ExecutionPlan
from scientist_bin_backend.agents.plan.states import PlanState

# ---------------------------------------------------------------------------
# ExecutionPlan schema tests
# ---------------------------------------------------------------------------


def test_execution_plan_required_fields():
    plan = ExecutionPlan(
        approach_summary="Simple classification pipeline",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression", "RandomForestClassifier"],
        evaluation_metrics=["accuracy", "f1_weighted"],
    )
    assert plan.approach_summary == "Simple classification pipeline"
    assert plan.problem_type == "classification"
    assert len(plan.algorithms_to_try) == 2
    assert plan.target_column is None


def test_execution_plan_defaults():
    plan = ExecutionPlan(
        approach_summary="Regression",
        problem_type="regression",
        algorithms_to_try=["LinearRegression"],
        evaluation_metrics=["rmse"],
    )
    assert plan.cv_strategy == "5-fold stratified"
    assert plan.success_criteria == {}
    assert plan.pipeline_preprocessing_steps == []
    assert plan.feature_engineering_steps == []
    assert plan.hyperparameter_tuning_approach.startswith("GridSearchCV")


def test_execution_plan_full():
    plan = ExecutionPlan(
        approach_summary="Full classification pipeline",
        problem_type="classification",
        target_column="species",
        algorithms_to_try=["LogisticRegression", "RandomForest", "GradientBoosting"],
        pipeline_preprocessing_steps=[
            "StandardScaler on numeric features",
            "OneHotEncoder on categorical features",
        ],
        feature_engineering_steps=["create polynomial features"],
        evaluation_metrics=["accuracy", "f1_weighted", "roc_auc_ovr"],
        cv_strategy="10-fold",
        success_criteria={"accuracy": 0.90, "f1_weighted": 0.85},
        hyperparameter_tuning_approach=(
            "GridSearchCV for LogisticRegression, "
            "RandomizedSearchCV with 50 iterations for ensemble methods"
        ),
    )
    assert plan.target_column == "species"
    assert len(plan.algorithms_to_try) == 3
    assert plan.success_criteria["accuracy"] == 0.90
    assert len(plan.pipeline_preprocessing_steps) == 2
    assert "RandomizedSearchCV" in plan.hyperparameter_tuning_approach


def test_execution_plan_serialization():
    """ExecutionPlan can round-trip through model_dump."""
    plan = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
        pipeline_preprocessing_steps=["StandardScaler"],
        hyperparameter_tuning_approach="GridSearchCV",
    )
    d = plan.model_dump()
    assert d["pipeline_preprocessing_steps"] == ["StandardScaler"]
    assert d["hyperparameter_tuning_approach"] == "GridSearchCV"
    assert "data_split_strategy" not in d
    assert "preprocessing_steps" not in d


# ---------------------------------------------------------------------------
# PlanState tests
# ---------------------------------------------------------------------------


def test_plan_state_creation():
    """PlanState is a TypedDict; verify it can be constructed with expected keys."""
    state: PlanState = {
        "objective": "Classify iris species",
        "data_description": "4 features, 3 classes",
        "data_file_path": "data/iris.csv",
        "framework_preference": "sklearn",
        "execution_plan": None,
        "plan_markdown": None,
        "plan_approved": False,
        "revision_count": 0,
        "max_revisions": 3,
    }
    assert state["objective"] == "Classify iris species"
    assert state["plan_approved"] is False
    assert state["revision_count"] == 0


def test_plan_state_has_no_rewritten_query():
    """rewritten_query was removed — verify it's not in PlanState annotations."""
    assert "rewritten_query" not in PlanState.__annotations__


# ---------------------------------------------------------------------------
# build_upstream_context tests
# ---------------------------------------------------------------------------


def test_build_upstream_context_empty_state():
    """Returns fallback message when no upstream data is present."""
    result = build_upstream_context({})
    assert result == "No upstream analysis available."


def test_build_upstream_context_task_analysis_only():
    """Renders task_analysis section when only central agent output is present."""
    state = {
        "task_analysis": {
            "task_type": "classification",
            "task_subtype": "binary",
            "complexity_estimate": "low",
            "key_considerations": ["class imbalance"],
            "recommended_approach": "Use logistic regression",
            "data_characteristics": {
                "estimated_features": "10",
                "estimated_samples": "500",
            },
        }
    }
    result = build_upstream_context(state)
    assert "Pre-Analysis" in result
    assert "classification" in result
    assert "binary" in result
    assert "class imbalance" in result
    assert "Estimated features: 10" in result
    assert "Estimated samples: 500" in result


def test_build_upstream_context_data_profile_only():
    """Renders data_profile section when only analyst output is present."""
    state = {
        "data_profile": {
            "shape": [150, 5],
            "column_names": ["a", "b", "c", "d", "target"],
            "numeric_columns": ["a", "b", "c", "d"],
            "categorical_columns": [],
            "target_column": "target",
            "missing_counts": {"a": 3},
            "class_distribution": {"setosa": 50, "versicolor": 50, "virginica": 50},
            "data_quality_issues": ["minor skew in column a"],
        }
    }
    result = build_upstream_context(state)
    assert "Actual Data Profile" in result
    assert "[150, 5]" in result
    assert "target" in result
    assert '"a": 3' in result
    assert "setosa" in result
    assert "minor skew" in result


def test_build_upstream_context_analysis_report_truncated():
    """Analysis report is truncated to 3000 characters."""
    long_report = "A" * 5000
    state = {"analysis_report": long_report}
    result = build_upstream_context(state)
    assert "Data Analysis Report" in result
    # The report content should be at most 3000 chars
    report_part = result.split("== Data Analysis Report (from analyst agent) ==\n")[1]
    assert len(report_part.strip()) == 3000


def test_build_upstream_context_problem_type():
    """problem_type is included when present."""
    state = {"problem_type": "regression"}
    result = build_upstream_context(state)
    assert "Confirmed problem type: regression" in result


def test_build_upstream_context_full():
    """All sections present when full upstream context is available."""
    state = {
        "task_analysis": {
            "task_type": "classification",
            "complexity_estimate": "medium",
        },
        "data_profile": {
            "shape": [100, 4],
            "column_names": ["x1", "x2", "x3", "y"],
            "numeric_columns": ["x1", "x2", "x3"],
            "categorical_columns": [],
            "target_column": "y",
        },
        "analysis_report": "# Analysis\nThis dataset has 100 samples.",
        "problem_type": "classification",
    }
    result = build_upstream_context(state)
    assert "Pre-Analysis" in result
    assert "Actual Data Profile" in result
    assert "Data Analysis Report" in result
    assert "Confirmed problem type: classification" in result


# ---------------------------------------------------------------------------
# _build_search_query tests
# ---------------------------------------------------------------------------


def test_build_search_query_minimal():
    """Basic query with just objective."""
    state = {"objective": "Classify iris species"}
    query = _build_search_query(state)
    assert "Classify iris species" in query
    assert "unknown" in query  # problem_type defaults to unknown
    assert "scikit-learn" in query  # default framework
    assert "Focus on:" in query


def test_build_search_query_with_data_profile():
    """Data profile characteristics are included in the query."""
    state = {
        "objective": "Predict prices",
        "problem_type": "regression",
        "framework_preference": "sklearn",
        "data_profile": {
            "shape": [1000, 20],
            "numeric_columns": ["a", "b", "c"],
            "categorical_columns": ["d", "e"],
            "target_column": "price",
        },
    }
    query = _build_search_query(state)
    assert "regression" in query
    assert "sklearn" in query
    assert "3 numeric features" in query
    assert "2 categorical features" in query
    assert "Target: price" in query


def test_build_search_query_with_class_distribution():
    """Class distribution included when present."""
    state = {
        "objective": "Classify",
        "data_profile": {
            "class_distribution": {"A": 100, "B": 50},
        },
    }
    query = _build_search_query(state)
    assert "Class distribution:" in query


def test_build_search_query_with_considerations():
    """Key considerations from task_analysis are included."""
    state = {
        "objective": "Classify",
        "task_analysis": {
            "key_considerations": ["class imbalance", "high cardinality"],
        },
    }
    query = _build_search_query(state)
    assert "class imbalance" in query
    assert "high cardinality" in query


def test_build_search_query_limits_considerations():
    """Only first 5 considerations are included."""
    state = {
        "objective": "Classify",
        "task_analysis": {
            "key_considerations": [f"item_{i}" for i in range(10)],
        },
    }
    query = _build_search_query(state)
    assert "item_4" in query
    assert "item_5" not in query


# ---------------------------------------------------------------------------
# _plan_to_markdown tests
# ---------------------------------------------------------------------------


def test_plan_to_markdown_required_sections():
    """Required sections always appear in markdown output."""
    plan = ExecutionPlan(
        approach_summary="Test approach",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
    )
    md = _plan_to_markdown(plan)
    assert "# Execution Plan" in md
    assert "## Summary" in md
    assert "## Problem Details" in md
    assert "## Algorithms" in md
    assert "## Evaluation Metrics" in md
    assert "## Hyperparameter Tuning" in md
    assert "Test approach" in md
    assert "LogisticRegression" in md


def test_plan_to_markdown_conditional_preprocessing():
    """Pipeline Preprocessing section only appears when steps are non-empty."""
    plan_without = ExecutionPlan(
        approach_summary="No preprocessing",
        problem_type="regression",
        algorithms_to_try=["Ridge"],
        evaluation_metrics=["rmse"],
    )
    md_without = _plan_to_markdown(plan_without)
    assert "## Pipeline Preprocessing" not in md_without

    plan_with = ExecutionPlan(
        approach_summary="With preprocessing",
        problem_type="regression",
        algorithms_to_try=["Ridge"],
        evaluation_metrics=["rmse"],
        pipeline_preprocessing_steps=["StandardScaler on numerics"],
    )
    md_with = _plan_to_markdown(plan_with)
    assert "## Pipeline Preprocessing" in md_with
    assert "StandardScaler on numerics" in md_with


def test_plan_to_markdown_conditional_feature_engineering():
    """Feature Engineering section only appears when steps are non-empty."""
    plan = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
    )
    assert "## Feature Engineering" not in _plan_to_markdown(plan)

    plan_with_fe = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
        feature_engineering_steps=["polynomial features"],
    )
    assert "## Feature Engineering" in _plan_to_markdown(plan_with_fe)


def test_plan_to_markdown_conditional_success_criteria():
    """Success Criteria section only appears when criteria are non-empty."""
    plan = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
    )
    assert "## Success Criteria" not in _plan_to_markdown(plan)

    plan_with_sc = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
        success_criteria={"accuracy": 0.9},
    )
    md = _plan_to_markdown(plan_with_sc)
    assert "## Success Criteria" in md
    assert "**accuracy** >= 0.9" in md


def test_plan_to_markdown_target_column():
    """Target column appears when set, absent when None."""
    plan_no_target = ExecutionPlan(
        approach_summary="Test",
        problem_type="clustering",
        algorithms_to_try=["KMeans"],
        evaluation_metrics=["silhouette"],
    )
    assert "Target column" not in _plan_to_markdown(plan_no_target)

    plan_with_target = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        target_column="species",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
    )
    assert "**Target column:** species" in _plan_to_markdown(plan_with_target)


def test_plan_to_markdown_hyperparameter_tuning():
    """Hyperparameter tuning approach is rendered in its own section."""
    plan = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
        hyperparameter_tuning_approach="Use RandomizedSearchCV with 100 iterations",
    )
    md = _plan_to_markdown(plan)
    assert "## Hyperparameter Tuning" in md
    assert "RandomizedSearchCV with 100 iterations" in md


def test_plan_to_markdown_no_data_split_section():
    """Markdown output has no Data split line (analyst owns splitting)."""
    plan = ExecutionPlan(
        approach_summary="Test",
        problem_type="classification",
        algorithms_to_try=["LogisticRegression"],
        evaluation_metrics=["accuracy"],
    )
    md = _plan_to_markdown(plan)
    assert "Data split" not in md
    assert "data_split_strategy" not in md


# ---------------------------------------------------------------------------
# _resolve_output_dir tests
# ---------------------------------------------------------------------------


def test_resolve_output_dir_structure():
    """Output path ends with outputs/runs/{experiment_id}/plan."""
    result = _resolve_output_dir("test-experiment-123")
    assert result.parts[-4:] == ("outputs", "runs", "test-experiment-123", "plan")


def test_resolve_output_dir_returns_path():
    """Returns a pathlib.Path object."""
    result = _resolve_output_dir("abc")
    assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# check_approval routing tests
# ---------------------------------------------------------------------------


def test_check_approval_approved():
    state = {"plan_approved": True}
    assert check_approval(state) == "approved"


def test_check_approval_revise():
    state = {"plan_approved": False, "revision_count": 0, "max_revisions": 3}
    assert check_approval(state) == "revise"


def test_check_approval_max_revisions_reached():
    state = {"plan_approved": False, "revision_count": 3, "max_revisions": 3}
    assert check_approval(state) == "approved"


def test_check_approval_max_revisions_exceeded():
    state = {"plan_approved": False, "revision_count": 5, "max_revisions": 3}
    assert check_approval(state) == "approved"


def test_check_approval_default_max_revisions():
    """When max_revisions is not set, defaults to 3."""
    state = {"plan_approved": False, "revision_count": 2}
    assert check_approval(state) == "revise"


def test_check_approval_no_state_fields():
    """With empty state, plan_approved is falsy and revision_count defaults to 0."""
    state = {}
    assert check_approval(state) == "revise"
