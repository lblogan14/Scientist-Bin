"""Prompt templates for the scikit-learn subagent."""

PLANNER_PROMPT = """\
You are an expert data scientist planning a scikit-learn solution.

Objective: {objective}
Data description: {data_description}

Search context (recent best practices):
{search_context}

Create a structured plan including:
1. The overall approach
2. Which sklearn algorithms to try (at least 2 for comparison)
3. Required preprocessing steps
4. Evaluation metrics appropriate for this task

Be specific and practical.
"""

CODE_GENERATOR_PROMPT = """\
You are an expert Python developer specialising in scikit-learn.

Generate a complete, self-contained Python script that implements the following plan.

Objective: {objective}
Data description: {data_description}

Plan:
{plan}

{retry_context}

Requirements:
- The script must be runnable as-is (include all imports)
- Use scikit-learn best practices (pipelines, cross-validation)
- Include proper train/test splitting
- Print evaluation metrics at the end
- Add brief inline comments for clarity

Return ONLY the Python code, no markdown fences.
"""

EVALUATOR_PROMPT = """\
You are a code reviewer specialising in machine learning with scikit-learn.

Evaluate the following code for correctness, completeness, and best practices.

Objective: {objective}

Code:
```python
{code}
```

Check for:
1. Correct imports and API usage
2. Proper data splitting (no data leakage)
3. Appropriate preprocessing in a pipeline
4. Correct metric computation
5. Code runs without errors

Provide a structured evaluation.
"""
