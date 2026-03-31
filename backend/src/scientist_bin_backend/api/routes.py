"""REST API endpoints for the Scientist-Bin backend."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from scientist_bin_backend.api.experiments import experiment_store

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class TrainRequestBody(BaseModel):
    objective: str
    data_description: str = ""
    framework_preference: str | None = None


# ---------------------------------------------------------------------------
# Background task for running the agent
# ---------------------------------------------------------------------------

async def _run_training(
    experiment_id: str,
    objective: str,
    data_description: str,
    framework: str | None,
) -> None:
    """Run the central agent and update the experiment with results."""
    experiment_store.update(experiment_id, status="running")
    try:
        from scientist_bin_backend.agents.central.agent import CentralAgent
        from scientist_bin_backend.agents.central.schemas import TrainRequest

        agent = CentralAgent()
        request = TrainRequest(
            objective=objective,
            data_description=data_description,
            framework_preference=framework,
        )
        result = await agent.run(request)
        experiment_store.update(
            experiment_id,
            status="completed",
            framework=result.framework,
            result=result.model_dump(),
        )
    except Exception as exc:
        experiment_store.update(experiment_id, status="failed", result={"error": str(exc)})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/train")
async def create_train(body: TrainRequestBody, background_tasks: BackgroundTasks) -> dict:
    """Submit a new training request."""
    experiment = experiment_store.create(
        objective=body.objective,
        data_description=body.data_description,
        framework=body.framework_preference,
    )
    background_tasks.add_task(
        _run_training,
        experiment.id,
        body.objective,
        body.data_description,
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
