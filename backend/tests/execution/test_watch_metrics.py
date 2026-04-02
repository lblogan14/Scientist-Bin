"""Tests for watch_metrics_file in execution/metrics_bridge.py.

Covers:
- Reading a JSONL file with valid metric entries
- Empty file returns nothing
- Malformed lines are skipped
- The stop event terminates the watcher
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from scientist_bin_backend.execution.metrics_bridge import watch_metrics_file


class TestWatchMetricsFileValid:
    async def test_reads_valid_entries(self, tmp_path: Path):
        """Valid JSONL entries are collected and returned."""
        metrics_file = tmp_path / "metrics.jsonl"
        entries = [
            {"name": "accuracy", "value": 0.85, "step": 1},
            {"name": "accuracy", "value": 0.92, "step": 2},
            {"name": "f1", "value": 0.88, "step": 2},
        ]
        metrics_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )

        stop = asyncio.Event()

        async def run_watcher():
            return await watch_metrics_file(
                metrics_file,
                on_metric=None,
                poll_interval=0.05,
                stop_event=stop,
            )

        # Set stop event after a brief delay to let watcher read
        async def stop_soon():
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(run_watcher())
        asyncio.create_task(stop_soon())
        result = await task

        assert len(result) == 3
        assert result[0]["name"] == "accuracy"
        assert result[0]["value"] == 0.85
        assert result[2]["name"] == "f1"

    async def test_on_metric_callback_called(self, tmp_path: Path):
        """The on_metric callback is invoked for each entry."""
        metrics_file = tmp_path / "metrics.jsonl"
        metrics_file.write_text(
            json.dumps({"name": "loss", "value": 0.3}) + "\n",
            encoding="utf-8",
        )

        stop = asyncio.Event()
        received = []

        async def on_metric(entry):
            received.append(entry)

        async def stop_soon():
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                on_metric=on_metric,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(stop_soon())
        await task

        assert len(received) == 1
        assert received[0]["name"] == "loss"


class TestWatchMetricsFileEmpty:
    async def test_empty_file_returns_nothing(self, tmp_path: Path):
        """An empty file yields no metrics."""
        metrics_file = tmp_path / "metrics.jsonl"
        metrics_file.write_text("", encoding="utf-8")

        stop = asyncio.Event()

        async def stop_soon():
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(stop_soon())
        result = await task

        assert result == []

    async def test_nonexistent_file_returns_nothing(self, tmp_path: Path):
        """A file that doesn't exist yields no metrics."""
        metrics_file = tmp_path / "does_not_exist.jsonl"

        stop = asyncio.Event()

        async def stop_soon():
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(stop_soon())
        result = await task

        assert result == []


class TestWatchMetricsFileMalformed:
    async def test_malformed_lines_skipped(self, tmp_path: Path):
        """Malformed JSON lines are skipped; valid ones are collected."""
        metrics_file = tmp_path / "metrics.jsonl"
        content = (
            '{"name": "accuracy", "value": 0.9}\n'
            "this is not json\n"
            "{{broken json}}\n"
            '{"name": "f1", "value": 0.85}\n'
        )
        metrics_file.write_text(content, encoding="utf-8")

        stop = asyncio.Event()

        async def stop_soon():
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(stop_soon())
        result = await task

        assert len(result) == 2
        assert result[0]["name"] == "accuracy"
        assert result[1]["name"] == "f1"


class TestWatchMetricsFileStopEvent:
    async def test_stop_event_terminates_watcher(self, tmp_path: Path):
        """Setting the stop event terminates the watcher promptly."""
        metrics_file = tmp_path / "metrics.jsonl"
        metrics_file.write_text("", encoding="utf-8")

        stop = asyncio.Event()

        async def stop_immediately():
            await asyncio.sleep(0.05)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(stop_immediately())

        # The watcher should finish within a reasonable time
        result = await asyncio.wait_for(task, timeout=2.0)
        assert isinstance(result, list)

    async def test_final_read_after_stop(self, tmp_path: Path):
        """After stop, a final read catches entries written during the last poll."""
        metrics_file = tmp_path / "metrics.jsonl"
        metrics_file.write_text("", encoding="utf-8")

        stop = asyncio.Event()

        async def write_then_stop():
            await asyncio.sleep(0.05)
            # Write entries while watcher is running
            metrics_file.write_text(
                json.dumps({"name": "late_metric", "value": 0.99}) + "\n",
                encoding="utf-8",
            )
            await asyncio.sleep(0.15)
            stop.set()

        task = asyncio.create_task(
            watch_metrics_file(
                metrics_file,
                poll_interval=0.05,
                stop_event=stop,
            )
        )
        asyncio.create_task(write_then_stop())
        result = await task

        # The metric should have been captured either during polling or final read
        assert len(result) >= 1
        assert any(m["name"] == "late_metric" for m in result)
