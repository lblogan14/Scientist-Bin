"""Thread-safe in-memory experiment store."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    """A single training experiment record."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    objective: str
    data_description: str = ""
    framework: str | None = None
    status: str = "pending"  # pending | running | completed | failed
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
        framework: str | None = None,
    ) -> Experiment:
        experiment = Experiment(
            objective=objective,
            data_description=data_description,
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
            updated = exp.model_copy(
                update={**kwargs, "updated_at": datetime.now(UTC)}
            )
            self._experiments[experiment_id] = updated
            return updated

    def delete(self, experiment_id: str) -> bool:
        with self._lock:
            return self._experiments.pop(experiment_id, None) is not None


experiment_store = ExperimentStore()
