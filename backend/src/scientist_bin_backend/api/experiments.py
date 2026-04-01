"""Thread-safe experiment store with file-based persistence."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from scientist_bin_backend.utils.naming import generate_experiment_id

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExperimentStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ExperimentPhase(StrEnum):
    initializing = "initializing"
    classify = "classify"
    eda = "eda"
    planning = "planning"
    plan_review = "plan_review"
    data_analysis = "data_analysis"
    execution = "execution"
    analysis = "analysis"
    summarizing = "summarizing"
    done = "done"
    error = "error"


class Framework(StrEnum):
    sklearn = "sklearn"
    pytorch = "pytorch"
    tensorflow = "tensorflow"
    transformers = "transformers"
    diffusers = "diffusers"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class MetricPoint(BaseModel):
    """A single metric observation."""

    name: str
    value: float
    step: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Run(BaseModel):
    """A single training run within an experiment."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    experiment_id: str
    algorithm: str = ""
    hyperparameters: dict = Field(default_factory=dict)
    metrics: list[MetricPoint] = Field(default_factory=list)
    final_metrics: dict | None = None
    status: str = "pending"  # pending | running | completed | failed | timeout
    code: str = ""
    stdout: str = ""
    stderr: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    wall_time_seconds: float | None = None
    artifacts: list[str] = Field(default_factory=list)


class Experiment(BaseModel):
    """A single training experiment record."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    objective: str
    data_description: str = ""
    data_file_path: str | None = None
    framework: str | None = None
    status: str = ExperimentStatus.pending
    phase: str | None = None
    runs: list[Run] = Field(default_factory=list)
    best_run_id: str | None = None
    iteration_count: int = 0
    progress_events: list[dict] = Field(default_factory=list)
    result: dict | None = None
    execution_plan: dict | None = None
    analysis_report: str | None = None
    summary_report: str | None = None
    split_data_paths: dict | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


_DEFAULT_STORE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "outputs" / "experiments"
)


class ExperimentStore:
    """Thread-safe CRUD store with JSON file persistence."""

    def __init__(self, store_dir: Path | None = None) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._lock = threading.Lock()
        self._store_dir = store_dir or _DEFAULT_STORE_DIR
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    # -- Persistence helpers --------------------------------------------------

    def _experiment_path(self, experiment_id: str) -> Path:
        return self._store_dir / f"{experiment_id}.json"

    def _save_to_disk(self, experiment: Experiment) -> None:
        """Persist a single experiment to its JSON file."""
        path = self._experiment_path(experiment.id)
        path.write_text(experiment.model_dump_json(indent=2), encoding="utf-8")

    def _load_from_disk(self) -> None:
        """Load all experiments from the store directory on startup."""
        for path in self._store_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                exp = Experiment.model_validate(data)
                self._experiments[exp.id] = exp
            except Exception:
                continue  # skip corrupt files

    def _delete_from_disk(self, experiment_id: str) -> None:
        path = self._experiment_path(experiment_id)
        path.unlink(missing_ok=True)

    # -- CRUD -----------------------------------------------------------------

    def create(
        self,
        objective: str,
        data_description: str = "",
        data_file_path: str | None = None,
        framework: str | None = None,
    ) -> Experiment:
        experiment = Experiment(
            id=generate_experiment_id(objective),
            objective=objective,
            data_description=data_description,
            data_file_path=data_file_path,
            framework=framework,
        )
        with self._lock:
            self._experiments[experiment.id] = experiment
            self._save_to_disk(experiment)
        return experiment

    def get(self, experiment_id: str) -> Experiment | None:
        with self._lock:
            return self._experiments.get(experiment_id)

    def list_all(self) -> list[Experiment]:
        with self._lock:
            return sorted(
                self._experiments.values(),
                key=lambda e: e.created_at,
                reverse=True,
            )

    def update(self, experiment_id: str, **kwargs: object) -> Experiment | None:
        with self._lock:
            exp = self._experiments.get(experiment_id)
            if exp is None:
                return None
            updated = exp.model_copy(update={**kwargs, "updated_at": datetime.now(UTC)})
            self._experiments[experiment_id] = updated
            self._save_to_disk(updated)
            return updated

    def append_events(self, experiment_id: str, events: list[dict]) -> Experiment | None:
        """Append progress events to an experiment."""
        with self._lock:
            exp = self._experiments.get(experiment_id)
            if exp is None:
                return None
            updated = exp.model_copy(
                update={
                    "progress_events": exp.progress_events + events,
                    "updated_at": datetime.now(UTC),
                }
            )
            self._experiments[experiment_id] = updated
            self._save_to_disk(updated)
            return updated

    def delete(self, experiment_id: str) -> bool:
        with self._lock:
            removed = self._experiments.pop(experiment_id, None) is not None
            if removed:
                self._delete_from_disk(experiment_id)
            return removed


experiment_store = ExperimentStore()
