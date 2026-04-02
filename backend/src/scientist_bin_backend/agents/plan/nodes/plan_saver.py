"""Plan saver node — persists the execution plan to disk.

Writes ``execution_plan.json`` to ``outputs/runs/{experiment_id}/plan/``
so the artifact copier can pick it up.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from scientist_bin_backend.agents.analyst.utils import resolve_run_subdir
from scientist_bin_backend.agents.plan.states import PlanState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

logger = logging.getLogger(__name__)


def _resolve_output_dir(experiment_id: str) -> Path:
    return resolve_run_subdir(experiment_id, "plan")


async def save_plan(state: PlanState) -> dict:
    """Save the approved execution plan as JSON to the run directory."""
    experiment_id = state.get("experiment_id")
    execution_plan = state.get("execution_plan")

    if not experiment_id or not execution_plan:
        return {}

    output_dir = _resolve_output_dir(experiment_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / "execution_plan.json"
    plan_path.write_text(
        json.dumps(execution_plan, indent=2, default=str),
        encoding="utf-8",
    )

    logger.info("Saved execution plan to %s", plan_path)

    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="agent_activity",
            data={
                "agent": "plan",
                "node": "save_plan",
                "summary": f"Execution plan saved to {plan_path.name}",
            },
        ),
    )

    return {}
