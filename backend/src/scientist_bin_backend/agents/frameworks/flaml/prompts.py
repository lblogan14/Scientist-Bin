"""Prompt templates for the FLAML AutoML subagent.

FLAML handles model selection and hyperparameter tuning internally, so these
prompts focus on configuring ``flaml.AutoML`` correctly rather than building
sklearn pipelines manually.

Each prompt provides a template script structure the LLM fills in, plus a
FORBIDDEN PATTERNS section to prevent common mistakes.
"""

FLAML_CLASSIFICATION_PROMPT = """\
You are an expert Python developer specialising in FLAML AutoML.

Generate a complete, self-contained Python script that trains and evaluates a \
classification model using FLAML AutoML.

Objective: {objective}

== Data Profile ==
{data_profile}

== Strategy / Execution Plan ==
{strategy}

== Data File Paths (pre-split by the analyst) ==
Training data: {train_file_path}
Validation data: {val_file_path}
Test data: {test_file_path}

{analysis_context}

{retry_context}

== FORBIDDEN PATTERNS (never use these) ==
- from flaml.training_log import ...    # WRONG — module does not exist
- from flaml.data import ...            # WRONG — use from flaml.automl.data import ...
- automl.model.estimator.feature_importances_  # FRAGILE — use automl.feature_importances_
- pandas.pd                             # WRONG — pandas IS pd

== TEMPLATE SCRIPT (fill in the # TODO sections, keep everything else) ==
```python
import pandas as pd
import numpy as np
from sklearn.metrics import (accuracy_score, f1_score,
    precision_score, recall_score, confusion_matrix)
from flaml import AutoML
from flaml.automl.data import get_output_from_log
import joblib
import json
import os
import time

# 1. Load data
train_df = pd.read_csv("{train_file_path}")
val_df = pd.read_csv("{val_file_path}")

# TODO: identify target column from data profile, drop ID columns if present
target_col = "TODO"
X_train = train_df.drop(columns=[target_col])
y_train = train_df[target_col]
X_val = val_df.drop(columns=[target_col])
y_val = val_df[target_col]

# 2. Train
automl = AutoML()
start_time = time.time()
automl.fit(
    X_train, y_train,
    task="classification",
    time_budget={time_budget},
    metric="{metric}",
    estimator_list={estimator_list},
    eval_method="holdout",
    X_val=X_val, y_val=y_val,
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# 3. Results extraction (use EXACTLY these attribute names)
best_estimator = automl.best_estimator
best_config = automl.best_config

# 4. Predictions + metrics
y_pred_val = automl.predict(X_val)
y_pred_train = automl.predict(X_train)
metrics = {{
    "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
    "val_accuracy": float(accuracy_score(y_val, y_pred_val)),
    "train_f1_weighted": float(f1_score(y_train, y_pred_train, average="weighted")),
    "val_f1_weighted": float(f1_score(y_val, y_pred_val, average="weighted")),
    "train_precision_weighted": float(precision_score(y_train, y_pred_train, average="weighted")),
    "val_precision_weighted": float(precision_score(y_val, y_pred_val, average="weighted")),
    "train_recall_weighted": float(recall_score(y_train, y_pred_train, average="weighted")),
    "val_recall_weighted": float(recall_score(y_val, y_pred_val, average="weighted")),
}}

# 5. Trial history (PRIMARY: config_history attribute, no file I/O needed)
trial_history = []
for i, (est, config, ts) in automl.config_history.items():
    trial_history.append({{"trial_id": int(i), "estimator": est,
        "config": config, "loss": 0.0, "time": float(ts)}})
try:
    time_hist, best_loss_hist, loss_hist, cfg_hist, metric_hist = get_output_from_log(
        filename="flaml_log.log", time_budget={time_budget})
    for idx, entry in enumerate(trial_history):
        if idx < len(loss_hist):
            entry["loss"] = float(loss_hist[idx])
except Exception:
    pass

# 6. Estimator comparison
estimator_comparison = []
for est_name, loss in (automl.best_loss_per_estimator or {{}}).items():
    cfg = (automl.best_config_per_estimator or {{}}).get(est_name, {{}})
    estimator_comparison.append({{"estimator": est_name,
        "best_loss": float(loss), "best_config": cfg}})

# 7. OPTIONAL enrichments (each in try/except)
feature_importances = None
try:
    fi = automl.feature_importances_
    if fi is not None:
        names = list(X_train.columns)
        pairs = sorted(zip(names, fi.tolist()), key=lambda x: abs(x[1]), reverse=True)[:20]
        feature_importances = [{{"feature": n, "importance": v}} for n, v in pairs]
except Exception:
    pass

confusion = None
try:
    labels = sorted(y_val.unique().tolist())
    cm = confusion_matrix(y_val, y_pred_val, labels=labels)
    confusion = {{"labels": [str(l) for l in labels], "matrix": cm.tolist()}}
except Exception:
    pass

# 8. report_metric calls
for k, v in metrics.items():
    report_metric(k, v)

# 9. Output
result = {{
    "results": [{{
        "algorithm": best_estimator or "unknown",
        "metrics": metrics,
        "best_params": best_config or {{}},
        "training_time": training_time,
        "trial_history": trial_history,
        "best_estimator_type": best_estimator or "unknown",
        "estimator_comparison": estimator_comparison,
        "feature_importances": feature_importances,
        "confusion_matrix": confusion,
    }}],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config or {{}},
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(result, default=str))

# 10. Save model
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

Fill in the TODO sections. Keep the rest of the code structure intact.
Return ONLY the Python code, no markdown fences.
"""

FLAML_REGRESSION_PROMPT = """\
You are an expert Python developer specialising in FLAML AutoML.

Generate a complete, self-contained Python script that trains and evaluates a \
regression model using FLAML AutoML.

Objective: {objective}

== Data Profile ==
{data_profile}

== Strategy / Execution Plan ==
{strategy}

== Data File Paths (pre-split by the analyst) ==
Training data: {train_file_path}
Validation data: {val_file_path}
Test data: {test_file_path}

{analysis_context}

{retry_context}

== FORBIDDEN PATTERNS (never use these) ==
- from flaml.training_log import ...    # WRONG — module does not exist
- from flaml.data import ...            # WRONG — use from flaml.automl.data import ...
- automl.model.estimator.feature_importances_  # FRAGILE — use automl.feature_importances_
- pandas.pd                             # WRONG — pandas IS pd

== TEMPLATE SCRIPT (fill in the # TODO sections, keep everything else) ==
```python
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from flaml import AutoML
from flaml.automl.data import get_output_from_log
import joblib
import json
import os
import time

# 1. Load data
train_df = pd.read_csv("{train_file_path}")
val_df = pd.read_csv("{val_file_path}")

# TODO: identify target column from data profile, drop ID columns if present
target_col = "TODO"
X_train = train_df.drop(columns=[target_col])
y_train = train_df[target_col]
X_val = val_df.drop(columns=[target_col])
y_val = val_df[target_col]

# 2. Train
automl = AutoML()
start_time = time.time()
automl.fit(
    X_train, y_train,
    task="regression",
    time_budget={time_budget},
    metric="{metric}",
    estimator_list={estimator_list},
    eval_method="holdout",
    X_val=X_val, y_val=y_val,
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# 3. Results
best_estimator = automl.best_estimator
best_config = automl.best_config

# 4. Predictions + metrics
y_pred_val = automl.predict(X_val)
y_pred_train = automl.predict(X_train)
metrics = {{
    "train_r2": float(r2_score(y_train, y_pred_train)),
    "val_r2": float(r2_score(y_val, y_pred_val)),
    "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
    "val_rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
    "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
    "val_mae": float(mean_absolute_error(y_val, y_pred_val)),
}}

# 5. Trial history
trial_history = []
for i, (est, config, ts) in automl.config_history.items():
    trial_history.append({{"trial_id": int(i), "estimator": est,
        "config": config, "loss": 0.0, "time": float(ts)}})
try:
    time_hist, best_loss_hist, loss_hist, cfg_hist, metric_hist = get_output_from_log(
        filename="flaml_log.log", time_budget={time_budget})
    for idx, entry in enumerate(trial_history):
        if idx < len(loss_hist):
            entry["loss"] = float(loss_hist[idx])
except Exception:
    pass

# 6. Estimator comparison
estimator_comparison = []
for est_name, loss in (automl.best_loss_per_estimator or {{}}).items():
    cfg = (automl.best_config_per_estimator or {{}}).get(est_name, {{}})
    estimator_comparison.append({{"estimator": est_name,
        "best_loss": float(loss), "best_config": cfg}})

# 7. OPTIONAL enrichments
feature_importances = None
try:
    fi = automl.feature_importances_
    if fi is not None:
        names = list(X_train.columns)
        pairs = sorted(zip(names, fi.tolist()), key=lambda x: abs(x[1]), reverse=True)[:20]
        feature_importances = [{{"feature": n, "importance": v}} for n, v in pairs]
except Exception:
    pass

residual_stats = None
actual_vs_predicted = None
try:
    residuals = np.array(y_val) - np.array(y_pred_val)
    residual_stats = {{
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "max_abs_residual": float(np.max(np.abs(residuals))),
        "residual_percentiles": {{
            "25": float(np.percentile(residuals, 25)),
            "50": float(np.percentile(residuals, 50)),
            "75": float(np.percentile(residuals, 75)),
        }},
    }}
    sample_idx = np.random.choice(len(y_val), min(2000, len(y_val)), replace=False)
    actual_vs_predicted = [
        {{"actual": float(y_val.iloc[i]), "predicted": float(y_pred_val[i])}}
        for i in sample_idx
    ]
except Exception:
    pass

# 8. report_metric calls
for k, v in metrics.items():
    report_metric(k, v)

# 9. Output
result = {{
    "results": [{{
        "algorithm": best_estimator or "unknown",
        "metrics": metrics,
        "best_params": best_config or {{}},
        "training_time": training_time,
        "trial_history": trial_history,
        "best_estimator_type": best_estimator or "unknown",
        "estimator_comparison": estimator_comparison,
        "feature_importances": feature_importances,
        "residual_stats": residual_stats,
        "actual_vs_predicted": actual_vs_predicted,
    }}],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config or {{}},
    "errors": [],
}}
print("===RESULTS===")
print(json.dumps(result, default=str))

# 10. Save model
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

Fill in the TODO sections. Keep the rest of the code structure intact.
Return ONLY the Python code, no markdown fences.
"""

FLAML_TS_FORECAST_PROMPT = """\
You are an expert Python developer specialising in FLAML AutoML for time series forecasting.

Generate a complete, self-contained Python script that trains and evaluates a \
time series forecasting model using FLAML AutoML.

Objective: {objective}

== Data Profile ==
{data_profile}

== Strategy / Execution Plan ==
{strategy}

== Data File Paths (pre-split chronologically by the analyst) ==
Training data: {train_file_path}
Validation data: {val_file_path}
Test data: {test_file_path}

{analysis_context}

{retry_context}

== TIME SERIES PARAMETERS ==
Forecast period (horizon): {ts_period}
Temporal column: {temporal_column}
Target column: {target_column}

== FORBIDDEN PATTERNS (never use these) ==
- from flaml.training_log import ...    # WRONG — module does not exist
- from flaml.data import ...            # WRONG — use from flaml.automl.data import ...
- automl.model.estimator.feature_importances_  # FRAGILE — use automl.feature_importances_
- pandas.pd                             # WRONG — pandas IS pd

== TEMPLATE SCRIPT (fill in the # TODO sections, keep everything else) ==
```python
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from flaml import AutoML
from flaml.automl.data import get_output_from_log
import joblib
import json
import os
import time

# 1. Load data
train_df = pd.read_csv("{train_file_path}")
val_df = pd.read_csv("{val_file_path}")

temporal_col = "{temporal_column}"
target_col = "{target_column}"

# 2. Prepare time series data
# CRITICAL: temporal column MUST be datetime64, X must be DataFrame not Series
train_df[temporal_col] = pd.to_datetime(train_df[temporal_col])
val_df[temporal_col] = pd.to_datetime(val_df[temporal_col])
train_df = train_df.sort_values(temporal_col).reset_index(drop=True)
val_df = val_df.sort_values(temporal_col).reset_index(drop=True)

X_train = train_df[[temporal_col]]   # DataFrame with one column
y_train = train_df[target_col].astype(float)
X_val = val_df[[temporal_col]]
y_val = val_df[target_col].astype(float)

# 3. Train
automl = AutoML()
start_time = time.time()
automl.fit(
    X_train, y_train,
    task="ts_forecast",
    period={ts_period},
    time_budget={time_budget},
    metric="{metric}",
    estimator_list={estimator_list},
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# 4. Results
best_estimator = automl.best_estimator
best_config = automl.best_config or {{}}

# 5. Predict (IMPORTANT: may return None)
preds = automl.predict(X_val)
if preds is None:
    preds = np.array([])

# 6. Metrics (each in try/except)
metrics = {{}}
errors = []
if len(preds) > 0 and len(preds) == len(y_val):
    try:
        metrics["val_mape"] = float(mean_absolute_percentage_error(y_val, preds))
    except Exception:
        pass
    try:
        metrics["val_rmse"] = float(np.sqrt(mean_squared_error(y_val, preds)))
    except Exception:
        pass
    try:
        metrics["val_mae"] = float(mean_absolute_error(y_val, preds))
    except Exception:
        pass
else:
    errors.append("Prediction returned empty or mismatched length")

# 7. Trial history
trial_history = []
if hasattr(automl, "config_history") and automl.config_history:
    for i, (est, config, ts) in automl.config_history.items():
        trial_history.append({{
            "trial_id": int(i), "estimator": est,
            "config": config, "loss": 0.0, "time": float(ts),
        }})
try:
    time_hist, best_loss_hist, loss_hist, cfg_hist, metric_hist = get_output_from_log(
        filename="flaml_log.log", time_budget={time_budget})
    for idx, entry in enumerate(trial_history):
        if idx < len(loss_hist):
            entry["loss"] = float(loss_hist[idx])
except Exception:
    pass

# 8. Estimator comparison
estimator_comparison = []
for est_name, loss in (automl.best_loss_per_estimator or {{}}).items():
    cfg = (automl.best_config_per_estimator or {{}}).get(est_name, {{}})
    estimator_comparison.append({{"estimator": est_name,
        "best_loss": float(loss), "best_config": cfg}})

# 9. Forecast data
forecast_data = []
if len(preds) > 0 and len(preds) == len(y_val):
    for ts_val, actual, pred in zip(X_val[temporal_col], y_val, preds):
        forecast_data.append({{
            "timestamp": str(ts_val),
            "actual": float(actual),
            "predicted": float(pred),
        }})

# 10. report_metric calls
for k, v in metrics.items():
    report_metric(k, v)

# 11. Output
result = {{
    "results": [{{
        "algorithm": best_estimator or "unknown",
        "metrics": metrics,
        "best_params": best_config,
        "training_time": training_time,
        "trial_history": trial_history,
        "best_estimator_type": best_estimator or "unknown",
        "estimator_comparison": estimator_comparison,
        "forecast_data": forecast_data,
    }}],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config,
    "errors": errors,
}}
print("===RESULTS===")
print(json.dumps(result, default=str))

# 12. Save model (save entire automl object, not just estimator)
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

Fill in the TODO sections. Keep the rest of the code structure intact.
Return ONLY the Python code, no markdown fences.
"""
