"""Code execution node — runs generated code in a sandboxed subprocess.

This node consumes ZERO LLM tokens. It:
1. Estimates training duration from data profile
2. Computes dynamic timeout
3. Writes code to a temp directory
4. Launches a subprocess
5. Monitors metrics file for real-time updates
6. Emits events for frontend streaming
7. Waits for completion
8. Parses and returns results
"""

from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage

from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.estimator import (
    compute_dynamic_timeout,
    estimate_training_duration,
    suggest_data_subset_size,
)
from scientist_bin_backend.execution.journal import get_journal_for_experiment
from scientist_bin_backend.execution.runner import CodeRunner, RunConfig


async def execute_code(state: dict) -> dict:
    """Execute generated code in a sandboxed subprocess. Zero LLM tokens."""
    experiment_id = state.get("experiment_id", "default")
    run_id = uuid.uuid4().hex[:12]
    code = state.get("generated_code", "")

    if not code:
        return {
            "execution_output": "",
            "execution_success": False,
            "execution_error": "No code to execute",
            "execution_metrics": [],
            "phase": "analysis",
            "messages": [HumanMessage(content="No code was generated to execute.")],
        }

    # Estimate duration and compute dynamic timeout from data profile
    data_profile = state.get("data_profile")
    n_algorithms = len(state.get("candidate_algorithms", [])) or 1
    estimated_duration = None
    dynamic_timeout = 300  # default

    if data_profile and "shape" in data_profile:
        n_rows = data_profile["shape"][0]
        n_cols = data_profile["shape"][1]
        estimated_duration = estimate_training_duration(n_rows, n_cols, n_algorithms=n_algorithms)
        dynamic_timeout = compute_dynamic_timeout(estimated_duration)
        subset_size = suggest_data_subset_size(n_rows, n_cols=n_cols, n_algorithms=n_algorithms)
    else:
        subset_size = None

    # Journal: log execution start
    journal = get_journal_for_experiment(experiment_id)
    journal.log(
        "execution_start",
        phase="execution",
        iteration=state.get("current_iteration", 0),
        data={
            "run_id": run_id,
            "estimated_duration": estimated_duration,
            "timeout": dynamic_timeout,
            "data_subset_size": subset_size,
        },
    )

    # Emit run started event
    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="run_started",
            data={
                "run_id": run_id,
                "iteration": state.get("current_iteration", 0),
                "estimated_duration": estimated_duration,
                "timeout": dynamic_timeout,
            },
        ),
    )

    # Stream metrics in real-time via event bus
    async def on_metric(metric: dict) -> None:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="metric_update",
                data={**metric, "run_id": run_id},
            ),
        )

    runner = CodeRunner()
    result = await runner.execute(
        RunConfig(
            experiment_id=experiment_id,
            code=code,
            run_id=run_id,
            timeout_seconds=dynamic_timeout,
        ),
        on_metric=on_metric,
    )

    # Journal: log execution result
    journal.log(
        "execution_complete",
        phase="execution",
        iteration=state.get("current_iteration", 0),
        data={
            "run_id": run_id,
            "status": result.status,
            "wall_time": result.wall_time_seconds,
            "success": result.success,
        },
    )

    # Emit completion event
    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="run_completed",
            data={
                "run_id": run_id,
                "status": result.status,
                "exit_code": result.exit_code,
                "wall_time_seconds": result.wall_time_seconds,
            },
        ),
    )

    # Build status message
    if result.success:
        status_msg = (
            f"Code executed successfully in {result.wall_time_seconds:.1f}s. "
            f"Collected {len(result.metrics)} metric points."
        )
        if result.results_json:
            status_msg += f"\nResults: {result.results_json}"
    else:
        error_snippet = result.stderr[:500] if result.stderr else "Unknown error"
        status_msg = (
            f"Execution {result.status} (exit code {result.exit_code}). Error: {error_snippet}"
        )

    return {
        "execution_output": result.stdout[:5000],
        "execution_success": result.success,
        "execution_error": result.stderr[:2000] if not result.success else None,
        "execution_metrics": result.metrics,
        "estimated_duration_seconds": estimated_duration,
        "dynamic_timeout": dynamic_timeout,
        "data_subset_size": subset_size,
        "phase": "analysis",
        "progress_events": [
            {
                "event_type": "run_completed",
                "data": {
                    "run_id": run_id,
                    "status": result.status,
                    "success": result.success,
                    "wall_time": result.wall_time_seconds,
                    "results": result.results_json,
                },
            }
        ],
        "messages": [HumanMessage(content=status_msg)],
    }
