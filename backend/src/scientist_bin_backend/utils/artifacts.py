"""Shared artifact saving logic for CLI and API."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# outputs/ is always relative to the backend package root
_OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "outputs"


def save_experiment_artifacts(
    experiment_id: str,
    result_dict: dict,
) -> dict[str, str]:
    """Save model, results JSON, and journal to top-level output directories.

    Returns a dict mapping artifact type to saved file path.
    """
    outputs_dir = _OUTPUTS_DIR
    runs_dir = outputs_dir / "runs" / experiment_id
    models_dir = outputs_dir / "models"
    results_dir = outputs_dir / "results"
    logs_dir = outputs_dir / "logs"
    saved: dict[str, str] = {}

    # Save result JSON
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        result_path = results_dir / f"{experiment_id}.json"
        result_path.write_text(
            json.dumps(result_dict, indent=2, default=str),
            encoding="utf-8",
        )
        saved["results"] = str(result_path)
    except Exception:
        logger.exception("Failed to save results JSON for %s", experiment_id)

    # Copy best model from run artifacts
    if runs_dir.exists():
        model_files = sorted(
            runs_dir.glob("*/artifacts/best_model.joblib"),
            key=lambda p: p.stat().st_mtime,
        )
        if model_files:
            try:
                models_dir.mkdir(parents=True, exist_ok=True)
                dest = models_dir / f"{experiment_id}.joblib"
                shutil.copy2(model_files[-1], dest)
                saved["model"] = str(dest)
            except Exception:
                logger.exception("Failed to save model for %s", experiment_id)

        # Copy journal
        journal_src = runs_dir / "journal.jsonl"
        if journal_src.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                dest = logs_dir / f"{experiment_id}.jsonl"
                shutil.copy2(journal_src, dest)
                saved["journal"] = str(dest)
            except Exception:
                logger.exception("Failed to save journal for %s", experiment_id)

    return saved
