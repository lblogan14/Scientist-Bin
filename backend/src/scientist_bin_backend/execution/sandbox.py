"""Sandbox setup and teardown for code execution."""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path

from scientist_bin_backend.execution.templates import METRICS_REPORTER_HARNESS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Framework venv resolution
# ---------------------------------------------------------------------------

_FRAMEWORKS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "framework_venvs"

# Maps agent framework_name → venv directory name under frameworks/
FRAMEWORK_VENV_MAP: dict[str, str] = {
    "analyst": "analyst",
    "sklearn": "traditional",
    "flaml": "traditional",
    "pytorch": "pytorch-gpu",
    "pytorch-gpu": "pytorch-gpu",
    "pytorch-cpu": "pytorch-cpu",
    "tensorflow": "tensorflow",
    "transformers": "transformers",
    "diffusers": "diffusers",
}

# Marker package to verify a framework's deps are importable in the current venv
_FRAMEWORK_MARKER_PACKAGE: dict[str, str] = {
    "analyst": "pandas",
    "traditional": "sklearn",
    "pytorch-gpu": "torch",
    "pytorch-cpu": "torch",
    "tensorflow": "tensorflow",
    "transformers": "transformers",
    "diffusers": "diffusers",
}


def get_framework_python(framework_name: str | None = None) -> str:
    """Resolve the Python executable for a framework's execution environment.

    Resolution order:
      1. Provisioned framework venv (``frameworks/<name>/.venv/``)
      2. Current venv if the marker package is importable (extras installed)
      3. ``RuntimeError`` with provisioning instructions

    Returns ``sys.executable`` when *framework_name* is ``None`` (backward
    compat for code that doesn't specify a framework).
    """
    if not framework_name:
        return sys.executable

    venv_name = FRAMEWORK_VENV_MAP.get(framework_name, framework_name)

    # 1. Check for a provisioned framework venv
    venv_dir = _FRAMEWORKS_DIR / venv_name / ".venv"
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    if python_path.exists():
        return str(python_path)

    # 2. Fallback: deps available in the current venv (extras installed)
    marker = _FRAMEWORK_MARKER_PACKAGE.get(venv_name)
    if marker:
        try:
            importlib.import_module(marker)
            logger.debug(
                "Framework '%s' not provisioned, using current venv (extras fallback)",
                framework_name,
            )
            return sys.executable
        except ImportError:
            pass

    # 3. Neither available
    raise RuntimeError(
        f"Framework '{framework_name}' is not available.\n"
        f"Either provision its venv:  scientist-bin provision {venv_name}\n"
        f"Or install as extra:       uv sync --extra {venv_name}"
    )


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
