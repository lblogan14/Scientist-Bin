"""Tests for execution/sandbox.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scientist_bin_backend.execution.sandbox import (
    build_sandbox_env,
    create_run_directory,
    get_sandbox_python,
    prepare_script,
    validate_data_path,
)


def test_get_sandbox_python():
    """get_sandbox_python returns the current interpreter."""
    result = get_sandbox_python()
    assert result == sys.executable
    assert "python" in result.lower()


def test_create_run_directory(tmp_path: Path):
    """create_run_directory creates the expected directory structure."""
    run_dir = create_run_directory(tmp_path, "exp-001", "run-001")

    assert run_dir.exists()
    assert run_dir.is_dir()
    assert run_dir == tmp_path / "runs" / "exp-001" / "run-001"
    assert (run_dir / "artifacts").exists()


def test_prepare_script(tmp_path: Path):
    """prepare_script writes harness + user code to script.py."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    code = "print('hello world')"
    script_path = prepare_script(code, run_dir)

    assert script_path.exists()
    assert script_path.name == "script.py"

    content = script_path.read_text(encoding="utf-8")
    assert "report_metric" in content  # Harness included
    assert "print('hello world')" in content  # User code included


def test_build_sandbox_env_strips_secrets(monkeypatch, tmp_path: Path):
    """Secret environment variables are excluded from the sandbox."""
    monkeypatch.setenv("GOOGLE_API_KEY", "secret-key")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-anthropic")
    monkeypatch.setenv("HF_TOKEN", "secret-hf")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-aws")
    monkeypatch.setenv("SAFE_VAR", "safe-value")

    run_dir = tmp_path / "run"
    metrics_file = tmp_path / "metrics.jsonl"

    env = build_sandbox_env(run_dir, metrics_file)

    assert "GOOGLE_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "HF_TOKEN" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert env.get("SAFE_VAR") == "safe-value"


def test_build_sandbox_env_preserves_path(monkeypatch, tmp_path: Path):
    """PATH is preserved in the sandbox environment."""
    monkeypatch.setenv("PATH", "/usr/bin:/usr/local/bin")

    env = build_sandbox_env(tmp_path, tmp_path / "m.jsonl")
    assert "PATH" in env


def test_build_sandbox_env_injects_sandbox_vars(tmp_path: Path):
    """Sandbox-specific variables are injected."""
    run_dir = tmp_path / "run"
    metrics_file = tmp_path / "metrics.jsonl"

    env = build_sandbox_env(run_dir, metrics_file)

    assert env["SCIENTIST_BIN_METRICS_FILE"] == str(metrics_file)
    assert env["SCIENTIST_BIN_RUN_DIR"] == str(run_dir)
    assert env["SCIENTIST_BIN_ARTIFACTS_DIR"] == str(run_dir / "artifacts")


def test_validate_data_path_within_root(tmp_path: Path):
    """Valid path within allowed root succeeds."""
    data_file = tmp_path / "data.csv"
    data_file.write_text("a,b\n1,2\n")

    result = validate_data_path(str(data_file), tmp_path)
    assert result == data_file.resolve()


def test_validate_data_path_escapes_root(tmp_path: Path):
    """Path outside allowed root raises ValueError."""
    with pytest.raises(ValueError, match="outside allowed root"):
        validate_data_path("/etc/passwd", tmp_path)


def test_validate_data_path_nonexistent(tmp_path: Path):
    """Non-existent file raises FileNotFoundError."""
    missing = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError, match="not found"):
        validate_data_path(str(missing), tmp_path)
