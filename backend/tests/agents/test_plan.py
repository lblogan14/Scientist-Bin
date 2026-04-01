"""Tests for the plan agent schemas, state, and routing logic."""

from __future__ import annotations

from scientist_bin_backend.agents.plan.nodes.plan_reviewer import check_approval
from scientist_bin_backend.agents.plan.schemas import ExecutionPlan, RewrittenQuery
from scientist_bin_backend.agents.plan.states import PlanState

# ---------------------------------------------------------------------------
# RewrittenQuery schema tests
# ---------------------------------------------------------------------------


def test_rewritten_query_required_fields():
    rq = RewrittenQuery(enhanced_objective="Classify iris species using supervised ML")
    assert rq.enhanced_objective == "Classify iris species using supervised ML"
    assert rq.key_requirements == []
    assert rq.constraints == []


def test_rewritten_query_full():
    rq = RewrittenQuery(
        enhanced_objective="Multi-class classification of iris species",
        key_requirements=["multi-class classification", "handle missing values"],
        constraints=["scikit-learn only", "must run under 5 minutes"],
    )
    assert len(rq.key_requirements) == 2
    assert "scikit-learn only" in rq.constraints


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
    assert plan.preprocessing_steps == []
    assert plan.feature_engineering_steps == []
    assert plan.data_split_strategy == "stratified 70/15/15"


def test_execution_plan_full():
    plan = ExecutionPlan(
        approach_summary="Full classification pipeline",
        problem_type="classification",
        target_column="species",
        algorithms_to_try=["LogisticRegression", "RandomForest", "GradientBoosting"],
        preprocessing_steps=["drop ID column", "impute missing with median"],
        feature_engineering_steps=["create polynomial features"],
        evaluation_metrics=["accuracy", "f1_weighted", "roc_auc_ovr"],
        cv_strategy="10-fold",
        success_criteria={"accuracy": 0.90, "f1_weighted": 0.85},
        data_split_strategy="stratified 80/10/10",
    )
    assert plan.target_column == "species"
    assert len(plan.algorithms_to_try) == 3
    assert plan.success_criteria["accuracy"] == 0.90
    assert plan.data_split_strategy == "stratified 80/10/10"


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
