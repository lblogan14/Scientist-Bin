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

# ---------------------------------------------------------------------------
# Regression-specific code generation prompt
# ---------------------------------------------------------------------------

REGRESSION_CODE_GENERATOR_PROMPT = """\
You are an expert Python developer specialising in scikit-learn regression.

Generate a complete, self-contained Python script that trains and evaluates a regression model.

Objective: {objective}
Problem type: regression

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
(set cv=5 on the training fold, scoring="neg_mean_squared_error" or "r2")
10. Call report_metric(name, value) for each key metric (this function is pre-defined)
11. Report both training and validation metrics: R2, RMSE, MAE, MAPE
12. At the end, print the marker "===RESULTS===" followed by a JSON object with this structure:
   {{"results": [{{"algorithm": "...", "metrics": {{"train_r2": val, "val_r2": val, \
"train_rmse": val, "val_rmse": val, "train_mae": val, "val_mae": val}}, \
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
best estimator from cv_results_ and include them as \
"cv_fold_scores": {{"<metric_name>": [fold0, fold1, ...]}}
19. Include "cv_results_top_n": the top-10 parameter combinations sorted by rank, each as \
{{"params": {{...}}, "mean_score": float, "std_score": float, "rank": int}}
20. If the best estimator exposes feature_importances_ (tree-based) or coef_ (linear), \
extract the top-20 features and include "feature_importances": \
[{{"feature": "<name>", "importance": float}}, ...] sorted descending
21. Compute residual statistics (y_val - y_pred) and include "residual_stats": \
{{"mean_residual": float, "std_residual": float, "max_abs_residual": float, \
"residual_percentiles": {{"25": float, "50": float, "75": float}}}}
22. Generate actual vs predicted scatter data (subsample to max 2000 points if needed): \
"actual_vs_predicted": [{{"actual": float, "predicted": float}}, ...]
23. For linear models with coef_, extract coefficients: \
"coefficients": [{{"feature": "<name>", "coefficient": float}}, ...] sorted by abs value
24. Generate learning curve data using sklearn.model_selection.learning_curve \
with 5 training sizes (0.2, 0.4, 0.6, 0.8, 1.0): \
"learning_curve": [{{"train_size": int, "train_score": float, "val_score": float}}, ...]
25. Requirements 18-24 are OPTIONAL enrichments — wrap each in try/except. \
If extraction fails, simply omit the key from the results JSON

Return ONLY the Python code, no markdown fences.
"""

# ---------------------------------------------------------------------------
# Clustering-specific code generation prompt
# ---------------------------------------------------------------------------

CLUSTERING_CODE_GENERATOR_PROMPT = """\
You are an expert Python developer specialising in scikit-learn clustering.

Generate a complete, self-contained Python script that performs unsupervised clustering.

Objective: {objective}
Problem type: clustering

== Data Profile ==
{data_profile}

== Strategy Plan ==
{strategy}

== Data File Paths (pre-split by the analyst) ==
Training data: {train_file_path}

{analysis_context}

{retry_context}

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is (include all imports)
2. Load training data from the TRAINING file path above using pandas
3. Do NOT use any target column — this is unsupervised learning
4. Preprocess the data: handle missing values, scale numeric features using StandardScaler \
or RobustScaler, encode categorical features if needed
5. Use sklearn Pipeline with ColumnTransformer for preprocessing
6. Try the clustering algorithms specified in the strategy plan (e.g., KMeans, DBSCAN, \
AgglomerativeClustering, GaussianMixture)
7. For KMeans/GaussianMixture: run an elbow analysis testing k from 2 to 10 (or as \
specified in the plan). Compute inertia (KMeans) or BIC (GaussianMixture) for each k
8. Evaluate each algorithm using internal clustering metrics: \
silhouette_score, calinski_harabasz_score, davies_bouldin_score
9. Call report_metric(name, value) for each key metric (this function is pre-defined)
10. At the end, print the marker "===RESULTS===" followed by a JSON object:
   {{"results": [{{"algorithm": "...", "metrics": {{"silhouette_score": val, \
"calinski_harabasz": val, "davies_bouldin": val}}, "n_clusters": N, \
"best_params": {{}}, "training_time": seconds}}], \
"best_model": "algorithm_name", "hyperparameters": {{}}, "errors": []}}
11. Save the best model using joblib.dump() to the path from \
os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") + "/best_model.joblib"
12. Add brief inline comments for clarity
13. Handle potential errors gracefully
14. Generate PCA 2D projection of the data and cluster assignments for visualization. \
Subsample to max 2000 points if dataset is large. Include in each result entry: \
"cluster_scatter": [{{"x": float, "y": float, "cluster": int}}, ...]
15. Include cluster sizes in each result entry: \
"cluster_sizes": [count_cluster_0, count_cluster_1, ...]
16. For KMeans: include elbow curve data: \
"elbow_data": [{{"k": int, "inertia": float}}, ...]
17. Compute per-sample silhouette scores and include (subsample to max 2000): \
"silhouette_per_sample": [{{"sample_index": int, "score": float, "cluster": int}}, ...]
18. Compute cluster centroids in original feature space (inverse-transform if scaled) \
and include: "cluster_profiles": [{{"cluster_id": int, "size": int, \
"centroid": {{"feature1": float, "feature2": float, ...}}}}, ...]
19. Requirements 14-18 are OPTIONAL enrichments — wrap each in try/except. \
If extraction fails, simply omit the key from the results JSON

Return ONLY the Python code, no markdown fences.
"""
