"""REST API endpoints for the Scientist-Bin backend."""

from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from scientist_bin_backend.api.experiments import (
    ExperimentPhase,
    ExperimentStatus,
    Run,
    experiment_store,
)
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# outputs/ is always relative to the backend package root
_OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "outputs"

# File validation constants
_ALLOWED_EXTENSIONS = {".csv", ".tsv", ".parquet", ".xlsx", ".xls", ".json"}
_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Active HITL sessions: experiment_id -> asyncio.Event for review feedback
_review_events: dict[str, asyncio.Event] = {}
_review_feedback: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class TrainRequestBody(BaseModel):
    objective: str = Field(..., min_length=1)
    data_description: str = ""
    data_file_path: str | None = None
    framework_preference: str | None = None
    auto_approve_plan: bool = False


class ReviewBody(BaseModel):
    feedback: str


# ---------------------------------------------------------------------------
# Background task for running the agent
# ---------------------------------------------------------------------------


async def _sync_events_from_queue(
    experiment_id: str,
    queue: asyncio.Queue,
) -> None:
    """Consume events from a pre-registered queue and mirror them into the store.

    Runs as a concurrent task alongside the agent so that polling clients
    (GET /experiments/{id}) see up-to-date phase and progress_events without
    relying solely on the SSE stream.
    """
    # Track the current run being assembled from events
    _current_run_id: str | None = None

    async for event in event_bus.consume(experiment_id, queue):
        event_dict = event.model_dump(mode="json")

        if event.event_type == "phase_change":
            phase_str = event.data.get("phase")
            if phase_str:
                try:
                    experiment_store.update(experiment_id, phase=ExperimentPhase(phase_str))
                except ValueError:
                    pass  # Sub-agent phase names (e.g. "cleaning") don't map to ExperimentPhase
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "run_started":
            experiment_store.update(experiment_id, phase=ExperimentPhase.execution)
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
                experiment_store.update(experiment_id, phase=ExperimentPhase.analysis)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "experiment_done":
            updates: dict = {"phase": ExperimentPhase.done}
            best_model = event.data.get("best_model")
            if best_model:
                exp = experiment_store.get(experiment_id)
                if exp:
                    for run in exp.runs:
                        if run.algorithm == best_model:
                            updates["best_run_id"] = run.id
                            break
            experiment_store.update(experiment_id, **updates)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "plan_completed":
            plan = event.data.get("execution_plan")
            if plan:
                experiment_store.update(experiment_id, execution_plan=plan)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "analysis_completed":
            report = event.data.get("analysis_report")
            paths = event.data.get("split_data_paths")
            updates: dict = {}
            if report:
                updates["analysis_report"] = report
            if paths:
                updates["split_data_paths"] = paths
            if updates:
                experiment_store.update(experiment_id, **updates)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "summary_completed":
            report = event.data.get("summary_report")
            if report:
                experiment_store.update(experiment_id, summary_report=report)
            experiment_store.append_events(experiment_id, [event_dict])

        elif event.event_type == "plan_review_pending":
            experiment_store.update(experiment_id, phase=ExperimentPhase.plan_review)
            experiment_store.append_events(experiment_id, [event_dict])

        else:
            experiment_store.append_events(experiment_id, [event_dict])


def _resolve_data_file_path(raw_path: str | None) -> str | None:
    """Resolve a user-provided data file path to an absolute path.

    Paths are resolved relative to ``backend/data/`` by default, which is the
    canonical location for datasets.  The full resolution order is:

    1. ``backend/data/<raw_path>`` — the recommended convention
    2. ``backend/<raw_path>`` — backwards-compatible with older paths
    3. ``<project_root>/<raw_path>``
    4. The path as given (absolute or relative to CWD)
    """
    if not raw_path:
        return None

    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    project_root = backend_dir.parent
    data_dir = backend_dir / "data"

    for base in (data_dir, backend_dir, project_root):
        candidate = base / raw_path
        if candidate.is_file():
            return str(candidate.resolve())

    # Try the path as-is (absolute or relative to CWD)
    p = Path(raw_path)
    if p.is_file():
        return str(p.resolve())

    # Return the original; validation in create_train() will reject it
    return raw_path


async def _run_training(
    experiment_id: str,
    objective: str,
    data_description: str,
    data_file_path: str | None,
    framework: str | None,
    auto_approve_plan: bool = False,
) -> None:
    """Run the central agent and update the experiment with results.

    When ``auto_approve_plan`` is ``False``, the plan agent will call
    ``interrupt()`` and the graph pauses. This function waits for the
    ``/review`` endpoint to supply feedback, then resumes the graph.
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    from scientist_bin_backend.agents.central.agent import CentralAgent
    from scientist_bin_backend.agents.central.schemas import AgentResponse, TrainRequest
    from scientist_bin_backend.agents.central.utils import build_initial_state

    data_file_path = _resolve_data_file_path(data_file_path)
    experiment_store.update(
        experiment_id,
        status=ExperimentStatus.running,
        phase=ExperimentPhase.initializing,
        data_file_path=data_file_path,
    )

    # Pre-register the event queue BEFORE the agent starts so no early events
    # are lost (fixes the race where subscribe() happened after agent.run()).
    sync_queue = event_bus.pre_register(experiment_id)
    sync_task = asyncio.create_task(_sync_events_from_queue(experiment_id, sync_queue))

    try:
        checkpointer = MemorySaver()
        agent = CentralAgent(checkpointer=checkpointer)
        graph = agent.graph
        config = {"configurable": {"thread_id": experiment_id}}

        request = TrainRequest(
            objective=objective,
            data_description=data_description,
            data_file_path=data_file_path,
            framework_preference=framework,
            auto_approve_plan=auto_approve_plan,
        )
        initial_state = build_initial_state(request, experiment_id=experiment_id)

        # Run graph — may pause at interrupt() if auto_approve is False
        state = await graph.ainvoke(initial_state, config=config)

        # Handle HITL: loop while the graph is interrupted (plan review)
        snapshot = await graph.aget_state(config)
        while snapshot.next:
            # Graph is paused at interrupt — wait for review feedback
            review_event = asyncio.Event()
            _review_events[experiment_id] = review_event

            try:
                await review_event.wait()
            finally:
                _review_events.pop(experiment_id, None)

            feedback = _review_feedback.pop(experiment_id, "approve")

            # Resume the graph with the reviewer's feedback
            state = await graph.ainvoke(Command(resume=feedback), config=config)
            snapshot = await graph.aget_state(config)

        # Build the AgentResponse from final state
        agent_resp = state.get("agent_response") or {}
        result = AgentResponse(
            framework=state.get("selected_framework") or "sklearn",
            plan=agent_resp.get("plan"),
            plan_markdown=state.get("plan_markdown"),
            generated_code=agent_resp.get("generated_code"),
            evaluation_results=agent_resp.get("evaluation_results"),
            experiment_history=agent_resp.get("experiment_history", []),
            data_profile=state.get("data_profile"),
            problem_type=state.get("problem_type"),
            iterations=agent_resp.get("iterations", 0),
            analysis_report=state.get("analysis_report"),
            summary_report=state.get("summary_report"),
            best_model=agent_resp.get("best_model"),
            best_hyperparameters=agent_resp.get("best_hyperparameters"),
            selection_reasoning=agent_resp.get("selection_reasoning"),
            report_sections=agent_resp.get("report_sections"),
            status=ExperimentStatus.failed if state.get("error") else ExperimentStatus.completed,
        )

        result_dict = result.model_dump()
        experiment_store.update(
            experiment_id,
            status=ExperimentStatus.completed,
            phase=ExperimentPhase.done,
            framework=result.framework,
            iteration_count=result.iterations,
            result=result_dict,
            execution_plan=result.plan,
            analysis_report=result.analysis_report,
            summary_report=result.summary_report,
        )

        # Save artifacts (model, results JSON, journal) like the CLI does
        try:
            from scientist_bin_backend.utils.artifacts import save_experiment_artifacts

            save_experiment_artifacts(experiment_id, result_dict)
        except Exception as save_exc:
            logger.exception("Failed to save artifacts for %s", experiment_id)
            experiment_store.update(
                experiment_id,
                result={**result_dict, "_warnings": [f"Artifact save failed: {save_exc}"]},
            )
    except Exception as exc:
        tb = traceback.format_exc()
        error_msg = str(exc) or f"{type(exc).__name__}: {tb.splitlines()[-1]}"
        logger.error("Experiment %s failed: %s\n%s", experiment_id, error_msg, tb)
        experiment_store.update(
            experiment_id,
            status=ExperimentStatus.failed,
            phase=ExperimentPhase.error,
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
        _review_events.pop(experiment_id, None)
        _review_feedback.pop(experiment_id, None)
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
    # Validate data file path upfront (matches CLI behavior)
    resolved_data_file = _resolve_data_file_path(body.data_file_path)
    if body.data_file_path and resolved_data_file:
        data_path = Path(resolved_data_file)
        if not data_path.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Data file not found: {body.data_file_path}",
            )
        # Validate file extension
        if data_path.suffix.lower() not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type '{data_path.suffix}'. "
                    f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
                ),
            )
        # Validate file size
        file_size = data_path.stat().st_size
        if file_size > _MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Data file too large ({file_size / 1024 / 1024:.1f} MB). Maximum: 500 MB.",
            )

    experiment = experiment_store.create(
        objective=body.objective,
        data_description=body.data_description,
        data_file_path=resolved_data_file,
        framework=body.framework_preference,
    )
    background_tasks.add_task(
        _run_training,
        experiment.id,
        body.objective,
        body.data_description,
        resolved_data_file,
        body.framework_preference,
        body.auto_approve_plan,
    )
    return experiment.model_dump(mode="json")


@router.get("/experiments")
async def list_experiments(
    status: str | None = None,
    framework: str | None = None,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    """List experiments with optional filtering and pagination.

    Query parameters:
        status: Filter by experiment status (pending, running, completed, failed).
        framework: Filter by ML framework (sklearn, pytorch, ...).
        search: Search within the objective text (case-insensitive).
        offset: Number of results to skip (default 0).
        limit: Maximum number of results to return (default 50).
    """
    experiments = experiment_store.list_filtered(
        status=status,
        framework=framework,
        search=search,
    )
    total = len(experiments)
    page = experiments[offset : offset + limit]
    return {
        "experiments": [e.model_dump(mode="json") for e in page],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


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


@router.post("/experiments/{experiment_id}/review")
async def submit_plan_review(experiment_id: str, body: ReviewBody) -> dict:
    """Submit plan review feedback for a waiting experiment.

    When a training experiment is paused at the plan review step, call
    this endpoint with ``{"feedback": "approve"}`` to accept the plan,
    or provide revision instructions to trigger a plan update.
    """
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    review_event = _review_events.get(experiment_id)
    if review_event is None:
        raise HTTPException(
            status_code=409,
            detail="Experiment is not waiting for plan review",
        )

    _review_feedback[experiment_id] = body.feedback
    review_event.set()
    return {"status": "review_submitted", "feedback": body.feedback}


@router.get("/experiments/{experiment_id}/journal")
async def get_journal(experiment_id: str) -> list[dict]:
    """Get the experiment journal (append-only decision/reasoning log)."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    from scientist_bin_backend.execution.journal import get_journal_for_experiment

    journal = get_journal_for_experiment(experiment_id)
    return journal.read_all()


# ---------------------------------------------------------------------------
# Artifact download endpoints
# ---------------------------------------------------------------------------

_ARTIFACT_MAP: dict[str, tuple[str, str, str]] = {
    # key: (directory relative to _OUTPUTS_DIR, filename pattern, media_type)
    "model": ("models", "{id}.joblib", "application/octet-stream"),
    "results": ("results", "{id}.json", "application/json"),
    "analysis": ("results", "{id}_analysis.md", "text/markdown"),
    "summary": ("results", "{id}_summary.md", "text/markdown"),
    "plan": ("results", "{id}_plan.json", "application/json"),
    "charts": ("results", "{id}_charts.json", "application/json"),
    "journal": ("logs", "{id}.jsonl", "application/x-ndjson"),
}


@router.get("/experiments/{experiment_id}/artifacts/{artifact_type}")
async def download_artifact(experiment_id: str, artifact_type: str) -> FileResponse:
    """Download an experiment artifact by type.

    Supported types: model, results, analysis, summary, plan, charts, journal.
    """
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    spec = _ARTIFACT_MAP.get(artifact_type)
    if spec is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown artifact type: {artifact_type}. Supported: {', '.join(_ARTIFACT_MAP)}",
        )

    subdir, pattern, media_type = spec
    filename = pattern.format(id=experiment_id)
    path = (_OUTPUTS_DIR / subdir / filename).resolve()

    # Guard against path traversal via crafted experiment IDs
    if not str(path).startswith(str(_OUTPUTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid experiment ID")

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"{artifact_type.title()} artifact not found",
        )

    return FileResponse(path=path, filename=filename, media_type=media_type)


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str) -> dict:
    """Delete an experiment."""
    if not experiment_store.delete(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"detail": "Experiment deleted"}


@router.get("/experiments/{experiment_id}/plan")
async def get_plan(experiment_id: str) -> dict:
    """Get the execution plan for an experiment."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"execution_plan": experiment.execution_plan}


@router.get("/experiments/{experiment_id}/analysis")
async def get_analysis(experiment_id: str) -> dict:
    """Get the analyst report for an experiment."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "analysis_report": experiment.analysis_report,
        "split_data_paths": experiment.split_data_paths,
    }


@router.get("/experiments/{experiment_id}/summary")
async def get_summary(experiment_id: str) -> dict:
    """Get the summary report for an experiment."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"summary_report": experiment.summary_report}


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Mock deployment endpoints
# ---------------------------------------------------------------------------

# In-memory deployment state (mock — not persisted)
_deployments: dict[str, dict] = {}


class DeployRequest(BaseModel):
    model_version: str = "v1.0"


@router.post("/experiments/{experiment_id}/deploy")
async def deploy_model(experiment_id: str, body: DeployRequest | None = None) -> dict:
    """Mock model deployment — simulates deploying the trained model to a server."""
    experiment = experiment_store.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.status != ExperimentStatus.completed:
        raise HTTPException(status_code=400, detail="Only completed experiments can be deployed")

    version = body.model_version if body else "v1.0"
    deployment_info = {
        "status": "deployed",
        "endpoint_url": f"/api/v1/predict/{experiment_id}",
        "deployed_at": datetime.now(UTC).isoformat(),
        "model_version": version,
        "experiment_id": experiment_id,
    }
    _deployments[experiment_id] = deployment_info
    return deployment_info


@router.post("/experiments/{experiment_id}/undeploy")
async def undeploy_model(experiment_id: str) -> dict:
    """Mock model undeployment — removes the deployed model."""
    if experiment_id not in _deployments:
        raise HTTPException(status_code=404, detail="Model is not deployed")

    _deployments.pop(experiment_id, None)
    return {"status": "not_deployed", "experiment_id": experiment_id}


@router.get("/experiments/{experiment_id}/deployment")
async def get_deployment(experiment_id: str) -> dict:
    """Get deployment status for a model."""
    deployment = _deployments.get(experiment_id)
    if deployment is None:
        return {"status": "not_deployed", "experiment_id": experiment_id}
    return deployment


@router.post("/predict/{experiment_id}")
async def predict(experiment_id: str) -> dict:
    """Mock prediction endpoint — returns a placeholder response."""
    deployment = _deployments.get(experiment_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="Model is not deployed")

    return {
        "prediction": "mock_prediction_result",
        "model": experiment_id,
        "model_version": deployment.get("model_version", "v1.0"),
        "message": "This is a mock prediction endpoint. "
        "In production, this would load the model and run inference.",
    }
