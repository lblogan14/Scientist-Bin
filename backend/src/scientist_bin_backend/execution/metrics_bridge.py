"""File-based IPC for real-time metrics collection from training subprocesses."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path


async def watch_metrics_file(
    metrics_file: Path,
    on_metric: Callable[[dict], Awaitable[None]] | None = None,
    poll_interval: float = 0.5,
    stop_event: asyncio.Event | None = None,
) -> list[dict]:
    """Watch a JSONL metrics file and invoke callback for each new entry.

    Returns the complete list of metrics when done.
    Cross-platform: uses polling (no inotify dependency).
    """
    metrics: list[dict] = []
    last_position = 0

    while True:
        if stop_event and stop_event.is_set():
            break

        if metrics_file.exists():
            with open(metrics_file, encoding="utf-8") as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    metrics.append(entry)
                    if on_metric:
                        await on_metric(entry)
                except json.JSONDecodeError:
                    continue

        await asyncio.sleep(poll_interval)

    # Final read to catch any remaining entries
    if metrics_file.exists():
        with open(metrics_file, encoding="utf-8") as f:
            f.seek(last_position)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    metrics.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return metrics


def parse_results_json(stdout: str) -> dict | None:
    """Extract the structured results JSON from stdout.

    Looks for ===RESULTS=== marker followed by JSON.
    """
    marker = "===RESULTS==="
    if marker not in stdout:
        return None

    json_str = stdout.split(marker)[-1].strip()
    # Handle case where there's trailing output after JSON
    # Find the end of the JSON object
    brace_count = 0
    json_end = -1
    in_string = False
    escape_next = False

    for i, ch in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            brace_count += 1
        elif ch == "}":
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break

    if json_end == -1:
        return None

    try:
        return json.loads(json_str[:json_end])
    except json.JSONDecodeError:
        return None
