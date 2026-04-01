"""Prompt templates for the scikit-learn subagent."""

CODE_GENERATOR_PROMPT = """\
You are an expert Python developer specialising in scikit-learn.

Generate a complete, self-contained Python script that trains and evaluates a model.

Objective: {objective}
Problem type: {problem_type}

== Data Profile ==
{data_profile}

== Strategy Plan ==
{strategy}

== Data File Paths (pre-split by the analyst) ==
Training data: {train_file_path}
Validation data: {val_file_path}
Test data: {test_file_path}

{analysis_context}

{retry_context}

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is (include all imports)
2. Load training data from the TRAINING file path above using pandas
3. Load validation data from the VALIDATION file path above using pandas
4. Do NOT re-split the data — the train/val/test split has already been done
5. Use sklearn Pipelines to prevent data leakage
6. Use ColumnTransformer for mixed feature types if needed
7. Fit the model on the training set
8. Evaluate on the validation set for model selection and tuning
9. Use GridSearchCV or RandomizedSearchCV with the training data for hyperparameter tuning \
(set cv=5 on the training fold)
10. Call report_metric(name, value) for each key metric (this function is pre-defined)
11. Report both training and validation metrics
12. At the end, print the marker "===RESULTS===" followed by a JSON object with this structure:
   {{"results": [{{"algorithm": "...", "metrics": {{"train_<metric>": val, "val_<metric>": val}}, \
"best_params": {{}}, "training_time": seconds}}], "best_model": "algorithm_name", \
"hyperparameters": {{}}, "errors": []}}
13. Save the best model using joblib.dump() to the path from \
os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") + "/best_model.joblib"
14. Use verbose=0 for GridSearchCV to minimize output
15. Add brief inline comments for clarity
16. Handle potential errors gracefully (e.g., convergence warnings)
17. Ensure the "hyperparameters" key in the results JSON contains the FULL set of \
best hyperparameters found by the search
18. After fitting GridSearchCV/RandomizedSearchCV, extract per-fold CV scores for the \
best estimator from cv_results_ (e.g. split0_test_score, split1_test_score, ...) and \
include them in each result entry as "cv_fold_scores": {{"<metric_name>": [fold0, fold1, ...]}}
19. Include "cv_results_top_n" in each result entry: the top-10 parameter combinations \
from cv_results_ sorted by rank_test_score, each as \
{{"params": {{...}}, "mean_score": float, "std_score": float, "rank": int}}
20. If the best estimator exposes feature_importances_ (tree-based) or coef_ (linear), \
extract the top-20 features by absolute importance and include "feature_importances": \
[{{"feature": "<name>", "importance": float}}, ...] sorted descending by importance
21. For classification problems: compute the confusion matrix on the validation set using \
sklearn.metrics.confusion_matrix and include "confusion_matrix": \
{{"labels": [<class_labels>], "matrix": [[int, ...], ...]}}
22. For regression problems: compute residual statistics (y_val - y_pred) and include \
"residual_stats": {{"mean_residual": float, "std_residual": float, \
"max_abs_residual": float, "residual_percentiles": {{"25": float, "50": float, "75": float}}}}
23. Requirements 18-22 are OPTIONAL enrichments — wrap each extraction in its own \
try/except block so that any failure does not break the main training script. \
If extraction fails, simply omit the key from the results JSON

Return ONLY the Python code, no markdown fences.
"""
