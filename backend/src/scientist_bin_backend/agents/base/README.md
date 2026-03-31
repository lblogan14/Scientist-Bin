# Base Agent Module

Reusable graph topology and shared infrastructure for all ML framework subagents.

## Purpose

Separates the **graph topology** (same for all ML frameworks) from **framework-specific logic** (differs per framework). A new framework subagent only needs to implement two functions (`plan_strategy`, `generate_code`) and gets the full 7-node pipeline for free.

## Graph Topology

```
classify_problem -> analyze_data -> plan_strategy* -> generate_code*
    -> execute_code -> analyze_results -> (route) -> finalize | generate_code
```

`*` = Framework-specific (provided by subagent)

## Modules

| File | Purpose |
|------|---------|
| `graph.py` | `build_ml_graph()` factory function |
| `states.py` | `BaseMLState`, `DataProfile`, `ExperimentRecord` TypedDicts |
| `schemas.py` | `ProblemClassification`, `StrategyPlan`, `IterationDecision`, `FinalReport` |
| `nodes/data_analyzer.py` | `classify_problem` (1 LLM call), `analyze_data` (0 LLM calls) |
| `nodes/code_executor.py` | `execute_code` (0 LLM calls, subprocess sandbox) |
| `nodes/results_analyzer.py` | `analyze_results`, `route_decision`, `finalize` |
| `prompts/templates.py` | Prompts for classification, results analysis, reflection, final report |
