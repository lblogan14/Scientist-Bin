"""REST API endpoints for the Scientist-Bin backend."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from scientist_bin_backend.api.experiments import experiment_store
from scientist_bin_backend.events.bus import event_bus

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


async def _run_training(
    experiment_id: str,
    objective: str,
    data_description: str,
    data_file_path: str | None,
    framework: str | None,
) -> None:
    """Run the central agent and update the experiment with results."""
    experiment_store.update(experiment_id, status="running", phase="initializing")
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
        result = await agent.run(request)
        experiment_store.update(
            experiment_id,
            status="completed",
            phase="done",
            framework=result.framework,
            iteration_count=result.iterations,
            result=result.model_dump(),
        )
    except Exception as exc:
        experiment_store.update(
            experiment_id,
            status="failed",
            phase="error",
            result={"error": str(exc)},
        )
    finally:
        await event_bus.close(experiment_id)


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
