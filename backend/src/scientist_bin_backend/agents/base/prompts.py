"""Prompt templates for framework-agnostic nodes.

Prompts here are used by shared base nodes (results_analyzer, test_evaluator,
finalize).  Framework-specific prompts (e.g. sklearn code generation) live in
the respective ``agents/frameworks/<name>/prompts.py``.
"""

RESULTS_ANALYZER_PROMPT = """\
You are an expert data scientist analyzing experiment results.

Objective: {objective}
Problem type: {problem_type}

Current iteration: {current_iteration} / {max_iterations}

== Latest execution results ==
{execution_summary}

== Full experiment history ==
{experiment_history}

== Success criteria ==
{success_criteria}

== Experiment journal (recent entries) ==
{journal_context}

Based on these results, decide the next action. Follow the IMPROVE pattern: \
modify only ONE component at a time for interpretable improvements.

Actions:
- "accept": Results are satisfactory. The best model meets or approaches success criteria.
- "refine_params": The best algorithm is identified but hyperparameters can be improved. \
Suggest specific parameter changes (only tune one parameter group at a time).
- "try_new_algo": Current algorithms are underperforming. Suggest ONE different algorithm \
to try, explaining why it might work better given the data characteristics.
- "fix_error": There was a code error. Provide diagnosis and fix instructions.
- "feature_engineer": Model performance is plateauing across algorithms. \
Suggest ONE specific feature transformation (polynomial, interaction, binning, etc.).
- "abort": No further improvement is likely, or budget is nearly exhausted.

Be concrete in your refinement_instructions — name the specific parameter, value, or \
feature to change. Do NOT suggest changing multiple things at once.
"""

REFLECTION_PROMPT = """\
You are reflecting on a machine learning experiment iteration to extract a useful insight.

Objective: {objective}
Iteration: {iteration}

Results from this iteration:
{results}

Decision taken: {decision}
Reasoning: {reasoning}

In 1-2 sentences, extract one actionable heuristic or lesson learned from this iteration \
that could help guide future experiments. Focus on what worked, what didn't, and why.

Examples of good heuristics:
- "For this dataset, tree-based models outperform linear models by ~10%, likely due to \
non-linear feature interactions."
- "Increasing n_estimators beyond 200 gave diminishing returns; the model plateaued."
- "StandardScaler improved SVM performance significantly but had no effect on RandomForest."

Write your heuristic:
"""

FINAL_REPORT_PROMPT = """\
You are an expert data scientist writing a final report.

Objective: {objective}
Problem type: {problem_type}

== Best model ==
Algorithm: {best_algorithm}
Metrics: {best_metrics}

== All experiments ==
{experiment_history}

== Data profile ==
{data_profile_summary}

Write a concise interpretation of the results:
1. Which model won and why it is suitable for this problem
2. Key metrics and what they mean in context
3. Any caveats or limitations
4. Recommendations for production use or further improvement
"""

TEST_EVALUATION_PROMPT = """\
You are an expert Python developer. Generate a self-contained Python script that \
evaluates a trained model on a held-out test set.

Objective: {objective}
Problem type: {problem_type}

== Best model details ==
Algorithm: {best_algorithm}
Training/validation metrics: {best_metrics}
Best hyperparameters: {best_hyperparameters}

== Data ==
Test data file: {test_file_path}

== REQUIREMENTS (MUST follow all) ==
1. The script must be runnable as-is (include all imports)
2. Load the saved model from the path in os.environ.get("SCIENTIST_BIN_ARTIFACTS_DIR", ".") \
+ "/best_model.joblib" using joblib.load()
3. Load the test data from the test file path above using pandas
4. Apply the SAME preprocessing as training — the loaded model is a sklearn Pipeline \
so calling model.predict() handles preprocessing automatically
5. Compute all relevant metrics for the problem type ({problem_type}):
   - Classification: accuracy, precision, recall, f1 (weighted), confusion matrix
   - Regression: mse, rmse, mae, r2
   - Clustering: silhouette_score, calinski_harabasz_score
6. Call report_metric(name, value) for each metric (this function is pre-defined)
7. Print "===TEST_RESULTS===" followed by a JSON object:
   {{"algorithm": "{best_algorithm}", "metrics": {{"test_<metric>": value, ...}}, \
"test_samples": N}}
8. Handle errors gracefully — if the model file doesn't exist, print an error message
9. For classification: also compute the confusion matrix on the test set using \
sklearn.metrics.confusion_matrix and include "confusion_matrix": \
{{"labels": [<class_labels>], "matrix": [[int, ...], ...]}} in the JSON
10. For regression: also compute residual statistics (y_test - y_pred) and include \
"residual_stats": {{"mean_residual": float, "std_residual": float, \
"max_abs_residual": float, "residual_percentiles": {{"25": float, "50": float, "75": float}}}}
11. Requirements 9-10 are OPTIONAL enrichments — wrap each in try/except so failures \
do not break the test evaluation script
12. For clustering: there is no target column — use ALL columns as features. \
Call model.predict(X_test) to get cluster labels, then compute \
"cluster_stats": {{"n_clusters": int, "cluster_sizes": [int, ...], \
"silhouette_score": float, "calinski_harabasz_score": float, \
"davies_bouldin_score": float}} on the test set. Include in the JSON output. \
Wrap in try/except like requirements 9-10.

Return ONLY the Python code, no markdown fences.
"""
