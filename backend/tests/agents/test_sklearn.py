"""Tests for the sklearn subagent schemas, utilities, and routing logic."""

from langgraph.graph import END

from scientist_bin_backend.agents.sklearn.nodes.evaluator import should_retry
from scientist_bin_backend.agents.sklearn.schemas import (
    CodeGenerationResult,
    EvaluationResult,
    SklearnPlan,
)
from scientist_bin_backend.agents.sklearn.utils import strip_code_fences

# --- Schema tests ---


def test_sklearn_plan_defaults():
    plan = SklearnPlan(approach="Random forest classification")
    assert plan.approach == "Random forest classification"
    assert plan.algorithms == []
    assert plan.preprocessing_steps == []


def test_sklearn_plan_full():
    plan = SklearnPlan(
        approach="Ensemble classification",
        algorithms=["RandomForest", "GradientBoosting"],
        preprocessing_steps=["StandardScaler", "OneHotEncoder"],
        evaluation_metrics=["accuracy", "f1"],
    )
    assert len(plan.algorithms) == 2


def test_code_generation_result():
    result = CodeGenerationResult(code="print('hello')", explanation="A simple test")
    assert "hello" in result.code


def test_evaluation_result_success():
    result = EvaluationResult(success=True, metrics={"accuracy": 0.95})
    assert result.success is True
    assert result.errors is None


def test_evaluation_result_failure():
    result = EvaluationResult(
        success=False,
        errors=["Missing import"],
        suggestions=["Add import sklearn"],
    )
    assert result.success is False
    assert len(result.errors) == 1


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


# --- Retry routing tests ---


def test_should_retry_success():
    state = {
        "evaluation_results": {"success": True},
        "retry_count": 1,
        "max_retries": 3,
    }
    assert should_retry(state) == END


def test_should_retry_failure():
    state = {
        "evaluation_results": {"success": False},
        "retry_count": 1,
        "max_retries": 3,
    }
    assert should_retry(state) == "generate_code"


def test_should_retry_max_reached():
    state = {
        "evaluation_results": {"success": False},
        "retry_count": 3,
        "max_retries": 3,
    }
    assert should_retry(state) == END
