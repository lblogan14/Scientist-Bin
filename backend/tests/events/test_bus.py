"""Tests for the event bus."""

import asyncio

import pytest

from scientist_bin_backend.events.bus import EventBus
from scientist_bin_backend.events.types import ExperimentEvent


@pytest.fixture()
def bus():
    return EventBus()


async def test_emit_and_subscribe(bus):
    received = []

    async def consumer():
        async for event in bus.subscribe("exp1"):
            received.append(event)

    task = asyncio.create_task(consumer())

    # Give subscriber time to register
    await asyncio.sleep(0.01)

    await bus.emit("exp1", ExperimentEvent(event_type="phase_change", data={"phase": "eda"}))
    await bus.emit("exp1", ExperimentEvent(event_type="metric_update", data={"value": 0.9}))
    await bus.close("exp1")

    await task
    assert len(received) == 2
    assert received[0].event_type == "phase_change"
    assert received[1].event_type == "metric_update"


async def test_close_without_subscribers(bus):
    """Closing a non-existent experiment should not raise."""
    await bus.close("nonexistent")


async def test_multiple_subscribers(bus):
    received1 = []
    received2 = []

    async def consumer1():
        async for event in bus.subscribe("exp1"):
            received1.append(event)

    async def consumer2():
        async for event in bus.subscribe("exp1"):
            received2.append(event)

    t1 = asyncio.create_task(consumer1())
    t2 = asyncio.create_task(consumer2())
    await asyncio.sleep(0.01)

    await bus.emit("exp1", ExperimentEvent(event_type="phase_change", data={}))
    await bus.close("exp1")

    await t1
    await t2
    assert len(received1) == 1
    assert len(received2) == 1


async def test_sse_format():
    event = ExperimentEvent(event_type="metric_update", data={"value": 42})
    sse = event.sse_format()
    assert sse["event"] == "metric_update"
    assert '"value":42' in sse["data"]
