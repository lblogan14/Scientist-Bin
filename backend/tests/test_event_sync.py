"""Tests for _sync_events_from_queue in api/routes.py.

Verifies that each event type correctly updates the experiment store.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from scientist_bin_backend.api.experiments import (
    ExperimentPhase,
    ExperimentStore,
)
from scientist_bin_backend.api.routes import _sync_events_from_queue
from scientist_bin_backend.events.types import ExperimentEvent


@pytest.fixture()
def store(tmp_path: Path) -> ExperimentStore:
    """Create an isolated experiment store."""
    return ExperimentStore(store_dir=tmp_path / "experiments")


@pytest.fixture()
def experiment_id(store: ExperimentStore) -> str:
    """Create a test experiment and return its ID."""
    exp = store.create(objective="Test experiment")
    return exp.id


async def _run_sync_with_events(
    experiment_id: str,
    store: ExperimentStore,
    events: list[ExperimentEvent],
) -> None:
    """Helper: run _sync_events_from_queue with a mocked consume that yields events."""
    queue = asyncio.Queue()

    async def mock_consume(exp_id, q):
        for event in events:
            yield event

    with (
        patch("scientist_bin_backend.api.routes.experiment_store", store),
        patch("scientist_bin_backend.api.routes.event_bus") as mock_bus,
    ):
        mock_bus.consume = mock_consume
        await _sync_events_from_queue(experiment_id, queue)


class TestPhaseChange:
    async def test_updates_experiment_phase(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "planning"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp is not None
        assert exp.phase == ExperimentPhase.planning

    async def test_appends_to_progress_events(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "eda"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert len(exp.progress_events) == 1
        assert exp.progress_events[0]["event_type"] == "phase_change"


class TestRunStarted:
    async def test_creates_run_and_sets_execution_phase(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="run_started",
                data={"run_id": "run-001"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp is not None
        assert exp.phase == ExperimentPhase.execution
        assert len(exp.runs) == 1
        assert exp.runs[0].id == "run-001"
        assert exp.runs[0].status == "running"
        assert exp.runs[0].experiment_id == experiment_id


class TestRunCompleted:
    async def test_updates_matching_run(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="run_started",
                data={"run_id": "run-001"},
            ),
            ExperimentEvent(
                event_type="run_completed",
                data={
                    "run_id": "run-001",
                    "status": "completed",
                    "wall_time_seconds": 12.5,
                    "algorithm": "RandomForest",
                    "metrics": {"accuracy": 0.95},
                },
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp is not None
        assert len(exp.runs) == 1
        run = exp.runs[0]
        assert run.status == "completed"
        assert run.wall_time_seconds == 12.5
        assert run.algorithm == "RandomForest"
        assert run.final_metrics == {"accuracy": 0.95}
        assert run.completed_at is not None

    async def test_increments_iteration_count(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="run_started",
                data={"run_id": "run-001"},
            ),
            ExperimentEvent(
                event_type="run_completed",
                data={"run_id": "run-001", "status": "completed"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.iteration_count == 1


class TestExperimentDone:
    async def test_sets_phase_to_done(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="experiment_done",
                data={"best_model": "SVM"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.phase == ExperimentPhase.done

    async def test_sets_best_run_id_when_algorithm_matches(self, store, experiment_id):
        """When best_model matches a run's algorithm, best_run_id is set."""
        events = [
            ExperimentEvent(
                event_type="run_started",
                data={"run_id": "run-001"},
            ),
            ExperimentEvent(
                event_type="run_completed",
                data={"run_id": "run-001", "status": "completed", "algorithm": "SVM"},
            ),
            ExperimentEvent(
                event_type="experiment_done",
                data={"best_model": "SVM"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.best_run_id == "run-001"


class TestPlanReviewPending:
    async def test_sets_phase_to_plan_review(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="plan_review_pending",
                data={"plan_markdown": "## Plan"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.phase == ExperimentPhase.plan_review


class TestPlanCompleted:
    async def test_stores_execution_plan(self, store, experiment_id):
        plan = {"algorithms_to_try": ["RandomForest", "SVM"]}
        events = [
            ExperimentEvent(
                event_type="plan_completed",
                data={"execution_plan": plan},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.execution_plan == plan


class TestAnalysisCompleted:
    async def test_stores_analysis_report(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="analysis_completed",
                data={
                    "analysis_report": "# Dataset Analysis\n150 rows",
                    "split_data_paths": {
                        "train": "/data/train.csv",
                        "val": "/data/val.csv",
                        "test": "/data/test.csv",
                    },
                },
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.analysis_report == "# Dataset Analysis\n150 rows"
        assert exp.split_data_paths["train"] == "/data/train.csv"


class TestSummaryCompleted:
    async def test_stores_summary_report(self, store, experiment_id):
        events = [
            ExperimentEvent(
                event_type="summary_completed",
                data={"summary_report": "# Summary\nBest model: RF"},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert exp.summary_report == "# Summary\nBest model: RF"


class TestUnknownEventType:
    async def test_unknown_event_still_appended(self, store, experiment_id):
        """Unknown event types are still appended to progress_events."""
        events = [
            ExperimentEvent(
                event_type="log_output",
                data={"message": "Training in progress..."},
            ),
        ]
        await _run_sync_with_events(experiment_id, store, events)

        exp = store.get(experiment_id)
        assert len(exp.progress_events) == 1
        assert exp.progress_events[0]["event_type"] == "log_output"
