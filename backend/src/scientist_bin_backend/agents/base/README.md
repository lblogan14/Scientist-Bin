# Base Agent Module

Shared nodes, schemas, and state definitions for ML framework subagents.

## Purpose

Provides reusable node functions and Pydantic schemas used by the sklearn subagent (and future framework subagents). The analyst agent has its own data profiling/cleaning nodes, and the plan agent handles strategy planning.

## Shared Nodes (actively used)

| Node | File | Used By | Description |
|------|------|---------|-------------|
| `execute_code` | `nodes/code_executor.py` | Sklearn, Analyst | Sandboxed subprocess execution (0 LLM calls). Process isolation, timeout enforcement, stdout/stderr capture. |
| `analyze_results` | `nodes/results_analyzer.py` | Sklearn | Parses metrics from `===RESULTS===` output, decides next action (accept, abort, refine, new algo, feature eng, fix error), writes to experiment journal. |
| `finalize` | `nodes/results_analyzer.py` | Sklearn | Generates a final report from the best experiment run. |

## Modules

| File | Purpose |
|------|---------|
| `states.py` | `BaseMLState`, `DataProfile`, `ExperimentRecord` TypedDicts |
| `schemas.py` | `ProblemClassification`, `StrategyPlan`, `IterationDecision`, `FinalReport` |
| `nodes/code_executor.py` | `execute_code` (0 LLM calls, subprocess sandbox) |
| `nodes/results_analyzer.py` | `analyze_results`, `finalize` |
| `prompts.py` | Prompts for results analysis, reflection, final report |
