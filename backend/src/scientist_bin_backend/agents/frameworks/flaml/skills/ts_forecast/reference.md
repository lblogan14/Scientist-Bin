# FLAML Time Series Forecasting Reference

## Complete Working Code Pattern

The following is a **complete, working script** for FLAML time series forecasting.
Use this as a direct template — adapt file paths and column names only.

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

# ---- 1. Load data ----
train_df = pd.read_csv("TRAIN_PATH")
val_df = pd.read_csv("VAL_PATH")

temporal_col = "DATE"       # The datetime column name
target_col = "IPG2211A2N"   # The target column name

# ---- 2. Prepare time series data ----
# CRITICAL: temporal column MUST be datetime64
train_df[temporal_col] = pd.to_datetime(train_df[temporal_col])
val_df[temporal_col] = pd.to_datetime(val_df[temporal_col])

# Sort chronologically
train_df = train_df.sort_values(temporal_col).reset_index(drop=True)
val_df = val_df.sort_values(temporal_col).reset_index(drop=True)

# X must be a DataFrame with the temporal column (NOT a Series)
X_train = train_df[[temporal_col]]
y_train = train_df[target_col].astype(float)
X_val = val_df[[temporal_col]]
y_val = val_df[target_col].astype(float)

# ---- 3. Train with FLAML AutoML ----
automl = AutoML()
start_time = time.time()
automl.fit(
    X_train, y_train,
    task="ts_forecast",
    period=12,                 # forecast horizon (number of future steps)
    time_budget=120,
    metric="mape",
    estimator_list=["lgbm", "xgboost", "rf", "extra_tree", "prophet", "arima", "sarimax"],
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# ---- 4. Extract results ----
best_estimator = automl.best_estimator    # e.g. "lgbm", "prophet", "arima"
best_config = automl.best_config or {}
best_loss = automl.best_loss

# ---- 5. Predict on validation set ----
# IMPORTANT: predict() may return None — always guard
preds = automl.predict(X_val)
if preds is None:
    preds = np.array([])

# ---- 6. Compute metrics (each in try/except) ----
metrics = {}
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

# ---- 7. Trial history (PRIMARY: use config_history attribute) ----
trial_history = []
if hasattr(automl, "config_history") and automl.config_history:
    for i, (est, config, ts) in automl.config_history.items():
        trial_history.append({
            "trial_id": int(i), "estimator": est,
            "config": config, "loss": 0.0, "time": float(ts),
        })
# SECONDARY: parse log for loss values
try:
    time_hist, best_loss_hist, loss_hist, cfg_hist, metric_hist = get_output_from_log(
        filename="flaml_log.log", time_budget=120)
    for idx, entry in enumerate(trial_history):
        if idx < len(loss_hist):
            entry["loss"] = float(loss_hist[idx])
except Exception:
    pass

# ---- 8. Estimator comparison ----
estimator_comparison = []
for est_name, loss in (automl.best_loss_per_estimator or {}).items():
    cfg = (automl.best_config_per_estimator or {}).get(est_name, {})
    estimator_comparison.append({"estimator": est_name, "best_loss": float(loss), "best_config": cfg})

# ---- 9. Build forecast_data ----
forecast_data = []
if len(preds) > 0 and len(preds) == len(y_val):
    for ts_val, actual, pred in zip(X_val[temporal_col], y_val, preds):
        forecast_data.append({
            "timestamp": str(ts_val),
            "actual": float(actual),
            "predicted": float(pred),
        })

# ---- 10. Output ----
result = {
    "results": [{
        "algorithm": best_estimator or "unknown",
        "metrics": metrics,
        "best_params": best_config,
        "training_time": training_time,
        "trial_history": trial_history,
        "best_estimator_type": best_estimator or "unknown",
        "estimator_comparison": estimator_comparison,
        "forecast_data": forecast_data,
    }],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config,
    "errors": [],
}
print("===RESULTS===")
print(json.dumps(result, default=str))

# ---- 11. Save model (save entire automl object) ----
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

## Critical TS Gotchas

1. **X_train must be a DataFrame**, not a Series. Use `df[["col"]]` not `df["col"]`
2. **Temporal column must be datetime64**. Always call `pd.to_datetime()` first
3. **predict() can return None**. Always check before using
4. **period parameter** = forecast horizon during training validation, not prediction length
5. **Sort chronologically** before passing to FLAML
6. **Save entire automl object** with joblib, not just `automl.model.estimator`

## Estimator Guide

| Estimator | Type | Best For |
|-----------|------|----------|
| `lgbm` | ML | Complex patterns with exogenous features |
| `xgboost` | ML | Robust tabular forecasting |
| `prophet` | Statistical | Seasonal data with holidays |
| `arima` | Statistical | Stationary/trending data |
| `sarimax` | Statistical | Seasonal + exogenous variables |

## FORBIDDEN Patterns (Never Use)

- `from flaml.training_log import ...` -- WRONG, does not exist
- `from flaml.data import ...` -- WRONG, use `from flaml.automl.data import ...`
- `pandas.pd` -- WRONG, pandas IS pd
- `automl.model.estimator.feature_importances_` -- FRAGILE, use `automl.feature_importances_`
