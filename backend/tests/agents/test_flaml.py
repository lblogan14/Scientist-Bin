"""Tests for the FLAML AutoML subagent schemas and framework-specific code.

Base infrastructure tests (routing, validation, state, graph building) are in
``test_base_framework.py``.  This file covers FLAML-specific schemas and
the FlamlAgent wrapper.
"""

from __future__ import annotations

from scientist_bin_backend.agents.frameworks.flaml.schemas import FlamlStrategyPlan

# --- FLAML schema tests ---


def test_flaml_strategy_plan_defaults():
    plan = FlamlStrategyPlan()
    assert plan.time_budget == 120
    assert plan.estimator_list == []
    assert plan.metric is None
    assert plan.ts_period is None
    assert plan.eval_method == "auto"
    assert plan.n_splits == 5


def test_flaml_strategy_plan_custom():
    plan = FlamlStrategyPlan(
        time_budget=300,
        estimator_list=["lgbm", "xgboost", "catboost"],
        metric="accuracy",
        ts_period=12,
        eval_method="cv",
        n_splits=3,
    )
    assert plan.time_budget == 300
    assert "lgbm" in plan.estimator_list
    assert plan.metric == "accuracy"
    assert plan.ts_period == 12


# --- FLAML agent wrapper tests ---


def test_flaml_agent_instantiation():
    from scientist_bin_backend.agents.frameworks.flaml.agent import FlamlAgent

    agent = FlamlAgent()
    assert agent.framework_name == "flaml"
    assert agent.graph is not None


def test_flaml_agent_has_examples():
    from scientist_bin_backend.agents.frameworks.flaml.agent import EXAMPLES

    assert len(EXAMPLES) >= 3
    problem_types = {ex["problem_type"] for ex in EXAMPLES}
    assert "classification" in problem_types
    assert "regression" in problem_types
    assert "ts_forecast" in problem_types

    for ex in EXAMPLES:
        assert "name" in ex
        assert "objective" in ex
        assert "problem_type" in ex
        assert "execution_plan" in ex


# --- FLAML state tests ---


def test_flaml_state_has_base_fields():
    from scientist_bin_backend.agents.frameworks.flaml.states import FlamlState

    # FlamlState is a TypedDict — verify it has the FLAML-specific keys
    annotations = FlamlState.__annotations__
    assert "time_budget" in annotations
    assert "estimator_list" in annotations
    assert "flaml_metric" in annotations
    assert "ts_period" in annotations
    # Also has base fields
    assert "objective" in annotations
    assert "generated_code" in annotations
    assert "experiment_history" in annotations


# --- Framework registry tests ---


def test_flaml_in_framework_registry():
    from scientist_bin_backend.agents.central.nodes.router import FRAMEWORK_REGISTRY

    assert "flaml" in FRAMEWORK_REGISTRY
    assert "FlamlAgent" in FRAMEWORK_REGISTRY["flaml"]


def test_flaml_in_agent_models():
    # Build with explicit settings to avoid requiring GOOGLE_API_KEY
    from unittest.mock import MagicMock

    from scientist_bin_backend.utils.llm import _build_agent_models

    settings = MagicMock()
    settings.gemini_model_flash = "gemini-flash"
    settings.gemini_model_pro = "gemini-pro"
    models = _build_agent_models(settings)
    assert "flaml" in models
    assert models["flaml"] == "gemini-pro"
