"""FLAML code generation and execution tests (Tier 1 — no LLM calls).

Hand-written FLAML training scripts are executed through CodeRunner to verify
that the framework venv (or extras) works correctly. These tests validate
the plumbing without requiring a GOOGLE_API_KEY.

Run with::

    uv run pytest tests/execution/test_flaml_codegen.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scientist_bin_backend.execution.runner import CodeRunner, RunConfig

flaml = pytest.importorskip(  # noqa: E402
    "flaml", reason="FLAML not installed — run: uv sync --extra traditional",
)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
IRIS_PATH = _DATA_DIR / "iris_data" / "Iris.csv"
WINE_PATH = _DATA_DIR / "wine_data" / "WineQT.csv"
ELECTRIC_PATH = _DATA_DIR / "electric_data" / "Electric_Production.csv"


@pytest.fixture()
def runner(tmp_path):
    return CodeRunner(output_base_dir=tmp_path)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IRIS_PATH.is_file(), reason=f"Dataset not found: {IRIS_PATH}")
async def test_flaml_classification_script_runs(runner):
    """Execute a hand-written FLAML classification script on Iris."""
    code = f"""\
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from flaml import AutoML
import json

df = pd.read_csv({str(IRIS_PATH)!r})
target_col = "Species"
X = df.drop(columns=[target_col, "Id"], errors="ignore")
y = df[target_col]
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

automl = AutoML()
automl.fit(X_train, y_train, task="classification", time_budget=10, seed=42, verbose=0)

y_pred = automl.predict(X_val)
acc = float(accuracy_score(y_val, y_pred))
report_metric("accuracy", acc)

result = {{
    "results": [{{
        "algorithm": automl.best_estimator or "unknown",
        "metrics": {{"accuracy": acc}},
        "best_params": automl.best_config or {{}},
        "training_time": 0.0,
    }}],
    "best_model": automl.best_estimator or "unknown",
    "hyperparameters": automl.best_config or {{}},
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(result, default=str))
"""
    result = await runner.execute(
        RunConfig(experiment_id="flaml-cls-test", code=code, timeout_seconds=120)
    )
    assert result.success, f"Script failed: {result.stderr[:500]}"
    assert result.results_json is not None
    assert result.results_json["best_model"] != "unknown"
    assert len(result.metrics) >= 1
    # Accuracy should be reasonable on Iris
    acc = result.results_json["results"][0]["metrics"]["accuracy"]
    assert acc > 0.5, f"Accuracy too low: {acc}"


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not WINE_PATH.is_file(), reason=f"Dataset not found: {WINE_PATH}")
async def test_flaml_regression_script_runs(runner):
    """Execute a hand-written FLAML regression script on Wine Quality."""
    code = f"""\
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from flaml import AutoML
import json

df = pd.read_csv({str(WINE_PATH)!r})
target_col = "quality"
X = df.drop(columns=[target_col])
y = df[target_col]

from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

automl = AutoML()
automl.fit(X_train, y_train, task="regression", time_budget=10, seed=42, verbose=0)

y_pred = automl.predict(X_val)
r2 = float(r2_score(y_val, y_pred))
rmse = float(np.sqrt(mean_squared_error(y_val, y_pred)))
report_metric("r2", r2)
report_metric("rmse", rmse)

result = {{
    "results": [{{
        "algorithm": automl.best_estimator or "unknown",
        "metrics": {{"r2": r2, "rmse": rmse}},
        "best_params": automl.best_config or {{}},
        "training_time": 0.0,
    }}],
    "best_model": automl.best_estimator or "unknown",
    "hyperparameters": automl.best_config or {{}},
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(result, default=str))
"""
    result = await runner.execute(
        RunConfig(experiment_id="flaml-reg-test", code=code, timeout_seconds=120)
    )
    assert result.success, f"Script failed: {result.stderr[:500]}"
    assert result.results_json is not None
    assert result.results_json["best_model"] != "unknown"
    assert len(result.metrics) >= 2


# ---------------------------------------------------------------------------
# Time series forecast
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not ELECTRIC_PATH.is_file(), reason=f"Dataset not found: {ELECTRIC_PATH}"
)
async def test_flaml_ts_forecast_script_runs(runner):
    """Execute a hand-written FLAML ts_forecast script on Electric Production."""
    code = f"""\
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error
from flaml import AutoML
import json

df = pd.read_csv({str(ELECTRIC_PATH)!r})
df["DATE"] = pd.to_datetime(df["DATE"])
df = df.sort_values("DATE").reset_index(drop=True)

# Simple 80/20 chronological split
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
val_df = df.iloc[split_idx:]

X_train = train_df[["DATE"]]
y_train = train_df["IPG2211A2N"].astype(float)
X_val = val_df[["DATE"]]
y_val = val_df["IPG2211A2N"].astype(float)

automl = AutoML()
automl.fit(
    X_train, y_train,
    task="ts_forecast",
    period=12,
    time_budget=15,
    seed=42,
    verbose=0,
)

preds = automl.predict(X_val)
metrics = {{}}
if preds is not None and len(preds) == len(y_val):
    mae = float(mean_absolute_error(y_val, preds))
    report_metric("mae", mae)
    metrics["mae"] = mae

    forecast_data = [
        {{"timestamp": str(t), "actual": float(a), "predicted": float(p)}}
        for t, a, p in zip(X_val["DATE"], y_val, preds)
    ]
else:
    forecast_data = []

result = {{
    "results": [{{
        "algorithm": automl.best_estimator or "unknown",
        "metrics": metrics,
        "best_params": automl.best_config or {{}},
        "training_time": 0.0,
        "forecast_data": forecast_data,
    }}],
    "best_model": automl.best_estimator or "unknown",
    "hyperparameters": automl.best_config or {{}},
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(result, default=str))
"""
    result = await runner.execute(
        RunConfig(experiment_id="flaml-ts-test", code=code, timeout_seconds=180)
    )
    assert result.success, f"Script failed: {result.stderr[:500]}"
    assert result.results_json is not None
    assert result.results_json["best_model"] != "unknown"


# ---------------------------------------------------------------------------
# Prompt patterns
# ---------------------------------------------------------------------------


def test_flaml_code_patterns_present():
    """Verify FLAML prompts reference the expected FLAML-specific patterns."""
    from scientist_bin_backend.agents.frameworks.flaml.prompts import (
        FLAML_CLASSIFICATION_PROMPT,
        FLAML_REGRESSION_PROMPT,
        FLAML_TS_FORECAST_PROMPT,
    )

    for prompt in [FLAML_CLASSIFICATION_PROMPT, FLAML_REGRESSION_PROMPT, FLAML_TS_FORECAST_PROMPT]:
        assert "flaml" in prompt.lower() or "AutoML" in prompt
        assert "automl.fit" in prompt
        assert "time_budget" in prompt
        assert "estimator_list" in prompt
        assert "===RESULTS===" in prompt
        assert "report_metric" in prompt

    # TS-specific patterns
    assert "ts_forecast" in FLAML_TS_FORECAST_PROMPT
    assert "period" in FLAML_TS_FORECAST_PROMPT

    # Classification-specific
    assert "accuracy" in FLAML_CLASSIFICATION_PROMPT
    assert "confusion_matrix" in FLAML_CLASSIFICATION_PROMPT.lower()

    # Regression-specific
    assert "r2" in FLAML_REGRESSION_PROMPT
    assert "rmse" in FLAML_REGRESSION_PROMPT.lower()
