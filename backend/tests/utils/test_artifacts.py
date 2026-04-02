"""Tests for save_experiment_artifacts utility."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scientist_bin_backend.utils.artifacts import save_experiment_artifacts


def test_save_creates_results_json(tmp_path: Path):
    """Results JSON is created with correct content."""
    with patch("scientist_bin_backend.utils.artifacts._OUTPUTS_DIR", tmp_path):
        result_dict = {"framework": "sklearn", "status": "success", "iterations": 3}
        saved = save_experiment_artifacts("exp-001", result_dict)

    result_file = tmp_path / "results" / "exp-001.json"
    assert result_file.exists()
    content = json.loads(result_file.read_text())
    assert content["framework"] == "sklearn"
    assert content["iterations"] == 3
    assert "results" in saved


def test_save_copies_model(tmp_path: Path):
    """Best model joblib is copied to outputs/models/."""
    runs_dir = tmp_path / "runs" / "exp-002" / "run_001" / "artifacts"
    runs_dir.mkdir(parents=True)
    model_src = runs_dir / "best_model.joblib"
    model_src.write_bytes(b"fake-model-data")

    with patch("scientist_bin_backend.utils.artifacts._OUTPUTS_DIR", tmp_path):
        saved = save_experiment_artifacts("exp-002", {"status": "success"})

    model_dest = tmp_path / "models" / "exp-002.joblib"
    assert model_dest.exists()
    assert model_dest.read_bytes() == b"fake-model-data"
    assert "model" in saved


def test_save_copies_journal(tmp_path: Path):
    """Journal JSONL is copied to outputs/logs/."""
    runs_dir = tmp_path / "runs" / "exp-003"
    runs_dir.mkdir(parents=True)
    journal_src = runs_dir / "journal.jsonl"
    journal_src.write_text('{"event": "start"}\n', encoding="utf-8")

    with patch("scientist_bin_backend.utils.artifacts._OUTPUTS_DIR", tmp_path):
        saved = save_experiment_artifacts("exp-003", {"status": "success"})

    journal_dest = tmp_path / "logs" / "exp-003.jsonl"
    assert journal_dest.exists()
    assert "journal" in saved


def test_save_handles_missing_runs_dir(tmp_path: Path):
    """When no runs directory exists, only results JSON is saved."""
    with patch("scientist_bin_backend.utils.artifacts._OUTPUTS_DIR", tmp_path):
        saved = save_experiment_artifacts("exp-none", {"status": "failed"})

    assert "results" in saved
    assert "model" not in saved
    assert "journal" not in saved


def test_save_copies_analysis_report(tmp_path: Path):
    """Analysis report markdown is copied to results dir."""
    data_dir = tmp_path / "runs" / "exp-004" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "analysis_report.md").write_text("# Analysis", encoding="utf-8")

    with patch("scientist_bin_backend.utils.artifacts._OUTPUTS_DIR", tmp_path):
        saved = save_experiment_artifacts("exp-004", {"status": "success"})

    assert (tmp_path / "results" / "exp-004_analysis.md").exists()
    assert "analysis" in saved
