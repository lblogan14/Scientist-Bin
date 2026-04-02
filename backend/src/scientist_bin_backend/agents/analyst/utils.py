"""Shared utilities for analyst agent nodes."""

from __future__ import annotations

from pathlib import Path


def resolve_run_subdir(experiment_id: str, subdir: str) -> Path:
    """Resolve an output subdirectory for an experiment run.

    Returns ``outputs/runs/{experiment_id}/{subdir}`` relative to the backend root.
    """
    backend_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    return backend_root / "outputs" / "runs" / experiment_id / subdir


def read_data_sample(data_file_path: str, n_lines: int = 6) -> str:
    """Read the first *n_lines* of a data file for LLM context."""
    try:
        with open(data_file_path, encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(n_lines)]
        return "".join(lines)
    except Exception:
        return "(Could not read data sample)"
