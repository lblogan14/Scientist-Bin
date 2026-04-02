"""Event types for experiment progress streaming."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "phase_change",
    "metric_update",
    "agent_activity",
    "log_output",
    "run_started",
    "run_completed",
    "error",
    "experiment_done",
    "plan_review_pending",
    "plan_review_submitted",
    "plan_completed",
    "analysis_completed",
    "sklearn_completed",
    "framework_completed",
    "summary_completed",
]


class ExperimentEvent(BaseModel):
    """A single event emitted during experiment execution."""

    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: dict = Field(default_factory=dict)

    def sse_format(self) -> dict[str, str]:
        """Format for Server-Sent Events."""
        return {
            "event": self.event_type,
            "data": self.model_dump_json(),
        }
