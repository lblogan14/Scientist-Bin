"""Prompt templates for the summary agent."""

EXPERIMENT_REVIEW_PROMPT = """\
You are an expert data scientist reviewing a series of machine learning experiments.

Your task is to analyze the experiment history and produce a ranked list of all models
that were trained, from best to worst.

== Objective ==
{objective}

== Problem Type ==
{problem_type}

== Execution Plan ==
{execution_plan}

== Data Analysis Report ==
{analysis_report}

== Experiment History ==
{experiment_history}

== Run Details ==
{runs}

For each model in the experiment history, provide:
1. A rank (1 = best overall model)
2. The algorithm name
3. The hyperparameters used
4. Training metrics (metrics computed on the training set, if available)
5. Validation metrics (cross-validation or validation-set metrics)
6. Test metrics (if available — only the final/best model typically gets test evaluation)
7. Training time in seconds
8. Key strengths (e.g., high accuracy, fast training, good generalization)
9. Key weaknesses (e.g., overfitting, slow training, poor on minority classes)

Rank models primarily by their validation metrics (not training metrics, to avoid
rewarding overfitting). Consider the problem type when choosing which metric matters
most:
- Classification: prioritize F1-score or accuracy (depending on class balance)
- Regression: prioritize RMSE or R² score
- Clustering: prioritize silhouette score or similar

If a run failed or produced no metrics, still include it with an explanation in the
weaknesses field.

Be thorough and objective in your analysis.
"""

MODEL_SELECTION_PROMPT = """\
You are an expert data scientist selecting the best model from a ranked comparison.

== Objective ==
{objective}

== Problem Type ==
{problem_type}

== Model Rankings ==
{model_comparison}

Based on the ranked model comparison above, select the single best model.

Provide:
1. The algorithm name
2. Its best hyperparameters
3. The primary metric name and value that determined the ranking
4. Detailed reasoning for why this model is the best choice, considering:
   - Predictive performance (validation and test metrics)
   - Generalization (gap between training and validation performance)
   - Training efficiency (time and resource usage)
   - Simplicity and interpretability (prefer simpler models when performance is similar)
   - Robustness (consistency across folds or evaluation runs)

If two models are very close in performance, prefer the simpler one (Occam's razor).
"""

REPORT_GENERATION_PROMPT = """\
You are an expert data scientist writing a comprehensive experiment report.

Generate a professional-quality report that a data scientist or ML engineer would
find valuable for understanding the experiment results, making deployment decisions,
and reproducing the work.

== Objective ==
{objective}

== Problem Type ==
{problem_type}

== Execution Plan ==
{execution_plan}

== Data Analysis Report ==
{analysis_report}

== Model Comparison (ranked) ==
{model_comparison}

== Best Model ==
Algorithm: {best_model}
Hyperparameters: {best_hyperparameters}
Metrics: {best_metrics}

== Full Sklearn Results ==
{sklearn_results}

Write each section in clear, professional markdown:

**Title**: A descriptive title for this experiment report.

**Dataset Overview**: Describe the dataset — number of samples, features, target
variable, class distribution (for classification), key statistics. Base this on the
data analysis report.

**Methodology**: Cover the full pipeline:
- Problem formulation and approach
- Data preprocessing steps (scaling, encoding, imputation, etc.)
- Feature engineering (if any)
- Algorithms tried and why they were selected
- Cross-validation strategy
- Hyperparameter tuning approach

**Model Comparison Table**: Create a clean markdown table comparing all models.
Include columns for: Algorithm, Key Hyperparameters, Validation Metric, Training Time.
Keep it concise but informative.

**Best Model Analysis**: Deep-dive into the winning model:
- Architecture and how it works (brief, intuitive explanation)
- Final hyperparameters and why they work well
- Performance breakdown across all available metrics
- Analysis of generalization (train vs. validation gap)
- Where the model excels and where it struggles

**Hyperparameter Analysis**: Discuss what was learned about hyperparameter sensitivity:
- Which hyperparameters had the largest impact on performance
- Optimal ranges discovered
- Interactions between hyperparameters (if observable)
- Suggestions for further tuning

**Conclusions**: Summarize the key findings:
- Was the objective achieved?
- Which approach worked best and why?
- Key insights about the dataset and problem

**Recommendations**: Provide 3-6 actionable next steps:
- Model improvements to try
- Data collection suggestions
- Deployment considerations
- Monitoring recommendations

**Reproducibility Notes**: Explain how to reproduce the results:
- Required packages and versions
- Data requirements
- Key random seeds and configuration
- How to load and use the saved model
"""
