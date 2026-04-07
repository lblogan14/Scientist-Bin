"""Test evaluation node — evaluates the best model on the held-out test set.

Runs after the iteration loop accepts a model (``next_action == "accept"``).
Uses 1 LLM call to generate a test-evaluation script, then executes it via
the same ``CodeRunner`` infrastructure.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.base.prompts import TEST_EVALUATION_PROMPT
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model


def _parse_test_results(stdout: str) -> dict | None:
    """Extract test results JSON from stdout using the ===TEST_RESULTS=== marker."""
    marker = "===TEST_RESULTS==="
    if marker not in stdout:
        return None

    json_str = stdout.split(marker)[-1].strip()
    brace_count = 0
    json_end = -1
    in_string = False
    escape_next = False

    for i, ch in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            brace_count += 1
        elif ch == "}":
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break

    if json_end == -1:
        return None

    try:
        return json.loads(json_str[:json_end])
    except json.JSONDecodeError:
        return None


async def evaluate_on_test(state: dict) -> dict:
    """Evaluate the best model on the held-out test set.

    Generates a test evaluation script via LLM, then executes it.
    Returns ``test_metrics`` dict for the summary agent.
    """
    experiment_id = state.get("experiment_id", "default")
    best_experiment = state.get("best_experiment")
    split_data_paths = state.get("split_data_paths", {})
    test_path = split_data_paths.get("test")

    # Skip if no test set or no best experiment
    if not test_path or not best_experiment:
        msg = "Skipping test evaluation: "
        msg += "no test set available." if not test_path else "no best experiment."
        return {
            "test_metrics": None,
            "test_evaluation_code": None,
            "messages": [HumanMessage(content=msg)],
        }

    test_path_resolved = str(Path(test_path).resolve())
    best_algorithm = best_experiment.get("algorithm", "unknown")
    best_metrics = best_experiment.get("metrics", {})
    best_hyperparameters = best_experiment.get("hyperparameters", {})

    # Generate test evaluation script
    llm = get_agent_model(state.get("framework_name") or "sklearn")
    prompt = TEST_EVALUATION_PROMPT.format(
        objective=state.get("objective", ""),
        problem_type=state.get("problem_type", "classification"),
        best_algorithm=best_algorithm,
        best_metrics=json.dumps(best_metrics),
        best_hyperparameters=json.dumps(best_hyperparameters),
        test_file_path=test_path_resolved,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    code = extract_text_content(response.content)

    # Strip markdown fences if present
    from scientist_bin_backend.agents.base.utils import strip_code_fences

    code = strip_code_fences(code)

    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="agent_activity",
            data={"action": "evaluate_on_test", "algorithm": best_algorithm},
        ),
    )

    # Execute the test evaluation script
    run_id = f"test_{uuid.uuid4().hex[:8]}"
    runner = CodeRunner()
    result = await runner.execute(
        RunConfig(
            experiment_id=experiment_id,
            code=code,
            run_id=run_id,
            timeout_seconds=120,
        ),
    )

    # Parse test results
    test_metrics: dict | None = None
    test_confusion_matrix: dict | None = None
    test_residual_stats: dict | None = None
    test_cluster_scatter: list | None = None
    test_actual_vs_predicted: list | None = None
    if result.success:
        parsed = _parse_test_results(result.stdout)
        if parsed:
            if "metrics" in parsed:
                test_metrics = parsed["metrics"]
            test_confusion_matrix = parsed.get("confusion_matrix")
            test_residual_stats = parsed.get("residual_stats")
            test_cluster_scatter = parsed.get("cluster_scatter")
            test_actual_vs_predicted = parsed.get("actual_vs_predicted")

    if test_metrics:
        status_msg = f"Test evaluation completed. Metrics: {json.dumps(test_metrics)}"
    elif not result.success:
        status_msg = "Test evaluation failed."
    else:
        status_msg = "Test evaluation produced no parseable results."

    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="agent_activity",
            data={
                "action": "test_evaluation_complete",
                "success": test_metrics is not None,
                "metrics": test_metrics,
            },
        ),
    )

    # Bundle enriched test diagnostics alongside metrics
    test_diagnostics: dict = {}
    if test_confusion_matrix:
        test_diagnostics["confusion_matrix"] = test_confusion_matrix
    if test_residual_stats:
        test_diagnostics["residual_stats"] = test_residual_stats
    if test_cluster_scatter:
        test_diagnostics["cluster_scatter"] = test_cluster_scatter
    if test_actual_vs_predicted:
        test_diagnostics["actual_vs_predicted"] = test_actual_vs_predicted

    return {
        "test_metrics": test_metrics,
        "test_evaluation_code": code,
        "test_diagnostics": test_diagnostics if test_diagnostics else None,
        "messages": [HumanMessage(content=status_msg)],
    }
