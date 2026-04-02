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

    def pre_register(self, experiment_id: str) -> asyncio.Queue[ExperimentEvent | None]:
        """Pre-register a queue before the agent starts emitting events.

        Call this *before* launching the agent so that no early events are lost.
        Pass the returned queue to :meth:`consume` to iterate over events.
        """
        q: asyncio.Queue[ExperimentEvent | None] = asyncio.Queue()
        self._queues.setdefault(experiment_id, []).append(q)
        return q

    async def consume(
        self, experiment_id: str, queue: asyncio.Queue[ExperimentEvent | None]
    ) -> AsyncIterator[ExperimentEvent]:
        """Iterate over events from a pre-registered queue until closed."""
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            queues = self._queues.get(experiment_id, [])
            if queue in queues:
                queues.remove(queue)

    async def subscribe(self, experiment_id: str) -> AsyncIterator[ExperimentEvent]:
        """Subscribe to events for an experiment. Yields events until closed.

        For cases where you need to guarantee no events are missed, use
        :meth:`pre_register` + :meth:`consume` instead.
        """
        q = self.pre_register(experiment_id)
        async for event in self.consume(experiment_id, q):
            yield event

    async def close(self, experiment_id: str) -> None:
        """Signal all subscribers that no more events will be sent."""
        queues = self._queues.pop(experiment_id, [])
        for q in queues:
            await q.put(None)


# Global singleton
event_bus = EventBus()
