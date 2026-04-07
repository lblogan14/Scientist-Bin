"""Sandbox setup and teardown for code execution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from scientist_bin_backend.execution.templates import METRICS_REPORTER_HARNESS


def get_sandbox_python() -> str:
    """Return the path to the Python executable in the current venv."""
    return sys.executable


def create_run_directory(base_dir: Path, experiment_id: str, run_id: str) -> Path:
    """Create an isolated directory for a single run."""
    run_dir = base_dir / "runs" / experiment_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "artifacts").mkdir(exist_ok=True)
    return run_dir


def prepare_script(code: str, run_dir: Path) -> Path:
    """Write code with harness to a script file in the run directory."""
    script_content = METRICS_REPORTER_HARNESS + code
    script_path = run_dir / "script.py"
    script_path.write_text(script_content, encoding="utf-8")
    return script_path


def build_sandbox_env(run_dir: Path, metrics_file: Path) -> dict[str, str]:
    """Build a sanitized environment for the subprocess.

    Starts from the full environment and strips known-dangerous keys
    (API keys, tokens, secrets). This preserves PATH, Python paths,
    and platform-specific vars needed for package imports.
    """
    secret_prefixes = (
        "GOOGLE_API",
        "SCIENTIST_BIN_GOOGLE",
        "OPENAI_API",
        "ANTHROPIC_API",
        "AWS_SECRET",
        "AZURE_",
        "HF_TOKEN",
    )
    secret_keys = {"API_KEY", "SECRET_KEY", "ACCESS_TOKEN", "AUTH_TOKEN"}

    env = {}
    for k, v in os.environ.items():
        k_upper = k.upper()
        if any(k_upper.startswith(p) for p in secret_prefixes):
            continue
        if k_upper in secret_keys:
            continue
        env[k] = v

    # Inject sandbox-specific vars
    env["SCIENTIST_BIN_METRICS_FILE"] = str(metrics_file)
    env["SCIENTIST_BIN_RUN_DIR"] = str(run_dir)
    env["SCIENTIST_BIN_ARTIFACTS_DIR"] = str(run_dir / "artifacts")
    return env
