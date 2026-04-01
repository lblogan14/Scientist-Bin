"""Tests for the base framework agent infrastructure.

Covers:
- BaseFrameworkAgent lifecycle and run() contract
- build_framework_graph() graph construction
- _route_decision and _route_validation routing functions
- validate_code node static analysis checks
- evaluate_on_test _parse_test_results helper
"""

from __future__ import annotations

import pytest

from scientist_bin_backend.agents.base.graph import (
    _route_decision,
    _route_validation,
    build_framework_graph,
)
from scientist_bin_backend.agents.base.nodes.code_validator import (
    MAX_VALIDATION_ATTEMPTS,
    _check_imports,
    _check_report_metric,
    _check_results_marker,
    _check_syntax,
)
from scientist_bin_backend.agents.base.nodes.test_evaluator import (
    _parse_test_results,
)
from scientist_bin_backend.agents.base.states import (
    BaseMLState,
    DataProfile,
    ExperimentRecord,
)

# ---------------------------------------------------------------------------
# BaseMLState TypedDict tests
# ---------------------------------------------------------------------------


def test_base_ml_state_creation():
    """BaseMLState can be created with minimal fields."""
    state: BaseMLState = {
        "objective": "Classify iris",
        "problem_type": "classification",
        "phase": "execution",
    }
    assert state["objective"] == "Classify iris"
    assert state["phase"] == "execution"


def test_base_ml_state_all_pipeline_fields():
    """BaseMLState accepts all upstream pipeline fields."""
    state: BaseMLState = {
        "objective": "Predict prices",
        "execution_plan": {"algorithms_to_try": ["Ridge"]},
        "analysis_report": "# Dataset Analysis",
        "split_data_paths": {
            "train": "/data/train.csv",
            "val": "/data/val.csv",
            "test": "/data/test.csv",
        },
        "problem_type": "regression",
        "data_profile": {"shape": [100, 5]},
        "phase": "execution",
    }
    assert state["split_data_paths"]["test"] == "/data/test.csv"
    assert state["execution_plan"]["algorithms_to_try"] == ["Ridge"]


def test_base_ml_state_validation_fields():
    """BaseMLState includes new validation fields."""
    state: BaseMLState = {
        "validation_error": "SyntaxError at line 5",
        "validation_attempts": 1,
        "phase": "execution",
    }
    assert state["validation_error"] == "SyntaxError at line 5"
    assert state["validation_attempts"] == 1


def test_base_ml_state_test_evaluation_fields():
    """BaseMLState includes test evaluation fields."""
    state: BaseMLState = {
        "test_metrics": {"test_accuracy": 0.93, "test_f1": 0.91},
        "test_evaluation_code": "import joblib\nmodel = joblib.load(...)",
        "phase": "done",
    }
    assert state["test_metrics"]["test_accuracy"] == 0.93
    assert state["test_evaluation_code"].startswith("import")


def test_data_profile_typed_dict():
    profile: DataProfile = {
        "shape": [150, 4],
        "column_names": ["a", "b", "c", "d"],
        "target_column": "species",
        "numeric_columns": ["a", "b", "c", "d"],
        "categorical_columns": [],
    }
    assert profile["shape"] == [150, 4]
    assert profile["target_column"] == "species"


def test_experiment_record_typed_dict():
    record: ExperimentRecord = {
        "iteration": 1,
        "algorithm": "RandomForestClassifier",
        "hyperparameters": {"n_estimators": 100},
        "metrics": {"accuracy": 0.95, "f1": 0.93},
        "training_time_seconds": 2.5,
        "timestamp": "2026-04-01T12:00:00Z",
    }
    assert record["algorithm"] == "RandomForestClassifier"
    assert record["metrics"]["accuracy"] == 0.95


# ---------------------------------------------------------------------------
# Routing function tests
# ---------------------------------------------------------------------------


class TestRouteDecision:
    """Tests for _route_decision — routes after analyze_results."""

    def test_accept_goes_to_evaluate_on_test(self):
        assert _route_decision({"next_action": "accept"}) == "evaluate_on_test"

    def test_abort_goes_to_evaluate_on_test(self):
        assert _route_decision({"next_action": "abort"}) == "evaluate_on_test"

    def test_fix_error_goes_to_error_research(self):
        assert _route_decision({"next_action": "fix_error"}) == "error_research"

    def test_refine_params_loops_to_generate_code(self):
        assert _route_decision({"next_action": "refine_params"}) == "generate_code"

    def test_try_new_algo_loops_to_generate_code(self):
        assert _route_decision({"next_action": "try_new_algo"}) == "generate_code"

    def test_feature_engineer_loops_to_generate_code(self):
        assert _route_decision({"next_action": "feature_engineer"}) == "generate_code"

    def test_default_no_action_goes_to_evaluate_on_test(self):
        assert _route_decision({}) == "evaluate_on_test"


class TestRouteValidation:
    """Tests for _route_validation — routes after validate_code."""

    def test_no_error_proceeds_to_execute(self):
        state = {"validation_error": None, "validation_attempts": 0}
        assert _route_validation(state) == "execute_code"

    def test_empty_string_error_proceeds_to_execute(self):
        state = {"validation_error": "", "validation_attempts": 0}
        assert _route_validation(state) == "execute_code"

    def test_error_below_max_retries_to_generate(self):
        state = {"validation_error": "SyntaxError", "validation_attempts": 1}
        assert _route_validation(state) == "generate_code"

    def test_error_at_max_retries_proceeds_to_execute(self):
        state = {
            "validation_error": "SyntaxError",
            "validation_attempts": MAX_VALIDATION_ATTEMPTS,
        }
        assert _route_validation(state) == "execute_code"

    def test_error_above_max_retries_proceeds_to_execute(self):
        state = {
            "validation_error": "SyntaxError",
            "validation_attempts": MAX_VALIDATION_ATTEMPTS + 1,
        }
        assert _route_validation(state) == "execute_code"


# ---------------------------------------------------------------------------
# Code validator individual check tests
# ---------------------------------------------------------------------------


class TestCheckSyntax:
    def test_valid_code(self):
        assert _check_syntax("x = 1 + 2\nprint(x)") is None

    def test_syntax_error(self):
        result = _check_syntax("def foo(\n")
        assert result is not None
        assert "SyntaxError" in result

    def test_indentation_error(self):
        result = _check_syntax("def foo():\nx = 1")
        assert result is not None

    def test_multiline_valid(self):
        code = "import os\nimport json\n\ndef main():\n    print('hello')\n"
        assert _check_syntax(code) is None

    def test_empty_code(self):
        assert _check_syntax("") is None


class TestCheckImports:
    def test_stdlib_imports(self):
        assert _check_imports("import os\nimport json\nimport sys") is None

    def test_missing_import(self):
        result = _check_imports("import nonexistent_xyz_package_999")
        assert result is not None
        assert "nonexistent_xyz_package_999" in result

    def test_from_import_missing(self):
        result = _check_imports("from nonexistent_xyz_999 import foo")
        assert result is not None
        assert "nonexistent_xyz_999" in result

    def test_nested_import(self):
        assert _check_imports("import os.path") is None

    def test_from_nested_import(self):
        assert _check_imports("from pathlib import Path") is None


class TestCheckResultsMarker:
    def test_marker_present(self):
        code = 'print("===RESULTS===")\nprint(json.dumps(results))'
        assert _check_results_marker(code) is None

    def test_marker_absent(self):
        result = _check_results_marker("print(results)")
        assert result is not None
        assert "===RESULTS===" in result

    def test_marker_in_string(self):
        code = 'marker = "===RESULTS==="\nprint(marker)'
        assert _check_results_marker(code) is None


class TestCheckReportMetric:
    def test_present(self):
        assert _check_report_metric("report_metric('accuracy', 0.95)") is None

    def test_absent(self):
        result = _check_report_metric("print('accuracy', 0.95)")
        assert result is not None
        assert "report_metric" in result

    def test_in_comment(self):
        code = "# report_metric is pre-defined\nreport_metric('f1', 0.88)"
        assert _check_report_metric(code) is None


# ---------------------------------------------------------------------------
# _parse_test_results tests
# ---------------------------------------------------------------------------


class TestParseTestResults:
    def test_valid_results(self):
        stdout = (
            'some output\n===TEST_RESULTS===\n{"algorithm": "RF", "metrics": {"test_acc": 0.95}}'
        )
        result = _parse_test_results(stdout)
        assert result is not None
        assert result["algorithm"] == "RF"
        assert result["metrics"]["test_acc"] == 0.95

    def test_no_marker(self):
        stdout = '{"algorithm": "RF", "metrics": {"test_acc": 0.95}}'
        assert _parse_test_results(stdout) is None

    def test_invalid_json(self):
        stdout = "===TEST_RESULTS===\nnot json at all"
        assert _parse_test_results(stdout) is None

    def test_trailing_output(self):
        stdout = (
            '===TEST_RESULTS===\n{"algorithm": "RF", "metrics": {"test_acc": 0.95}}\nsome trailing'
        )
        result = _parse_test_results(stdout)
        assert result is not None
        assert result["algorithm"] == "RF"

    def test_empty_stdout(self):
        assert _parse_test_results("") is None

    def test_multiple_markers(self):
        stdout = (
            "first===TEST_RESULTS===ignored\n"
            "===TEST_RESULTS===\n"
            '{"algorithm": "SVM", "metrics": {}}'
        )
        result = _parse_test_results(stdout)
        assert result is not None
        assert result["algorithm"] == "SVM"

    def test_nested_json(self):
        stdout = (
            "===TEST_RESULTS===\n"
            '{"algorithm": "RF", "metrics": '
            '{"test_acc": 0.95, "test_f1": 0.93}, '
            '"test_samples": 30}'
        )
        result = _parse_test_results(stdout)
        assert result is not None
        assert result["test_samples"] == 30


# ---------------------------------------------------------------------------
# build_framework_graph tests
# ---------------------------------------------------------------------------


class TestBuildFrameworkGraph:
    """Tests for build_framework_graph — verifies graph structure."""

    @staticmethod
    def _dummy_generate_code(state: dict) -> dict:
        return {"generated_code": "print('hello')", "messages": []}

    @staticmethod
    def _dummy_error_research(state: dict) -> dict:
        return {"search_results": "fix suggestion", "messages": []}

    def test_builds_with_error_research(self):
        graph = build_framework_graph(
            state_class=BaseMLState,
            generate_code_node=self._dummy_generate_code,
            error_research_node=self._dummy_error_research,
        )
        assert graph is not None

    def test_builds_without_error_research(self):
        graph = build_framework_graph(
            state_class=BaseMLState,
            generate_code_node=self._dummy_generate_code,
            error_research_node=None,
        )
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        graph = build_framework_graph(
            state_class=BaseMLState,
            generate_code_node=self._dummy_generate_code,
            error_research_node=self._dummy_error_research,
        )
        node_names = set(graph.get_graph().nodes.keys())
        expected = {
            "__start__",
            "__end__",
            "generate_code",
            "validate_code",
            "execute_code",
            "analyze_results",
            "error_research",
            "evaluate_on_test",
            "finalize",
        }
        assert expected.issubset(node_names)

    def test_graph_without_error_research_excludes_node(self):
        graph = build_framework_graph(
            state_class=BaseMLState,
            generate_code_node=self._dummy_generate_code,
            error_research_node=None,
        )
        node_names = set(graph.get_graph().nodes.keys())
        assert "error_research" not in node_names


# ---------------------------------------------------------------------------
# BaseFrameworkAgent tests
# ---------------------------------------------------------------------------


class TestBaseFrameworkAgent:
    """Tests for BaseFrameworkAgent abstract class."""

    def test_cannot_instantiate_directly(self):
        from scientist_bin_backend.agents.base.agent import BaseFrameworkAgent

        with pytest.raises(TypeError):
            BaseFrameworkAgent()

    def test_sklearn_agent_extends_base(self):
        from scientist_bin_backend.agents.base.agent import BaseFrameworkAgent
        from scientist_bin_backend.agents.frameworks.sklearn.agent import SklearnAgent

        assert issubclass(SklearnAgent, BaseFrameworkAgent)

    def test_sklearn_agent_has_framework_name(self):
        from scientist_bin_backend.agents.frameworks.sklearn.agent import SklearnAgent

        agent = SklearnAgent()
        assert agent.framework_name == "sklearn"

    def test_sklearn_agent_has_graph(self):
        from scientist_bin_backend.agents.frameworks.sklearn.agent import SklearnAgent

        agent = SklearnAgent()
        assert agent.graph is not None
