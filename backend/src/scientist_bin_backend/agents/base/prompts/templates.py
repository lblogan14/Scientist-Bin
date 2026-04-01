"""Prompt templates for framework-agnostic nodes."""

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
