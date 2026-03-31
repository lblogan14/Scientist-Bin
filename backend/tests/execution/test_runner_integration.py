"""Integration tests for CodeRunner with actual code execution.

These tests verify that the subprocess sandbox works correctly
by executing real Python code (no LLM calls needed).
"""

import json
from pathlib import Path

import pytest

from scientist_bin_backend.execution.runner import CodeRunner, RunConfig

IRIS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "iris_data" / "Iris.csv"


@pytest.fixture()
def runner(tmp_path):
    return CodeRunner(output_base_dir=tmp_path)


async def test_simple_script_execution(runner):
    """Execute a simple Python script and capture output."""
    code = 'print("Hello from sandbox")\nprint("===RESULTS===")\nprint(\'{"status": "ok"}\')'
    result = await runner.execute(RunConfig(experiment_id="test", code=code, timeout_seconds=30))
    assert result.success
    assert "Hello from sandbox" in result.stdout
    assert result.results_json == {"status": "ok"}


async def test_script_with_metrics(runner):
    """Execute a script that uses report_metric()."""
    code = """
report_metric("accuracy", 0.95, step=1)
report_metric("f1", 0.93, step=1)
print("Done")
"""
    result = await runner.execute(RunConfig(experiment_id="test", code=code, timeout_seconds=30))
    assert result.success
    assert len(result.metrics) == 2
    assert result.metrics[0]["name"] == "accuracy"
    assert result.metrics[0]["value"] == 0.95


async def test_script_with_error(runner):
    """Execute a script that raises an error."""
    code = "raise ValueError('intentional test error')"
    result = await runner.execute(RunConfig(experiment_id="test", code=code, timeout_seconds=30))
    assert not result.success
    assert result.error_type == "value_error"
    assert "intentional test error" in result.stderr


async def test_script_timeout(runner):
    """Execute a script that exceeds timeout."""
    code = "import time; time.sleep(60)"
    result = await runner.execute(RunConfig(experiment_id="test", code=code, timeout_seconds=2))
    assert not result.success
    assert result.status == "timeout"
    assert result.error_type == "timeout"


@pytest.mark.skipif(not IRIS_PATH.exists(), reason="Iris dataset not found")
async def test_eda_with_iris_data(runner):
    """Run the EDA template against the actual iris dataset."""
    from scientist_bin_backend.execution.templates import EDA_TEMPLATE

    code = EDA_TEMPLATE.format(
        data_file=str(IRIS_PATH),
        target_column="Species",
        problem_type="classification",
    )
    result = await runner.execute(
        RunConfig(experiment_id="test-eda", code=code, timeout_seconds=30)
    )
    assert result.success, f"EDA failed: {result.stderr}"

    profile = json.loads(result.stdout.strip())
    assert profile["shape"] == [150, 6]
    assert "Species" in profile["column_names"]
    assert profile["target_column"] == "Species"
    assert "Iris-setosa" in profile["class_distribution"]
    assert profile["class_distribution"]["Iris-setosa"] == 50
    assert len(profile["numeric_columns"]) >= 4
    assert "statistics_summary" in profile


@pytest.mark.skipif(not IRIS_PATH.exists(), reason="Iris dataset not found")
async def test_sklearn_training_with_iris(runner):
    """Run a real sklearn training script against the iris dataset.

    This verifies the full code execution pipeline:
    - report_metric() harness injection
    - ===RESULTS=== structured output
    - Actual model training with sklearn
    """
    code = f"""
import json
import os
import time

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

# Load data
df = pd.read_csv({str(IRIS_PATH)!r})
X = df[["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]]
y = LabelEncoder().fit_transform(df["Species"])

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train
start = time.monotonic()
model = RandomForestClassifier(n_estimators=50, random_state=42)
scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
model.fit(X_train, y_train)
test_acc = model.score(X_test, y_test)
elapsed = time.monotonic() - start

# Report metrics
report_metric("cv_accuracy_mean", float(scores.mean()))
report_metric("cv_accuracy_std", float(scores.std()))
report_metric("test_accuracy", float(test_acc))

# Save model
import joblib
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(model, os.path.join(artifacts_dir, "best_model.joblib"))

# Structured results
results = {{
    "results": [{{
        "algorithm": "RandomForestClassifier",
        "metrics": {{"accuracy": float(test_acc), "cv_accuracy": float(scores.mean())}},
        "best_params": {{"n_estimators": 50}},
        "training_time": round(elapsed, 3),
    }}],
    "best_model": "RandomForestClassifier",
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(results))
"""
    result = await runner.execute(
        RunConfig(experiment_id="test-train", code=code, timeout_seconds=60)
    )
    assert result.success, f"Training failed: {result.stderr}"

    # Verify metrics were captured
    assert len(result.metrics) == 3
    metric_names = [m["name"] for m in result.metrics]
    assert "cv_accuracy_mean" in metric_names
    assert "test_accuracy" in metric_names

    # Verify structured results
    assert result.results_json is not None
    assert result.results_json["best_model"] == "RandomForestClassifier"
    accuracy = result.results_json["results"][0]["metrics"]["accuracy"]
    assert accuracy > 0.8  # Iris is an easy dataset

    # Verify artifact was saved
    assert any("best_model.joblib" in a for a in result.artifacts)
