"""REST API endpoints for the Scientist-Bin backend."""

from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from scientist_bin_backend.api.experiments import Run, experiment_store
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class TrainRequestBody(BaseModel):
    objective: str
    data_description: str = ""
    data_file_path: str | None = None
    framework_preference: str | None = None


# ---------------------------------------------------------------------------
# Background task for running the agent
# ---------------------------------------------------------------------------


async def _sync_events_to_store(experiment_id: str) -> None:
    """Subscribe to experiment events and mirror phase/progress into the store.

    Runs as a concurrent task alongside the agent so that polling clients
    (GET /experiments/{id}) see up-to-date phase and progress_events without
    relying solely on the SSE stream.
    """
    # Track the current run being assembled from events
    _current_run_id: str | None = None

    async for event in event_bus.subscribe(experiment_id):
        event_dict = event.model_dump(mode="json")

        if event.event_type == "phase_change":
            phase = event.data.get("phase")
            if phase:
                experiment_store.update(experiment_id, phase=phase)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "run_started":
            experiment_store.update(experiment_id, phase="execution")
            # Create a new Run object
            run_id = event.data.get("run_id", "")
            _current_run_id = run_id
            exp = experiment_store.get(experiment_id)
            if exp is not None:
                new_run = Run(
                    id=run_id,
                    experiment_id=experiment_id,
                    status="running",
                    started_at=datetime.now(UTC),
                )
                experiment_store.update(experiment_id, runs=exp.runs + [new_run])
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "run_completed":
            run_id = event.data.get("run_id", _current_run_id or "")
            exp = experiment_store.get(experiment_id)
            if exp is not None:
                # Update the matching run with completion data
                updated_runs = []
                for run in exp.runs:
                    if run.id == run_id:
                        run = run.model_copy(
                            update={
                                "status": event.data.get("status", "completed"),
                                "wall_time_seconds": event.data.get("wall_time_seconds"),
                                "algorithm": event.data.get("algorithm", ""),
                                "final_metrics": event.data.get("metrics"),
                                "completed_at": datetime.now(UTC),
                            }
                        )
                    updated_runs.append(run)
                experiment_store.update(
                    experiment_id,
                    runs=updated_runs,
                    iteration_count=exp.iteration_count + 1,
                )
            experiment_store.append_events(experiment_id, [event_dict])
            _current_run_id = None

        elif event.event_type == "agent_activity":
            action = event.data.get("action")
            if action == "analyze_results":
                experiment_store.update(experiment_id, phase="analysis")
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "experiment_done":
            experiment_store.update(experiment_id, phase="done")
            experiment_store.append_events(experiment_id, [event_dict])

        else:
            experiment_store.append_events(experiment_id, [event_dict])


def _resolve_data_file_path(raw_path: str | None) -> str | None:
    """Resolve a user-provided data file path to an absolute path.

    Tries (in order):
    1. The path as given (absolute or relative to CWD)
    2. Relative to the backend/ directory
    3. Relative to the project root (parent of backend/)
    """
    if not raw_path:
        return None

    from pathlib import Path

    p = Path(raw_path)
    if p.is_file():
        return str(p.resolve())

    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    project_root = backend_dir.parent

    for base in (backend_dir, project_root):
        candidate = base / raw_path
        if candidate.is_file():
            return str(candidate.resolve())

    # Return the original; downstream code will handle missing files
    return raw_path


async def _run_training(
    experiment_id: str,
    objective: str,
    data_description: str,
    data_file_path: str | None,
    framework: str | None,
) -> None:
    """Run the central agent and update the experiment with results."""
    data_file_path = _resolve_data_file_path(data_file_path)
    experiment_store.update(
        experiment_id,
        status="running",
        phase="initializing",
        data_file_path=data_file_path,
    )

    # Mirror events into the experiment store so polling clients stay current
    sync_task = asyncio.create_task(_sync_events_to_store(experiment_id))

    try:
        from scientist_bin_backend.agents.central.agent import CentralAgent
        from scientist_bin_backend.agents.central.schemas import TrainRequest

        agent = CentralAgent()
        request = TrainRequest(
            objective=objective,
            data_description=data_description,
            data_file_path=data_file_path,
            framework_preference=framework,
        )
        result = await agent.run(request, experiment_id=experiment_id)
        experiment_store.update(
            experiment_id,
            status="completed",
            phase="done",
            framework=result.framework,
            iteration_count=result.iterations,
            result=result.model_dump(),
        )
    except Exception as exc:
        tb = traceback.format_exc()
        error_msg = str(exc) or f"{type(exc).__name__}: {tb.splitlines()[-1]}"
        logger.error("Experiment %s failed: %s\n%s", experiment_id, error_msg, tb)
        experiment_store.update(
            experiment_id,
            status="failed",
            phase="error",
            result={"error": error_msg, "traceback": tb},
        )
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="error",
                data={"message": error_msg, "phase": "error"},
            ),
        )
    finally:
        await event_bus.close(experiment_id)
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/train")
async def create_train(body: TrainRequestBody, background_tasks: BackgroundTasks) -> dict:
    """Submit a new training request."""
    experiment = experiment_store.create(
        objective=body.objective,
        data_description=body.data_description,
        data_file_path=body.data_file_path,
        framework=body.framework_preference,
    )
    background_tasks.add_task(
        _run_training,
        experiment.id,
        body.objective,
        body.data_description,
        body.data_file_path,
        body.framework_preference,
    )
    return experiment.model_dump(mode="json")


@router.get("/experiments")
async def list_experiments() -> list[dict]:
    """List all experiments, most recent first."""
    return [e.model_dump(mode="json") for e in experiment_store.list_all()]


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str) -> dict:
    """Get a single experiment by ID."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment.model_dump(mode="json")


@router.get("/experiments/{experiment_id}/events")
async def stream_events(experiment_id: str) -> StreamingResponse:
    """Stream experiment events via Server-Sent Events."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    async def event_generator():
        async for event in event_bus.subscribe(experiment_id):
            sse = event.sse_format()
            yield f"event: {sse['event']}\ndata: {sse['data']}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/experiments/{experiment_id}/journal")
async def get_journal(experiment_id: str) -> list[dict]:
    """Get the experiment journal (append-only decision/reasoning log)."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    from scientist_bin_backend.execution.journal import get_journal_for_experiment

    journal = get_journal_for_experiment(experiment_id)
    return journal.read_all()


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str) -> dict:
    """Delete an experiment."""
    if not experiment_store.delete(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"detail": "Experiment deleted"}


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
