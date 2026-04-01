"""Tests for the sklearn subagent schemas, utilities, and routing logic."""

from __future__ import annotations

from scientist_bin_backend.agents.base.schemas import (
    AlgorithmCandidate,
    FinalReport,
    IterationDecision,
    ProblemClassification,
    StrategyPlan,
)
from scientist_bin_backend.agents.sklearn.graph import _route_decision
from scientist_bin_backend.agents.sklearn.schemas import SklearnStrategyPlan
from scientist_bin_backend.agents.sklearn.utils import strip_code_fences

# --- Base schema tests ---


def test_problem_classification():
    result = ProblemClassification(
        problem_type="classification",
        reasoning="Categorical target",
        target_column_guess="species",
        suggested_metrics=["accuracy", "f1"],
    )
    assert result.problem_type == "classification"
    assert result.target_column_guess == "species"


def test_algorithm_candidate():
    candidate = AlgorithmCandidate(
        algorithm_name="RandomForestClassifier",
        rationale="Good for tabular data",
        hyperparameter_grid={"n_estimators": [100, 200], "max_depth": [5, 10]},
        priority=2,
    )
    assert candidate.algorithm_name == "RandomForestClassifier"
    assert len(candidate.hyperparameter_grid) == 2


def test_strategy_plan_defaults():
    plan = StrategyPlan(
        approach_summary="Ensemble classification",
        candidate_algorithms=[
            AlgorithmCandidate(
                algorithm_name="LogisticRegression",
                rationale="Simple baseline",
            ),
        ],
    )
    assert plan.approach_summary == "Ensemble classification"
    assert len(plan.candidate_algorithms) == 1
    assert plan.cv_strategy == "5-fold stratified"


def test_sklearn_strategy_plan():
    plan = SklearnStrategyPlan(
        approach_summary="Sklearn pipeline",
        candidate_algorithms=[
            AlgorithmCandidate(
                algorithm_name="RandomForest",
                rationale="Good for tabular",
            ),
        ],
        pipeline_structure="imputer -> scaler -> model",
        use_grid_search=True,
    )
    assert plan.pipeline_structure == "imputer -> scaler -> model"
    assert plan.use_grid_search is True


def test_iteration_decision():
    decision = IterationDecision(
        action="refine_params",
        reasoning="Best model can be improved",
        refinement_instructions="Increase n_estimators",
        confidence=0.8,
    )
    assert decision.action == "refine_params"
    assert decision.confidence == 0.8


def test_final_report():
    report = FinalReport(
        best_model="RandomForest",
        best_metrics={"accuracy": 0.95},
        total_iterations=3,
        interpretation="RandomForest performed best",
        recommendations=["Try more data"],
    )
    assert report.best_model == "RandomForest"
    assert report.total_iterations == 3


# --- Utility tests ---


def test_strip_code_fences_python():
    text = '```python\nprint("hello")\n```'
    assert strip_code_fences(text) == 'print("hello")'


def test_strip_code_fences_plain():
    text = '```\nprint("hello")\n```'
    assert strip_code_fences(text) == 'print("hello")'


def test_strip_code_fences_no_fences():
    text = 'print("hello")'
    assert strip_code_fences(text) == 'print("hello")'


# --- Route decision tests (now at agents/sklearn/graph._route_decision) ---


def test_route_decision_accept():
    state = {"next_action": "accept"}
    assert _route_decision(state) == "finalize"


def test_route_decision_abort():
    state = {"next_action": "abort"}
    assert _route_decision(state) == "finalize"


def test_route_decision_fix_error():
    """fix_error now routes to error_research (web search before regenerating)."""
    state = {"next_action": "fix_error"}
    assert _route_decision(state) == "error_research"


def test_route_decision_refine_params():
    state = {"next_action": "refine_params"}
    assert _route_decision(state) == "generate_code"


def test_route_decision_try_new_algo():
    state = {"next_action": "try_new_algo"}
    assert _route_decision(state) == "generate_code"


def test_route_decision_feature_engineer():
    state = {"next_action": "feature_engineer"}
    assert _route_decision(state) == "generate_code"


def test_route_decision_default_aborts():
    """With no next_action, defaults to 'abort' which routes to finalize."""
    state = {}
    assert _route_decision(state) == "finalize"
