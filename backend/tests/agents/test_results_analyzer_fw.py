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
