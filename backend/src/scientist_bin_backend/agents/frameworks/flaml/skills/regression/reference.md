# FLAML Regression Reference

## Complete Working Code Pattern

The following is a **complete, working script** for FLAML regression.
Use this as a direct template — adapt file paths and column names only.

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

# ---- 1. Load data ----
train_df = pd.read_csv("TRAIN_PATH")
val_df = pd.read_csv("VAL_PATH")

target_col = "TARGET_COLUMN"
X_train = train_df.drop(columns=[target_col])
y_train = train_df[target_col]
X_val = val_df.drop(columns=[target_col])
y_val = val_df[target_col]

# ---- 2. Train with FLAML AutoML ----
automl = AutoML()
start_time = time.time()
automl.fit(
    X_train, y_train,
    task="regression",
    time_budget=120,
    metric="r2",
    estimator_list=["lgbm", "xgboost", "rf", "extra_tree"],
    eval_method="holdout",
    X_val=X_val, y_val=y_val,
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# ---- 3. Extract results ----
best_estimator = automl.best_estimator
best_config = automl.best_config
best_loss = automl.best_loss

# ---- 4. Predictions and metrics ----
y_pred_val = automl.predict(X_val)
y_pred_train = automl.predict(X_train)
metrics = {
    "train_r2": float(r2_score(y_train, y_pred_train)),
    "val_r2": float(r2_score(y_val, y_pred_val)),
    "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
    "val_rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
    "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
    "val_mae": float(mean_absolute_error(y_val, y_pred_val)),
}

# ---- 5. Trial history (PRIMARY: use config_history attribute) ----
trial_history = []
for i, (est, config, ts) in automl.config_history.items():
    trial_history.append({"trial_id": int(i), "estimator": est, "config": config, "loss": 0.0, "time": float(ts)})
try:
    time_hist, best_loss_hist, loss_hist, cfg_hist, metric_hist = get_output_from_log(
        filename="flaml_log.log", time_budget=120)
    for idx, entry in enumerate(trial_history):
        if idx < len(loss_hist):
            entry["loss"] = float(loss_hist[idx])
except Exception:
    pass

# ---- 6. Estimator comparison ----
estimator_comparison = []
for est_name, loss in (automl.best_loss_per_estimator or {}).items():
    cfg = (automl.best_config_per_estimator or {}).get(est_name, {})
    estimator_comparison.append({"estimator": est_name, "best_loss": float(loss), "best_config": cfg})

# ---- 7. OPTIONAL enrichments ----
feature_importances = None
try:
    fi = automl.feature_importances_
    if fi is not None:
        names = list(X_train.columns)
        pairs = sorted(zip(names, fi.tolist()), key=lambda x: abs(x[1]), reverse=True)[:20]
        feature_importances = [{"feature": n, "importance": v} for n, v in pairs]
except Exception:
    pass

residual_stats = None
actual_vs_predicted = None
try:
    residuals = np.array(y_val) - np.array(y_pred_val)
    residual_stats = {
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "max_abs_residual": float(np.max(np.abs(residuals))),
        "residual_percentiles": {
            "25": float(np.percentile(residuals, 25)),
            "50": float(np.percentile(residuals, 50)),
            "75": float(np.percentile(residuals, 75)),
        },
    }
    sample_idx = np.random.choice(len(y_val), min(2000, len(y_val)), replace=False)
    actual_vs_predicted = [
        {"actual": float(y_val.iloc[i]), "predicted": float(y_pred_val[i])}
        for i in sample_idx
    ]
except Exception:
    pass

# ---- 8. Output ----
result_entry = {
    "algorithm": best_estimator or "unknown",
    "metrics": metrics,
    "best_params": best_config or {},
    "training_time": training_time,
    "trial_history": trial_history,
    "best_estimator_type": best_estimator or "unknown",
    "estimator_comparison": estimator_comparison,
    "feature_importances": feature_importances,
    "residual_stats": residual_stats,
    "actual_vs_predicted": actual_vs_predicted,
}
result = {
    "results": [result_entry],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config or {},
    "errors": [],
}
print("===RESULTS===")
print(json.dumps(result, default=str))

# ---- 9. Save model ----
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

## FORBIDDEN Patterns (Never Use)

- `from flaml.training_log import ...` -- WRONG, does not exist
- `from flaml.data import ...` -- WRONG, use `from flaml.automl.data import ...`
- `automl.model.estimator.feature_importances_` -- FRAGILE, use `automl.feature_importances_`
- `pandas.pd` -- WRONG, pandas IS pd
