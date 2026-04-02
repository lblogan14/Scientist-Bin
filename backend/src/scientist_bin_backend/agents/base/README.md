# Base Agent Module

Shared infrastructure for all ML framework subagents: base class, graph builder, nodes, schemas, state, prompts, and utilities.

## Purpose

Provides the `BaseFrameworkAgent` abstract class, `build_framework_graph()` graph builder, and reusable node functions used by framework subagents under `agents/frameworks/` (sklearn, and future pytorch, huggingface, etc.). The base module eliminates duplication across frameworks by sharing the iteration loop, execution, analysis, validation, and test evaluation logic.

## Architecture

Framework agents extend `BaseFrameworkAgent` and call `build_framework_graph()` with their framework-specific `generate_code` and `error_research` nodes. The base handles everything else.

```
START -> generate_code -> validate_code -> execute_code -> analyze_results
              ^                                                |
              |--- (refine/new_algo/feature_eng) --------------|
              |--- (fix_error) -> error_research --------------|
                                                               |
              (accept/abort) -> evaluate_on_test -> finalize -> END
```

## Shared Nodes

| Node | File | LLM Calls | Description |
|------|------|-----------|-------------|
| `validate_code` | `nodes/code_validator.py` | 0 | Static analysis: syntax check, import check, results marker, report_metric call. Max 2 retries. |
| `execute_code` | `nodes/code_executor.py` | 0 | Sandboxed subprocess execution with dynamic timeout, metrics streaming, journal logging. |
| `analyze_results` | `nodes/results_analyzer.py` | 0-2 | Parses metrics, decides next action (IMPROVE pattern), structured reflection (ERL). Uses `get_agent_model(fw)` for per-framework model selection. |
| `evaluate_on_test` | `nodes/test_evaluator.py` | 1 | Evaluates best model on held-out test set after iteration loop accepts. |
| `finalize` | `nodes/results_analyzer.py` | 1 | Generates final structured report from best experiment. Uses `get_agent_model(fw)` for per-framework model selection. |

## Modules

| File | Purpose |
|------|---------|
| `agent.py` | `BaseFrameworkAgent` ABC with shared `run()` interface |
| `graph.py` | `build_framework_graph()` shared graph builder, `_route_decision`, `_route_validation` |
| `states.py` | `BaseMLState` (incl. `framework_name: str \| None`), `DataProfile`, `ExperimentRecord` TypedDicts |
| `schemas.py` | `ProblemClassification`, `StrategyPlan`, `IterationDecision`, `FinalReport` |
| `prompts.py` | Prompts for results analysis, reflection, final report, test evaluation |
| `utils.py` | `strip_code_fences()` utility for cleaning LLM code output |
| `nodes/code_validator.py` | `validate_code` node + individual check functions |
| `nodes/code_executor.py` | `execute_code` node (0 LLM calls, subprocess sandbox) |
| `nodes/results_analyzer.py` | `analyze_results`, `finalize` nodes |
| `nodes/test_evaluator.py` | `evaluate_on_test` node + `_parse_test_results` helper |
