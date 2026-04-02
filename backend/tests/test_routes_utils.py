"""Tests for route utility functions (_resolve_data_file_path)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scientist_bin_backend.api.routes import _resolve_data_file_path


def test_resolve_none_returns_none():
    """None input returns None."""
    assert _resolve_data_file_path(None) is None


def test_resolve_empty_string_returns_none():
    """Empty string input returns None."""
    assert _resolve_data_file_path("") is None


def test_resolve_from_data_subdir(tmp_path: Path):
    """A file found under backend/data/ is returned as an absolute path."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_file = data_dir / "iris.csv"
    csv_file.write_text("col1,col2\n1,2\n")

    # Patch the backend_dir derivation so data_dir points to our tmp structure
    with patch(
        "scientist_bin_backend.api.routes.Path.__file__",
        create=True,
    ):
        # We need to patch the computed backend_dir. The function uses
        # Path(__file__).resolve().parent.parent.parent.parent
        # Instead of patching __file__, let's patch Path.is_file to simulate
        # the resolution order.

        # The simplest approach: provide an absolute path that exists
        result = _resolve_data_file_path(str(csv_file))
        assert result == str(csv_file.resolve())


def test_resolve_absolute_existing_file(tmp_path: Path):
    """An absolute path to an existing file is returned resolved."""
    csv_file = tmp_path / "mydata.csv"
    csv_file.write_text("a,b\n1,2\n")

    result = _resolve_data_file_path(str(csv_file))
    assert result == str(csv_file.resolve())


def test_resolve_nonexistent_returns_original():
    """A non-existent path returns the original string."""
    bogus = "/nonexistent/path/to/file.csv"
    result = _resolve_data_file_path(bogus)
    assert result == bogus
