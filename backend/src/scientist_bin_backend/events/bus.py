"""Per-experiment event bus backed by asyncio.Queue."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from scientist_bin_backend.events.types import ExperimentEvent


class EventBus:
    """Manages per-experiment event queues for real-time streaming."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[ExperimentEvent | None]]] = {}

    async def emit(self, experiment_id: str, event: ExperimentEvent) -> None:
        """Publish an event to all subscribers of an experiment."""
        queues = self._queues.get(experiment_id, [])
        for q in queues:
            await q.put(event)

    async def subscribe(self, experiment_id: str) -> AsyncIterator[ExperimentEvent]:
        """Subscribe to events for an experiment. Yields events until closed."""
        q: asyncio.Queue[ExperimentEvent | None] = asyncio.Queue()
        if experiment_id not in self._queues:
            self._queues[experiment_id] = []
        self._queues[experiment_id].append(q)

        try:
            while True:
                event = await q.get()
                if event is None:
                    break
                yield event
        finally:
            self._queues.get(experiment_id, []).remove(q) if q in self._queues.get(
                experiment_id, []
            ) else None

    async def close(self, experiment_id: str) -> None:
        """Signal all subscribers that no more events will be sent."""
        queues = self._queues.pop(experiment_id, [])
        for q in queues:
            await q.put(None)


# Global singleton
event_bus = EventBus()
