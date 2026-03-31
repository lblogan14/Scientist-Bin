# Sklearn Subagent

Scikit-learn framework subagent that plans an approach, generates training code, and evaluates it.

## Flow

`START → plan → generate_code → evaluate → [retry generate_code | END]`

The evaluate node checks code quality. If the evaluation fails and retries remain, it loops back to `generate_code` with feedback. Maximum 3 retries.

## Nodes

- `planner.py` — Searches for best practices via Google Search grounding, then produces a structured plan.
- `code_generator.py` — Generates complete, runnable sklearn code from the plan.
- `evaluator.py` — Reviews generated code for correctness and completeness.

## Skills

SKILL.md files in `skills/` define modular capabilities (e.g., classification, regression).
