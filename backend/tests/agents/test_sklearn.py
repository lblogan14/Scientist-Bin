"""Tests for the sklearn subagent schemas and framework-specific code.

Base infrastructure tests (routing, validation, state, graph building) are in
``test_base_framework.py``.  This file covers sklearn-specific schemas and
the SklearnAgent wrapper.
"""

from __future__ import annotations

from scientist_bin_backend.agents.base.schemas import (
    AlgorithmCandidate,
    FinalReport,
    IterationDecision,
    ProblemClassification,
    StrategyPlan,
)
from scientist_bin_backend.agents.base.utils import strip_code_fences
from scientist_bin_backend.agents.frameworks.sklearn.schemas import SklearnStrategyPlan

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


# --- Sklearn agent wrapper tests ---


def test_sklearn_agent_instantiation():
    from scientist_bin_backend.agents.frameworks.sklearn.agent import SklearnAgent

    agent = SklearnAgent()
    assert agent.framework_name == "sklearn"
    assert agent.graph is not None


def test_sklearn_agent_has_examples():
    from scientist_bin_backend.agents.frameworks.sklearn.agent import EXAMPLES

    assert len(EXAMPLES) >= 2
    for ex in EXAMPLES:
        assert "name" in ex
        assert "objective" in ex
        assert "problem_type" in ex
        assert "execution_plan" in ex
