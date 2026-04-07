"""Tests for get_framework_python() resolution logic."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scientist_bin_backend.execution.sandbox import (
    FRAMEWORK_VENV_MAP,
    get_framework_python,
)


def test_none_returns_sys_executable():
    """Passing None returns the current interpreter."""
    assert get_framework_python(None) == sys.executable


def test_empty_string_returns_sys_executable():
    """Passing empty string returns the current interpreter."""
    assert get_framework_python("") == sys.executable


def test_framework_venv_map_has_expected_keys():
    """All core framework agent names are in the mapping."""
    for name in ("analyst", "sklearn", "flaml", "pytorch-gpu", "pytorch-cpu", "tensorflow"):
        assert name in FRAMEWORK_VENV_MAP


def test_sklearn_maps_to_traditional():
    """sklearn and flaml both map to the 'traditional' venv."""
    assert FRAMEWORK_VENV_MAP["sklearn"] == "traditional"
    assert FRAMEWORK_VENV_MAP["flaml"] == "traditional"


def test_provisioned_venv_takes_priority(tmp_path: Path):
    """When a framework venv exists, its Python is returned."""
    venv_dir = tmp_path / "traditional" / ".venv"
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("fake python")

    with patch("scientist_bin_backend.execution.sandbox._FRAMEWORKS_DIR", tmp_path):
        result = get_framework_python("sklearn")

    assert result == str(python_path)


def test_falls_back_to_sys_executable_when_marker_importable(tmp_path: Path):
    """When no venv exists but the marker package is importable, falls back to sys.executable."""
    # tmp_path has no venvs, but sklearn is importable in the current env (extras installed)
    with patch("scientist_bin_backend.execution.sandbox._FRAMEWORKS_DIR", tmp_path):
        result = get_framework_python("sklearn")

    # sklearn should be available in our test venv (via extras)
    assert result == sys.executable


def test_raises_when_nothing_available(tmp_path: Path):
    """When no venv and no importable marker, raises RuntimeError."""
    with (
        patch("scientist_bin_backend.execution.sandbox._FRAMEWORKS_DIR", tmp_path),
        patch("scientist_bin_backend.execution.sandbox.importlib") as mock_importlib,
    ):
        mock_importlib.import_module.side_effect = ImportError("no module")
        with pytest.raises(RuntimeError, match="not available"):
            get_framework_python("tensorflow")
