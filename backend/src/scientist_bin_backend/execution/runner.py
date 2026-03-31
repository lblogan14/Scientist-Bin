"""Sandboxed code execution via subprocess."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from scientist_bin_backend.execution.metrics_bridge import (
    parse_results_json,
    watch_metrics_file,
)
from scientist_bin_backend.execution.sandbox import (
    build_sandbox_env,
    create_run_directory,
    get_sandbox_python,
    prepare_script,
)


@dataclass
class RunConfig:
    """Configuration for a single code execution run."""

    experiment_id: str
    code: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timeout_seconds: int = 300
    max_output_bytes: int = 1_000_000  # 1 MB


@dataclass
class RunResult:
    """Structured result from a code execution."""

    run_id: str
    exit_code: int
    stdout: str
    stderr: str
    metrics: list[dict]
    results_json: dict | None  # Parsed from ===RESULTS=== marker
    artifacts: list[str]
    wall_time_seconds: float
    status: Literal["completed", "failed", "timeout"]

    @property
    def success(self) -> bool:
        return self.status == "completed" and self.exit_code == 0

    @property
    def error_type(self) -> str | None:
        if self.success:
            return None
        if self.status == "timeout":
            return "timeout"
        return _classify_error(self.stderr)


def _classify_error(stderr: str) -> str:
    """Classify an error from stderr into a category."""
    if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
        return "import_error"
    if "SyntaxError" in stderr:
        return "syntax_error"
    if "FileNotFoundError" in stderr:
        return "data_error"
    if "MemoryError" in stderr:
        return "memory_error"
    if "KeyError" in stderr:
        return "key_error"
    if "ValueError" in stderr:
        return "value_error"
    return "runtime_error"


class CodeRunner:
    """Execute Python code in an isolated subprocess."""

    def __init__(
        self,
        output_base_dir: Path | None = None,
        python_path: str | None = None,
    ) -> None:
        if output_base_dir is None:
            # Resolve relative to the backend package root
            output_base_dir = Path(__file__).resolve().parent.parent.parent.parent / "outputs"
        self.output_base_dir = output_base_dir.resolve()
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.python_path = python_path or get_sandbox_python()
        self._active_processes: dict[str, asyncio.subprocess.Process] = {}

    async def execute(
        self,
        config: RunConfig,
        on_metric: Callable[[dict], Awaitable[None]] | None = None,
    ) -> RunResult:
        """Run code in a subprocess and return structured result."""
        run_dir = create_run_directory(self.output_base_dir, config.experiment_id, config.run_id)
        metrics_file = run_dir / "metrics.jsonl"
        script_path = prepare_script(config.code, run_dir)
        env = build_sandbox_env(run_dir, metrics_file)

        start_time = time.monotonic()
        stop_event = asyncio.Event()

        # Start metrics watcher in background
        metrics_task = asyncio.create_task(
            watch_metrics_file(metrics_file, on_metric, stop_event=stop_event)
        )

        try:
            process = await asyncio.create_subprocess_exec(
                self.python_path,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(run_dir),
                env=env,
            )
            self._active_processes[config.run_id] = process

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=config.timeout_seconds
                )
                status: Literal["completed", "failed", "timeout"] = (
                    "completed" if process.returncode == 0 else "failed"
                )
            except TimeoutError:
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()
                status = "timeout"

        finally:
            self._active_processes.pop(config.run_id, None)
            stop_event.set()
            # Give the watcher a moment to finish its final read
            await asyncio.sleep(0.1)

        wall_time = time.monotonic() - start_time

        stdout = stdout_bytes.decode("utf-8", errors="replace")[: config.max_output_bytes]
        stderr = stderr_bytes.decode("utf-8", errors="replace")[: config.max_output_bytes]

        # Save logs to disk
        (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        (run_dir / "completion.json").write_text(
            json.dumps(
                {
                    "exit_code": process.returncode,
                    "status": status,
                    "wall_time_seconds": round(wall_time, 3),
                },
            ),
            encoding="utf-8",
        )

        # Collect metrics from watcher
        metrics = await metrics_task

        # Parse structured results from stdout
        results_json = parse_results_json(stdout)

        # Collect artifacts
        artifacts_dir = run_dir / "artifacts"
        artifacts = [str(p.relative_to(run_dir)) for p in artifacts_dir.rglob("*") if p.is_file()]

        return RunResult(
            run_id=config.run_id,
            exit_code=process.returncode or 0,
            stdout=stdout,
            stderr=stderr,
            metrics=metrics,
            results_json=results_json,
            artifacts=artifacts,
            wall_time_seconds=round(wall_time, 3),
            status=status,
        )

    async def kill(self, run_id: str) -> None:
        """Kill an active subprocess."""
        process = self._active_processes.get(run_id)
        if process:
            process.kill()

    async def kill_all(self) -> None:
        """Kill all active subprocesses."""
        for process in self._active_processes.values():
            process.kill()
        self._active_processes.clear()
