"""Thread-safe in-memory experiment store."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


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
    status: str = "pending"  # pending | running | completed | failed
    phase: str | None = None
    runs: list[Run] = Field(default_factory=list)
    best_run_id: str | None = None
    iteration_count: int = 0
    progress_events: list[dict] = Field(default_factory=list)
    result: dict | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExperimentStore:
    """Thread-safe CRUD store backed by an in-memory dict."""

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._lock = threading.Lock()

    def create(
        self,
        objective: str,
        data_description: str = "",
        data_file_path: str | None = None,
        framework: str | None = None,
    ) -> Experiment:
        experiment = Experiment(
            objective=objective,
            data_description=data_description,
            data_file_path=data_file_path,
            framework=framework,
        )
        with self._lock:
            self._experiments[experiment.id] = experiment
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
            return updated

    def delete(self, experiment_id: str) -> bool:
        with self._lock:
            return self._experiments.pop(experiment_id, None) is not None


experiment_store = ExperimentStore()
