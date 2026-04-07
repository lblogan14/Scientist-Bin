"""Prompt templates for the FLAML AutoML subagent.

FLAML handles model selection and hyperparameter tuning internally, so these
prompts focus on configuring ``flaml.AutoML`` correctly rather than building
sklearn pipelines manually.
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

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is (include all imports: flaml, pandas, numpy, \
sklearn.metrics, joblib, json, os, time)
2. Load training data from the TRAINING file path using pandas
3. Load validation data from the VALIDATION file path using pandas
4. Separate features (X) and target (y) for both train and val sets
5. IMPORTANT: Before passing data to FLAML, convert any pandas StringDtype or other \
extension dtypes to standard Python types. FLAML cannot handle pandas extension dtypes:
   ```
   # Convert extension dtypes to standard types for FLAML compatibility
   for col in X_train.columns:
       if pd.api.types.is_string_dtype(X_train[col]):
           X_train[col] = X_train[col].astype(str)
           X_val[col] = X_val[col].astype(str)
   if hasattr(y_train.dtype, 'name') and 'string' in str(y_train.dtype).lower():
       y_train = y_train.astype(str)
       y_val = y_val.astype(str)
   ```
6. Create a FLAML AutoML instance and call fit():
   ```
   automl = AutoML()
   automl.fit(
       X_train, y_train,
       task="classification",
       time_budget={time_budget},
       metric="{metric}",
       estimator_list={estimator_list},
       eval_method="holdout",
       X_val=X_val, y_val=y_val,
       log_file_name="flaml_log.log",
       log_training_metric=True,
       seed=42,
       verbose=0,
   )
   ```
6. Do NOT add sklearn preprocessing pipelines — FLAML handles preprocessing internally
7. After fit(), extract results:
   - automl.best_estimator (winning estimator name)
   - automl.best_config (best hyperparameters)
   - automl.best_loss (best validation loss)
   - automl.best_config_per_estimator (best config for each estimator tried)
   - automl.best_loss_per_estimator (best loss for each estimator tried)
8. Predict on validation set and compute: accuracy, f1 (weighted), precision, recall
9. Predict on training set and compute the same metrics for overfitting analysis
10. Call report_metric(name, value) for each key metric (this function is pre-defined)
11. Extract trial history from the log file using:
    ```
    from flaml.automl.data import get_output_from_log
    time_history, best_valid_loss_history, valid_loss_history, config_history, metric_history = \\
        get_output_from_log(filename="flaml_log.log", time_budget={time_budget})
    ```
12. Build trial_history list: [{{"trial_id": i, "estimator": est, "config": cfg, \
"loss": loss, "time": t}}, ...]
13. Build estimator_comparison list from best_config_per_estimator and best_loss_per_estimator: \
[{{"estimator": name, "best_loss": loss, "best_config": config}}, ...]
14. Try to extract feature_importances_ from automl.model.estimator (wrap in try/except)
15. Compute confusion matrix on validation set (wrap in try/except)
16. Print "===RESULTS===" followed by a JSON object:
    {{"results": [{{"algorithm": "<best_estimator>", "metrics": \
{{"train_accuracy": val, "val_accuracy": val, "train_f1_weighted": val, "val_f1_weighted": val, \
...}}, "best_params": {{...}}, "training_time": seconds, \
"trial_history": [...], "best_estimator_type": "...", \
"estimator_comparison": [...], "feature_importances": [...], \
"confusion_matrix": {{"labels": [...], "matrix": [[...]]}}}}], \
"best_model": "<best_estimator>", "hyperparameters": {{...}}, "errors": []}}
17. Save the best model: joblib.dump(automl.model.estimator, \
os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") + "/best_model.joblib")
18. Requirements 14-15 are OPTIONAL enrichments — wrap each in try/except so failures \
do not break the main script

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

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is (include all imports: flaml, pandas, numpy, \
sklearn.metrics, joblib, json, os, time)
2. Load training data from the TRAINING file path using pandas
3. Load validation data from the VALIDATION file path using pandas
4. Separate features (X) and target (y) for both train and val sets
5. IMPORTANT: Before passing data to FLAML, convert any pandas StringDtype or other \
extension dtypes to standard Python types. FLAML cannot handle pandas extension dtypes:
   ```
   for col in X_train.columns:
       if pd.api.types.is_string_dtype(X_train[col]):
           X_train[col] = X_train[col].astype(str)
           X_val[col] = X_val[col].astype(str)
   ```
6. Create a FLAML AutoML instance and call fit():
   ```
   automl = AutoML()
   automl.fit(
       X_train, y_train,
       task="regression",
       time_budget={time_budget},
       metric="{metric}",
       estimator_list={estimator_list},
       eval_method="holdout",
       X_val=X_val, y_val=y_val,
       log_file_name="flaml_log.log",
       log_training_metric=True,
       seed=42,
       verbose=0,
   )
   ```
6. Do NOT add sklearn preprocessing pipelines — FLAML handles preprocessing internally
7. After fit(), extract results (same as classification: best_estimator, best_config, etc.)
8. Predict on validation set and compute: r2, rmse, mae, mape (wrap mape in try/except)
9. Predict on training set and compute the same metrics for overfitting analysis
10. Call report_metric(name, value) for each key metric (this function is pre-defined)
11. Extract trial history from the log file (same pattern as classification)
12. Build trial_history and estimator_comparison lists
13. Try to extract feature_importances_ from automl.model.estimator (wrap in try/except)
14. Compute residual statistics on validation set: mean_residual, std_residual, \
max_abs_residual, residual_percentiles (25, 50, 75)
15. Compute actual_vs_predicted on validation set (subsample to max 2000 points)
16. Print "===RESULTS===" followed by a JSON object:
    {{"results": [{{"algorithm": "<best_estimator>", "metrics": \
{{"train_r2": val, "val_r2": val, "train_rmse": val, "val_rmse": val, ...}}, \
"best_params": {{...}}, "training_time": seconds, \
"trial_history": [...], "best_estimator_type": "...", \
"estimator_comparison": [...], "feature_importances": [...], \
"residual_stats": {{...}}, "actual_vs_predicted": [...]}}], \
"best_model": "<best_estimator>", "hyperparameters": {{...}}, "errors": []}}
17. Save the best model: joblib.dump(automl.model.estimator, \
os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") + "/best_model.joblib")
18. Requirements 13-15 are OPTIONAL enrichments — wrap each in try/except

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

== CRITICAL IMPORT INSTRUCTIONS ==
Use EXACTLY these imports — do NOT use any other import paths:
```python
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, \
    mean_absolute_percentage_error
from flaml import AutoML
from flaml.automl.data import get_output_from_log
import joblib, json, os, time
```
Do NOT import from flaml.data, flaml.training_log, or other wrong paths.

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is using the imports above
2. Load training data from the TRAINING file path using pandas
3. Load validation data from the VALIDATION file path using pandas
4. Prepare time series data:
   - Parse the temporal column: df["{temporal_column}"] = pd.to_datetime(df["{temporal_column}"])
   - Sort both train and val by the temporal column
   - X_train = train_df[["{temporal_column}"]]  (DataFrame with just the datetime column)
   - y_train = train_df["{target_column}"]
   - X_val = val_df[["{temporal_column}"]]
   - y_val = val_df["{target_column}"]
5. Create a FLAML AutoML instance and call fit():
   ```python
   automl = AutoML()
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
   ```
6. Predict on the validation set:
   ```python
   preds = automl.predict(X_val)
   # IMPORTANT: preds may be None if prediction fails — always check
   if preds is None:
       preds = []
   ```
7. Compute forecasting metrics (wrap each in try/except):
   - val_mape using mean_absolute_percentage_error(y_val, preds)
   - val_rmse using np.sqrt(mean_squared_error(y_val, preds))
   - val_mae using mean_absolute_error(y_val, preds)
8. Call report_metric(name, value) for each metric
9. Extract trial history from the log file:
   ```python
   try:
       time_history, best_valid_loss_history, valid_loss_history, \
           config_history, metric_history = get_output_from_log(
               filename="flaml_log.log", time_budget={time_budget})
   except Exception:
       time_history, config_history, valid_loss_history = [], {{}}, []
   ```
10. Build trial_history and estimator_comparison lists
11. Build forecast_data list from validation predictions:
    [{{"timestamp": str(ts), "actual": float(actual), "predicted": float(pred)}}, ...]
12. Print "===RESULTS===" followed by a JSON object:
    {{"results": [{{"algorithm": "<best_estimator>", "metrics": \
{{"val_mape": val, "val_rmse": val, "val_mae": val}}, \
"best_params": {{...}}, "training_time": seconds, \
"trial_history": [...], "best_estimator_type": "...", \
"estimator_comparison": [...], "forecast_data": [...]}}], \
"best_model": "<best_estimator>", "hyperparameters": {{...}}, "errors": []}}
13. Save the best model: joblib.dump(automl, \
os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") + "/best_model.joblib")

Return ONLY the Python code, no markdown fences.
"""
