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

Also suggest which column is likely the target and what metrics are appropriate.
"""

CLEANING_PROMPT = """\
You are an expert data engineer. Generate a self-contained Python script that cleans \
the following dataset for machine learning.

Objective: {objective}
Problem type: {problem_type}
Data file: {data_file_path}
Output path: {output_path}

== Data Profile ==
Shape: {shape}
Columns: {columns}
Dtypes: {dtypes}
Missing value counts: {missing_counts}
Numeric columns: {numeric_columns}
Categorical columns: {categorical_columns}
Target column: {target_column}
Data quality issues: {data_quality_issues}

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

== Data Profile ==
{data_profile}

== Cleaning Summary ==
{cleaning_summary}

== Split Statistics ==
{split_summary}

Write a comprehensive but concise Markdown analysis report that includes:
1. **Dataset Overview**: Shape, columns, data types, and a brief description
2. **Data Quality Assessment**: Missing values, duplicates, outliers, class imbalance
3. **Cleaning Actions**: What was cleaned and why
4. **Train/Val/Test Split**: Split strategy, sizes, and ratios
5. **Recommendations for Modeling**: Feature importance hints, suggested algorithms, \
potential pitfalls, and preprocessing advice

Keep the report professional, factual, and actionable. Use bullet points and tables \
where appropriate. Do not include code.
"""
