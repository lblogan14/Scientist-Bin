# FLAML Classification Reference

## Complete Working Code Pattern

The following is a **complete, working script** for FLAML classification.
Use this as a direct template — adapt file paths and column names only.

```python
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
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
    task="classification",
    time_budget=120,
    metric="accuracy",
    estimator_list=["lgbm", "xgboost", "rf", "extra_tree", "lrl1"],
    eval_method="holdout",
    X_val=X_val, y_val=y_val,
    log_file_name="flaml_log.log",
    seed=42,
    verbose=0,
)
training_time = time.time() - start_time

# ---- 3. Extract results (EXACT attribute names) ----
best_estimator = automl.best_estimator          # str: "lgbm", "xgboost", etc.
best_config = automl.best_config                # dict of hyperparams
best_loss = automl.best_loss                    # float (1 - accuracy for accuracy metric)

# ---- 4. Predictions and metrics ----
y_pred_val = automl.predict(X_val)
y_pred_train = automl.predict(X_train)
metrics = {
    "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
    "val_accuracy": float(accuracy_score(y_val, y_pred_val)),
    "train_f1_weighted": float(f1_score(y_train, y_pred_train, average="weighted")),
    "val_f1_weighted": float(f1_score(y_val, y_pred_val, average="weighted")),
    "train_precision_weighted": float(precision_score(y_train, y_pred_train, average="weighted")),
    "val_precision_weighted": float(precision_score(y_val, y_pred_val, average="weighted")),
    "train_recall_weighted": float(recall_score(y_train, y_pred_train, average="weighted")),
    "val_recall_weighted": float(recall_score(y_val, y_pred_val, average="weighted")),
}

# ---- 5. Trial history (PRIMARY: use config_history attribute) ----
trial_history = []
for i, (est, config, ts) in automl.config_history.items():
    trial_history.append({"trial_id": int(i), "estimator": est, "config": config, "loss": 0.0, "time": float(ts)})
# SECONDARY: parse log file for loss values
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

# ---- 7. OPTIONAL enrichments (each in try/except) ----
feature_importances = None
try:
    fi = automl.feature_importances_
    if fi is not None:
        names = list(X_train.columns)
        pairs = sorted(zip(names, fi.tolist()), key=lambda x: abs(x[1]), reverse=True)[:20]
        feature_importances = [{"feature": n, "importance": v} for n, v in pairs]
except Exception:
    pass

confusion = None
try:
    labels = sorted(y_val.unique().tolist())
    cm = confusion_matrix(y_val, y_pred_val, labels=labels)
    confusion = {"labels": [str(l) for l in labels], "matrix": cm.tolist()}
except Exception:
    pass

# ---- 8. Output ----
result = {
    "results": [{
        "algorithm": best_estimator or "unknown",
        "metrics": metrics,
        "best_params": best_config or {},
        "training_time": training_time,
        "trial_history": trial_history,
        "best_estimator_type": best_estimator or "unknown",
        "estimator_comparison": estimator_comparison,
        "feature_importances": feature_importances,
        "confusion_matrix": confusion,
    }],
    "best_model": best_estimator or "unknown",
    "hyperparameters": best_config or {},
    "errors": [],
}
print("===RESULTS===")
print(json.dumps(result, default=str))

# ---- 9. Save model (save entire automl object) ----
artifacts_dir = os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".")
joblib.dump(automl, os.path.join(artifacts_dir, "best_model.joblib"))
```

## Estimator Selection

| Estimator | Best For | Notes |
|-----------|----------|-------|
| `lgbm` | General tabular | Fast, handles missing values |
| `xgboost` | Balanced performance | Good regularization |
| `rf` | Small-medium datasets | Robust |
| `extra_tree` | Fast baseline | Randomized splits |
| `lrl1` | Linear relationships | Interpretable, L1 regularization |

## Metric Selection

- **Balanced classes**: `accuracy` (default)
- **Imbalanced classes**: `macro_f1` or `roc_auc`
- **Multi-class**: `log_loss` or `macro_f1`

## FORBIDDEN Patterns (Never Use)

- `from flaml.training_log import ...` -- WRONG, does not exist
- `from flaml.data import ...` -- WRONG, use `from flaml.automl.data import ...`
- `automl.model.estimator.feature_importances_` -- FRAGILE, use `automl.feature_importances_`
- `pandas.pd` -- WRONG, pandas IS pd
