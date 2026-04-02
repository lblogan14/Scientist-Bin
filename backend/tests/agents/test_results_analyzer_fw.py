"""Tests for framework_name-aware LLM selection in results_analyzer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scientist_bin_backend.agents.base.nodes.results_analyzer import (
    analyze_results,
    finalize,
)


def _make_analyze_state(*, framework_name: str | None = "sklearn") -> dict:
    """Build a minimal state for analyze_results with a successful execution."""
    state = {
        "execution_success": True,
        "execution_output": "",
        "execution_error": "",
        "current_iteration": 0,
        "max_iterations": 5,
        "experiment_history": [],
        "experiment_id": "test-exp",
        "execution_results_json": {
            "results": [
                {
                    "algorithm": "LogisticRegression",
                    "metrics": {"accuracy": 0.9},
                    "best_params": {},
                    "training_time": 1.0,
                }
            ],
            "best_model": "LogisticRegression",
        },
        "success_criteria": {"accuracy": 0.95},
        "objective": "Classify iris",
        "problem_type": "classification",
    }
    if framework_name is not None:
        state["framework_name"] = framework_name
    return state


def _make_finalize_state(*, framework_name: str | None = "sklearn") -> dict:
    """Build a minimal state for finalize."""
    state = {
        "best_experiment": {
            "algorithm": "RandomForest",
            "metrics": {"accuracy": 0.95},
        },
        "experiment_history": [
            {
                "iteration": 1,
                "algorithm": "RandomForest",
                "metrics": {"accuracy": 0.95},
                "training_time_seconds": 2.0,
            }
        ],
        "data_profile": {"statistics_summary": "150 rows, 4 features"},
        "experiment_id": "test-exp",
        "objective": "Classify iris",
        "problem_type": "classification",
        "current_iteration": 1,
    }
    if framework_name is not None:
        state["framework_name"] = framework_name
    return state


@pytest.mark.asyncio
async def test_analyze_results_uses_framework_name_for_llm():
    """analyze_results should pass framework_name to get_agent_model."""
    mock_llm = MagicMock()
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(
        return_value=MagicMock(
            action="accept",
            refinement_instructions=None,
            confidence=0.9,
            reasoning="Good results",
        )
    )
    mock_llm.with_structured_output.return_value = mock_structured

    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
            return_value=mock_llm,
        ) as mock_get,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_analyze_state(framework_name="sklearn")
        await analyze_results(state)
        mock_get.assert_called_once_with("sklearn")


@pytest.mark.asyncio
async def test_analyze_results_defaults_to_sklearn():
    """analyze_results should default to 'sklearn' when framework_name is absent."""
    mock_llm = MagicMock()
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(
        return_value=MagicMock(
            action="accept",
            refinement_instructions=None,
            confidence=0.9,
            reasoning="Good enough",
        )
    )
    mock_llm.with_structured_output.return_value = mock_structured

    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
            return_value=mock_llm,
        ) as mock_get,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_analyze_state(framework_name=None)
        await analyze_results(state)
        mock_get.assert_called_once_with("sklearn")


@pytest.mark.asyncio
async def test_finalize_uses_framework_name_for_llm():
    """finalize should pass framework_name to get_agent_model."""
    mock_llm = MagicMock()
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(
        return_value=MagicMock(
            best_model="RandomForest",
            best_metrics={"accuracy": 0.95},
            total_iterations=1,
            interpretation="Good model",
            recommendations=["Try more data"],
        )
    )
    mock_llm.with_structured_output.return_value = mock_structured

    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
            return_value=mock_llm,
        ) as mock_get,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_finalize_state(framework_name="sklearn")
        await finalize(state)
        mock_get.assert_called_once_with("sklearn")


@pytest.mark.asyncio
async def test_finalize_defaults_to_sklearn():
    """finalize should default to 'sklearn' when framework_name is absent."""
    mock_llm = MagicMock()
    mock_structured = AsyncMock()
    mock_structured.ainvoke = AsyncMock(
        return_value=MagicMock(
            best_model="LogisticRegression",
            best_metrics={"accuracy": 0.90},
            total_iterations=1,
            interpretation="OK model",
            recommendations=["Try tuning"],
        )
    )
    mock_llm.with_structured_output.return_value = mock_structured

    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
            return_value=mock_llm,
        ) as mock_get,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_finalize_state(framework_name=None)
        await finalize(state)
        mock_get.assert_called_once_with("sklearn")


# ---------------------------------------------------------------------------
# analyze_results deterministic error paths (no LLM call needed)
# ---------------------------------------------------------------------------


def _make_error_state(*, execution_error: str = "ModuleNotFoundError: No module named 'xgb'"):
    """Build a state where execution failed (no results)."""
    return {
        "execution_success": False,
        "execution_output": "",
        "execution_error": execution_error,
        "current_iteration": 0,
        "max_iterations": 5,
        "experiment_history": [],
        "experiment_id": "test-exp",
        "execution_results_json": None,
        "success_criteria": {"accuracy": 0.95},
        "objective": "Classify iris",
        "problem_type": "classification",
        "framework_name": "sklearn",
    }


def _make_budget_exhausted_state(
    *,
    best_experiment=None,
    current_iteration: int = 5,
    include_results: bool = True,
):
    """Build a state where max_iterations has been reached."""
    results_json = None
    if include_results:
        results_json = {
            "results": [
                {
                    "algorithm": "LogisticRegression",
                    "metrics": {"accuracy": 0.88},
                    "best_params": {},
                    "training_time": 1.0,
                }
            ],
            "best_model": "LogisticRegression",
        }
    return {
        "execution_success": True,
        "execution_output": "",
        "execution_error": "",
        "current_iteration": current_iteration - 1,  # +1 is applied inside
        "max_iterations": current_iteration,
        "experiment_history": [],
        "experiment_id": "test-exp",
        "execution_results_json": results_json,
        "success_criteria": {},
        "objective": "Classify iris",
        "problem_type": "classification",
        "framework_name": "sklearn",
        "best_experiment": best_experiment,
    }


@pytest.mark.asyncio
async def test_analyze_results_execution_failed_fix_error():
    """When execution_success=False, next_action is 'fix_error' without LLM call."""
    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
        ) as mock_get_model,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_error_state()
        result = await analyze_results(state)

        assert result["next_action"] == "fix_error"
        ctx = result["refinement_context"].lower()
        assert "failed" in ctx or "error" in ctx
        # The LLM should NOT be invoked for deterministic error handling
        mock_get_model.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_results_budget_exhausted_with_best_accepts():
    """When max_iterations reached with a best_experiment, next_action is 'accept'."""
    best = {
        "iteration": 3,
        "algorithm": "RandomForest",
        "metrics": {"accuracy": 0.92},
    }
    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
        ) as mock_get_model,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_budget_exhausted_state(best_experiment=best, current_iteration=5)
        result = await analyze_results(state)

        assert result["next_action"] == "accept"
        # Budget exhausted is also deterministic — no LLM call
        mock_get_model.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_results_budget_exhausted_without_best_aborts():
    """When max_iterations reached without a best_experiment, next_action is 'abort'."""
    with (
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_agent_model",
        ) as mock_get_model,
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.event_bus",
            emit=AsyncMock(),
        ),
        patch(
            "scientist_bin_backend.agents.base.nodes.results_analyzer.get_journal_for_experiment",
            return_value=MagicMock(),
        ),
    ):
        state = _make_budget_exhausted_state(
            best_experiment=None, current_iteration=5, include_results=False
        )
        result = await analyze_results(state)

        assert result["next_action"] == "abort"
        # Budget exhausted is also deterministic — no LLM call
        mock_get_model.assert_not_called()
