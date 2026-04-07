"""Prompt templates for the analyst agent."""

CLASSIFY_PROBLEM_PROMPT = """\
You are an expert data scientist. Analyze the following machine learning task and \
classify the problem type.

Objective: {objective}

{data_sample}

Classify this as one of:
- classification: Predicting categorical labels
- regression: Predicting continuous numeric values
- clustering: Grouping data without labels
- dimensionality_reduction: Reducing feature space
- anomaly_detection: Identifying outliers
- ts_forecast: Predicting future values in a time-ordered sequence

Also suggest which column is likely the target and what metrics are appropriate.
"""

VALIDATE_CLASSIFICATION_PROMPT = """\
You are an expert data scientist. The upstream orchestrator has pre-classified this \
ML task. Your job is to VALIDATE or CORRECT this classification using the actual data.

Objective: {objective}

== Upstream Classification ==
Task type: {upstream_task_type}
Task subtype: {upstream_task_subtype}
Key considerations: {upstream_key_considerations}
Recommended approach: {upstream_recommended_approach}
Estimated data characteristics: {upstream_data_characteristics}

== Actual Data Sample ==
{data_sample}

Analyze the actual data and determine:
1. Does the upstream classification match what the data shows?
2. If the data has a clear target column, does it match the upstream hint?
3. Are there any data characteristics the upstream missed?

Set confidence to:
- "confirmed": The upstream classification is correct and well-supported by the data.
- "refined": The upstream classification is approximately right but needs adjustment \
(e.g., they said "classification" but it is specifically binary classification, or the \
target column guess was wrong).
- "overridden": The upstream classification is wrong based on actual data evidence \
(e.g., they said "regression" but the target is clearly categorical).

If confidence is "refined" or "overridden", explain what was wrong in \
upstream_disagreement.

Also suggest appropriate evaluation metrics for the confirmed/corrected problem type.
"""

CLEANING_PROMPT = """\
You are an expert data engineer. Generate a self-contained Python script that cleans \
the following dataset for machine learning.

Objective: {objective}
Problem type: {problem_type}
Data file: {data_file_path}
Output path: {output_path}
Target framework: {selected_framework}

== Data Profile ==
Shape: {shape}
Columns: {columns}
Dtypes: {dtypes}
Missing value counts: {missing_counts}
Numeric columns: {numeric_columns}
Categorical columns: {categorical_columns}
Target column: {target_column}
Data quality issues: {data_quality_issues}

== Upstream Analysis Context ==
Key considerations: {key_considerations}
Recommended approach: {recommended_approach}
Task complexity: {complexity_estimate}

Use these considerations to guide your cleaning decisions. For example:
- If class imbalance is noted, do NOT drop minority class samples
- If high cardinality categoricals are noted, prefer frequency/target encoding over \
one-hot
- If missing data patterns are noted, consider whether missingness is informative
- If the target framework is "sklearn", ensure all features are numeric after cleaning
- If the problem_type is "ts_forecast":
  - Use forward-fill (ffill) or time-based interpolation for missing values, NOT median/mode
  - Preserve temporal ordering — do NOT shuffle or reindex
  - Do NOT drop rows with missing values — interpolate instead
  - Do NOT encode the temporal column — keep it as-is for datetime parsing
  - Only remove exact duplicates of the entire row (same timestamp + same values)

== Data Sample (first 5 rows) ==
{data_sample}

Generate a complete Python script that:
1. Imports pandas and any needed libraries (numpy, etc.)
2. Loads the CSV from the data file path
3. Handles missing values appropriately:
   - For numeric columns with few missing values: impute with median
   - For categorical columns with few missing values: impute with mode
   - For columns with >50% missing: drop the column
4. Removes duplicate rows
5. Encodes categorical columns using label encoding (save a mapping dict)
   - Do NOT encode the target column if it is categorical for classification
6. Handles any specific data quality issues noted above
7. Saves the cleaned DataFrame to the output path as CSV (index=False)
8. Prints a JSON summary to stdout with keys:
   - "rows_before": int
   - "rows_after": int
   - "columns_dropped": list[str]
   - "missing_filled": dict (column -> strategy)
   - "duplicates_removed": int
   - "encoding_applied": list[str]

IMPORTANT: The script must be fully self-contained. Only use standard library + \
pandas + numpy + scikit-learn. Print ONLY the JSON summary to stdout (no other print \
statements). Wrap the entire script in a try/except that prints a JSON error on failure.
"""

REPORT_PROMPT = """\
You are an expert data scientist writing a data analysis report.

Objective: {objective}
Problem type: {problem_type}

== Classification Validation ==
{classification_context}

== Data Profile ==
{data_profile}

== Cleaning Summary ==
{cleaning_summary}

== Split Statistics ==
{split_summary}

Write a comprehensive but concise Markdown analysis report that includes:
1. **Dataset Overview**: Shape, columns, data types, and a brief description
2. **Problem Classification**: The validated problem type and confidence level. If the \
upstream classification was refined or overridden, explain why based on data evidence.
3. **Data Quality Assessment**: Missing values, duplicates, outliers, class imbalance
4. **Cleaning Actions**: What was cleaned and why
5. **Train/Val/Test Split**: Split strategy, sizes, and ratios
6. **Recommendations for Modeling**: Feature importance hints, suggested algorithms, \
potential pitfalls, and preprocessing advice

Keep the report professional, factual, and actionable. Use bullet points and tables \
where appropriate. Do not include code.
"""
