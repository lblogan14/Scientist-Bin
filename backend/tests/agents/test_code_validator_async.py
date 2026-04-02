"""Tests for the validate_code async node in agents/base/nodes/code_validator.py.

Covers:
- No generated_code in state returns error
- Syntax error code emits event and sets validation_error
- Valid code returns no error
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scientist_bin_backend.agents.base.nodes.code_validator import validate_code


@pytest.fixture()
def _mock_event_bus():
    """Patch event_bus.emit to prevent real event emission."""
    with patch(
        "scientist_bin_backend.agents.base.nodes.code_validator.event_bus",
        emit=AsyncMock(),
    ) as mock_bus:
        yield mock_bus


class TestValidateCodeNoCode:
    async def test_no_generated_code_returns_error(self, _mock_event_bus):
        state = {"generated_code": "", "experiment_id": "test-exp"}
        result = await validate_code(state)

        assert result["validation_error"] == "No code to validate"
        assert result["validation_attempts"] == 1
        assert len(result["messages"]) == 1
        assert "No code was generated" in result["messages"][0].content

    async def test_missing_generated_code_key_returns_error(self, _mock_event_bus):
        state = {"experiment_id": "test-exp"}
        result = await validate_code(state)

        assert result["validation_error"] == "No code to validate"
        assert result["validation_attempts"] == 1


class TestValidateCodeSyntaxError:
    async def test_syntax_error_sets_validation_error(self, _mock_event_bus):
        state = {
            "generated_code": "def foo(\n",
            "experiment_id": "test-exp",
            "validation_attempts": 0,
            "current_iteration": 1,
        }
        result = await validate_code(state)

        assert result["validation_error"] is not None
        assert "SyntaxError" in result["validation_error"]
        assert result["validation_attempts"] == 1

    async def test_syntax_error_emits_event(self, _mock_event_bus):
        state = {
            "generated_code": "def foo(\n",
            "experiment_id": "test-exp",
            "validation_attempts": 0,
        }
        await validate_code(state)

        _mock_event_bus.emit.assert_called_once()
        call_args = _mock_event_bus.emit.call_args
        assert call_args[0][0] == "test-exp"
        event = call_args[0][1]
        assert event.event_type == "agent_activity"
        assert event.data["action"] == "validate_code"
        assert event.data["result"] == "failed"

    async def test_syntax_error_increments_attempts(self, _mock_event_bus):
        state = {
            "generated_code": "x = (",
            "experiment_id": "test-exp",
            "validation_attempts": 1,
        }
        result = await validate_code(state)

        assert result["validation_attempts"] == 2


class TestValidateCodeValid:
    async def test_valid_code_returns_no_error(self, _mock_event_bus):
        code = (
            "import json\n"
            "import os\n"
            "results = {'algorithm': 'RF', 'metrics': {}}\n"
            "report_metric('accuracy', 0.95)\n"
            'print("===RESULTS===")\n'
            "print(json.dumps(results))\n"
        )
        state = {
            "generated_code": code,
            "experiment_id": "test-exp",
            "validation_attempts": 0,
        }
        result = await validate_code(state)

        assert result["validation_error"] is None
        assert "passed" in result["messages"][0].content

    async def test_valid_code_emits_passed_event(self, _mock_event_bus):
        code = (
            "import json\n"
            "report_metric('accuracy', 0.95)\n"
            'print("===RESULTS===")\n'
            "print(json.dumps({}))\n"
        )
        state = {
            "generated_code": code,
            "experiment_id": "test-exp",
            "validation_attempts": 0,
        }
        await validate_code(state)

        _mock_event_bus.emit.assert_called_once()
        event = _mock_event_bus.emit.call_args[0][1]
        assert event.data["result"] == "passed"

    async def test_valid_code_preserves_attempt_count(self, _mock_event_bus):
        code = (
            "import os\n"
            "report_metric('f1', 0.88)\n"
            'print("===RESULTS===")\n'
            "print('{}')\n"
        )
        state = {
            "generated_code": code,
            "experiment_id": "test-exp",
            "validation_attempts": 2,
        }
        result = await validate_code(state)

        # On success, validation_attempts is NOT incremented
        assert result["validation_attempts"] == 2


class TestValidateCodeNoExperimentId:
    async def test_no_experiment_id_does_not_emit(self, _mock_event_bus):
        """When experiment_id is not in state, no event is emitted."""
        state = {"generated_code": "", "validation_attempts": 0}
        result = await validate_code(state)

        assert result["validation_error"] == "No code to validate"
        _mock_event_bus.emit.assert_not_called()

    async def test_valid_code_no_experiment_id(self, _mock_event_bus):
        code = (
            "report_metric('acc', 1.0)\n"
            'print("===RESULTS===")\n'
            "print('{}')\n"
        )
        state = {"generated_code": code, "validation_attempts": 0}
        result = await validate_code(state)

        assert result["validation_error"] is None
        _mock_event_bus.emit.assert_not_called()
