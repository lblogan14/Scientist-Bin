"""Code validation node — static analysis before execution.

This node consumes ZERO LLM tokens. It performs:
1. Syntax check via compile()
2. Import availability check via importlib.util.find_spec()
3. Results marker check (===RESULTS===)
4. report_metric() call check

On failure the graph routes back to generate_code with the validation
error as context (max ``MAX_VALIDATION_ATTEMPTS`` retries before
proceeding to execution anyway).
"""

from __future__ import annotations

import ast
import importlib.util

from langchain_core.messages import HumanMessage

from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

MAX_VALIDATION_ATTEMPTS = 2


def _check_syntax(code: str) -> str | None:
    """Return error message if code has syntax errors, else None."""
    try:
        compile(code, "<generated>", "exec")
    except SyntaxError as exc:
        return f"SyntaxError at line {exc.lineno}: {exc.msg}"
    return None


def _check_imports(code: str) -> str | None:
    """Return error message if any top-level import is unavailable."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # Already caught by _check_syntax

    missing: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                if importlib.util.find_spec(top_level) is None:
                    missing.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level = node.module.split(".")[0]
                if importlib.util.find_spec(top_level) is None:
                    missing.append(node.module)

    if missing:
        return f"Missing imports (not installed): {', '.join(missing)}"
    return None


def _check_results_marker(code: str) -> str | None:
    """Warn if the code doesn't print the ===RESULTS=== marker."""
    if "===RESULTS===" not in code:
        return (
            "Code does not contain the '===RESULTS===' output marker. "
            "The script must print '===RESULTS===' followed by a JSON object."
        )
    return None


def _check_report_metric(code: str) -> str | None:
    """Warn if the code doesn't call report_metric()."""
    if "report_metric" not in code:
        return (
            "Code does not call report_metric(). "
            "The script must call report_metric(name, value) for each key metric."
        )
    return None


async def validate_code(state: dict) -> dict:
    """Validate generated code before execution. Zero LLM tokens.

    Returns ``validation_error`` (non-empty string) on failure so the
    graph can route back to the code generator.
    """
    code = state.get("generated_code", "")
    experiment_id = state.get("experiment_id")
    validation_attempts = state.get("validation_attempts", 0)

    if not code:
        return {
            "validation_error": "No code to validate",
            "validation_attempts": validation_attempts + 1,
            "messages": [HumanMessage(content="No code was generated to validate.")],
        }

    errors: list[str] = []

    # 1. Syntax check (blocking — code can't run at all)
    syntax_err = _check_syntax(code)
    if syntax_err:
        errors.append(syntax_err)

    # 2. Import check (blocking — will fail on import)
    if not syntax_err:
        import_err = _check_imports(code)
        if import_err:
            errors.append(import_err)

    # 3. Results marker check (warning — code may run but output won't parse)
    marker_err = _check_results_marker(code)
    if marker_err:
        errors.append(marker_err)

    # 4. report_metric check (warning)
    metric_err = _check_report_metric(code)
    if metric_err:
        errors.append(metric_err)

    if errors:
        validation_error = "\n".join(errors)

        if experiment_id:
            await event_bus.emit(
                experiment_id,
                ExperimentEvent(
                    event_type="agent_activity",
                    data={
                        "action": "validate_code",
                        "result": "failed",
                        "iteration": state.get("current_iteration", 0),
                        "errors": errors,
                        "attempt": validation_attempts + 1,
                    },
                ),
            )

        return {
            "validation_error": validation_error,
            "validation_attempts": validation_attempts + 1,
            "messages": [
                HumanMessage(
                    content=(
                        f"Code validation failed (attempt {validation_attempts + 1}):"
                        f"\n{validation_error}"
                    )
                )
            ],
        }

    # Validation passed
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "action": "validate_code",
                    "result": "passed",
                    "iteration": state.get("current_iteration", 0),
                },
            ),
        )

    return {
        "validation_error": None,
        "validation_attempts": validation_attempts,
        "messages": [HumanMessage(content="Code validation passed.")],
    }
