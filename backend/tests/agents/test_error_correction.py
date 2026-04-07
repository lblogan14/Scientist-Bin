"""Tests for the error correction and retry flow in framework agents.

Verifies that the graph routing correctly handles fix_error, accept, and
other next_action values, and that the error_research node produces
search results for downstream code regeneration.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scientist_bin_backend.agents.base.graph import _route_decision

# ---------------------------------------------------------------------------
# Routing decision tests
# ---------------------------------------------------------------------------


def test_route_decision_fix_error():
    """fix_error routes to error_research."""
    assert _route_decision({"next_action": "fix_error"}) == "error_research"


def test_route_decision_accept():
    """accept routes to evaluate_on_test."""
    assert _route_decision({"next_action": "accept"}) == "evaluate_on_test"


def test_route_decision_abort():
    """abort routes to evaluate_on_test (same as accept)."""
    assert _route_decision({"next_action": "abort"}) == "evaluate_on_test"


def test_route_decision_refine_params():
    """refine_params routes back to generate_code."""
    assert _route_decision({"next_action": "refine_params"}) == "generate_code"


def test_route_decision_try_new_algo():
    """try_new_algo routes back to generate_code."""
    assert _route_decision({"next_action": "try_new_algo"}) == "generate_code"


def test_route_decision_feature_engineer():
    """feature_engineer routes back to generate_code."""
    assert _route_decision({"next_action": "feature_engineer"}) == "generate_code"


def test_route_decision_missing_key_defaults_to_abort():
    """Missing next_action key defaults to 'abort' → evaluate_on_test."""
    assert _route_decision({}) == "evaluate_on_test"


def test_route_decision_none_falls_through_to_generate():
    """Explicit None next_action falls through to generate_code."""
    assert _route_decision({"next_action": None}) == "generate_code"


# ---------------------------------------------------------------------------
# Error research node tests
# ---------------------------------------------------------------------------


def _has_sklearn_error_research() -> bool:
    """Check if the sklearn error_research node is importable."""
    try:
        from scientist_bin_backend.agents.frameworks.sklearn.nodes.error_researcher import (  # noqa: F401
            error_research,
        )

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not _has_sklearn_error_research(),
    reason="sklearn error_research node not found",
)
async def test_error_research_produces_search_results():
    """The error_research node should add search_results to its return dict."""
    from scientist_bin_backend.agents.frameworks.sklearn.nodes.error_researcher import (
        error_research,
    )

    state = {
        "execution_error": "ModuleNotFoundError: No module named 'catboost'",
        "execution_output": "",
        "experiment_id": "test-err-research",
        "current_iteration": 0,
        "messages": [],
    }

    mock_result = "Try installing catboost: pip install catboost"
    with patch(
        "scientist_bin_backend.agents.frameworks.sklearn.nodes.error_researcher.search_with_gemini",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await error_research(state)

    assert "search_results" in result
    assert result["search_results"] is not None
    assert len(result["search_results"]) > 0
