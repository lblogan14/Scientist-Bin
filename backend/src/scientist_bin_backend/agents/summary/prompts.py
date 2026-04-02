"""Prompt templates for the summary agent."""

REVIEW_AND_RANK_PROMPT = """\
You are an expert data scientist reviewing a series of machine learning experiments.

Your task is to:
1. Rank ALL models from best to worst
2. Select the single best model and explain your reasoning

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

== Pre-Computed Diagnostics ==
{diagnostics_summary}

== Test Set Metrics ==
{test_metrics}

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
rewarding overfitting). Use the pre-computed diagnostics to inform your ranking:
- CV stability (low variance across folds is better)
- Overfitting risk (prefer models with small train-val gap)
- Pareto optimality (performance vs training time trade-off)

Consider the problem type when choosing which metric matters most:
- Classification: prioritize F1-score or accuracy (depending on class balance)
- Regression: prioritize RMSE or R² score
- Clustering: prioritize silhouette score or similar

After ranking, select the single best model and provide:
- The algorithm name and its best hyperparameters
- The primary metric name and value that determined the ranking
- Detailed reasoning considering: predictive performance, generalization (train-val gap),
  training efficiency, simplicity/interpretability, and robustness (CV stability)
- If two models are very close in performance, prefer the simpler one (Occam's razor)

If a run failed or produced no metrics, still include it with an explanation in the
weaknesses field.
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

== Data Profile ==
{data_profile}

== Model Rankings (from best to worst) ==
{model_rankings}

== Best Model ==
Algorithm: {best_model}
Hyperparameters: {best_hyperparameters}
Metrics: {best_metrics}
Selection reasoning: {selection_reasoning}

== Pre-Computed Diagnostics ==

CV Stability Analysis:
{cv_stability_summary}

Overfitting Analysis:
{overfit_summary}

Feature Importances:
{feature_importance_summary}

Confusion Matrix / Error Data:
{error_data_summary}

Hyperparameter Sensitivity:
{hyperparam_sensitivity_summary}

Pareto-Optimal Models (performance vs speed):
{pareto_summary}

== Test Set Metrics (held-out, unseen during training/validation) ==
{test_metrics}

== Reproducibility Context ==
Data paths: {split_data_paths}
Generated training code length: {code_length} characters

Write each section in clear, professional markdown. Use the pre-computed diagnostics
to ground your analysis in concrete numbers — do not re-compute, just interpret and
narrate.

**Executive Summary**: A 3-5 sentence TL;DR. State the objective, the best model and
its key metric, whether success criteria were met, and the main takeaway.

**Dataset Overview**: Describe the dataset — number of samples, features, target
variable, class distribution (for classification), key statistics. Base this on the
data analysis report and data profile.

**Methodology**: Cover the full pipeline:
- Problem formulation and approach
- Data preprocessing steps (scaling, encoding, imputation, etc.)
- Feature engineering (if any)
- Algorithms tried and why they were selected
- Cross-validation strategy
- Hyperparameter tuning approach

**Model Comparison Table**: Create a clean markdown table comparing all models.
Include columns for: Algorithm, Key Hyperparameters, Primary Val Metric, CV Std, \
Training Time. Keep it concise but informative.

**CV Stability Analysis**: Discuss cross-validation stability using the pre-computed
diagnostics. Which models were most consistent across folds? Which showed high
variance? What does this imply for generalization?

**Best Model Analysis**: Deep-dive into the winning model:
- Architecture and how it works (brief, intuitive explanation)
- Final hyperparameters and why they work well
- Performance breakdown across all available metrics
- Overfitting analysis (train vs validation gap, risk level)
- Where the model excels and where it struggles

**Feature Importance Analysis**: Based on the extracted feature importances:
- Which features are most predictive and why?
- Are there surprising features with high/low importance?
- Domain interpretation of the top features
- If no feature importances were extracted, note this and suggest ways to obtain them

**Hyperparameter Analysis**: Based on the hyperparameter sensitivity diagnostics:
- Which hyperparameters had the largest impact on performance?
- Optimal ranges discovered
- Interactions between hyperparameters (if observable)
- Suggestions for further tuning

**Error Analysis**: Based on confusion matrices (classification) or residual \
statistics (regression):
- Classification: which classes are most confused? Are there systematic errors?
- Regression: are residuals normally distributed? Any patterns in errors?
- If no error data was extracted, note this and suggest how to obtain it

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
- Data requirements and split strategy
- Key random seeds and configuration
- How to load and use the saved model
"""
