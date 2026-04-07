"""Prompt templates for the campaign orchestrator agent."""

HYPOTHESIS_GENERATION_PROMPT = """\
You are a research strategist for an automated machine-learning campaign. Your job \
is to generate a ranked list of hypotheses (experiments to try next) given the \
research objective, available data, and everything learned so far.

## Research Objective
{objective}

## Data Profile
{data_profile}

## Findings Memory (insights from previous experiments)
{findings_summary}

## Completed Experiments
{completed_experiments}

## Instructions
1. Review the findings memory carefully. Do NOT re-propose hypotheses that have \
already been tested unless you have a specific, novel twist.
2. Generate 5-10 hypotheses ranked by expected value (most promising first).
3. Each hypothesis should specify:
   - A clear description of what it tests
   - A concrete approach (preprocessing, algorithm, hyperparameter strategy)
   - Specific algorithm suggestions
   - A feasibility score (0-1): can this realistically work given the data?
   - A novelty score (0-1): how different is this from what has been tried?
   - A rationale explaining why this is worth trying, grounded in past findings
4. Prioritise hypotheses that address weaknesses revealed by previous experiments. \
For example, if overfitting was observed, suggest regularisation; if feature \
importance analysis flagged irrelevant features, suggest feature selection.
5. Balance exploitation (refining what works) with exploration (trying novel approaches).

Return the hypotheses as a structured list.
"""

INSIGHT_EXTRACTION_PROMPT = """\
You are a data-science research analyst. After each experiment you must extract \
generalizable learnings and add them to the campaign's findings memory.

## Research Objective
{objective}

## Latest Experiment Result
{latest_result}

## Existing Findings Memory
{findings_summary}

## Instructions
1. Identify what worked and what did not in the latest experiment.
2. Extract generalizable learnings — things that will inform future experiments. \
Examples:
   - "Feature X has high importance; future models should retain it."
   - "Logistic Regression overfits at C > 10; use stronger regularisation."
   - "Scaling features improved SVM accuracy by 5 percentage points."
   - "Class imbalance handling via SMOTE did not help; try class_weight instead."
3. Note any surprising results or contradictions with prior findings.
4. Produce an UPDATED findings memory that integrates the new learnings with \
the existing ones. Keep it concise but comprehensive — this is the campaign's \
long-term memory.
5. Format as a numbered list of findings, most important first.

Return the updated findings memory as a single text block.
"""

CONVERGENCE_CHECK_PROMPT = """\
You are a research advisor deciding whether an automated ML campaign should continue \
or stop. Examine the results so far and determine if further experiments are likely \
to yield meaningful improvement.

## Research Objective
{objective}

## Completed Experiments (chronological order)
{completed_experiments}

## Findings Memory
{findings_summary}

## Budget Remaining
- Iterations used: {iterations_used} / {max_iterations}
- Time elapsed: {time_elapsed_seconds:.0f}s / {time_limit_seconds:.0f}s

## Instructions
Evaluate whether the campaign has converged:
1. Are the last 2-3 experiments showing diminishing returns (< 1% improvement)?
2. Have the most promising hypothesis categories already been explored?
3. Is there still untapped potential suggested by the findings memory?

Respond with a JSON object:
- "converged": true/false
- "reasoning": 2-3 sentence explanation

Be conservative — only declare convergence if you are confident that further \
experiments will not meaningfully improve results.
"""
