# Sklearn Subagent

Scikit-learn framework subagent that classifies problems, analyzes data, plans experiments, generates training code, executes it in a sandbox, analyzes results, and iterates.

## Flow

```
START -> classify_problem -> analyze_data -> plan_strategy -> generate_code
      -> execute_code -> analyze_results -> (route) -> finalize | generate_code
```

The graph is built using `build_ml_graph()` from `agents/base/`, with sklearn-specific `plan_strategy` and `generate_code` nodes.

### Iteration Loop

After `analyze_results`, the agent decides:
- **accept** / **abort** -> finalize and produce report
- **fix_error** -> regenerate code with error context
- **refine_params** -> adjust hyperparameters (one at a time, IMPROVE pattern)
- **try_new_algo** -> switch algorithm family
- **feature_engineer** -> add feature transformations

Max 5 iterations by default. Deterministic budget limits (wall time, iteration count) stop runaway loops without LLM calls.

## Nodes

- `planner.py` — Loads matching SKILL.md, searches Google for best practices, produces a structured `SklearnStrategyPlan`.
- `code_generator.py` — Generates complete, runnable sklearn code using the data profile, strategy, and `===RESULTS===` output convention.

Base nodes (from `agents/base/`):
- `classify_problem` — 1 LLM call to determine problem type
- `analyze_data` — Deterministic EDA via subprocess (0 LLM calls)
- `execute_code` — Sandboxed subprocess execution (0 LLM calls)
- `analyze_results` — Parse metrics, decide next action, write to experiment journal
- `finalize` — Generate final report

## Skills

SKILL.md files in `skills/` follow the [Anthropic Agent Skills specification](https://agentskills.io/specification). Each skill defines capabilities, algorithms, metrics, and a recommended approach for a specific problem type.

```
skills/
├── classification/SKILL.md   — Binary/multi-class classification
├── regression/SKILL.md       — Continuous numeric prediction
└── clustering/SKILL.md       — Unsupervised grouping
```

The planner node discovers skills at startup via `discover_skills()`, matches the best skill to the detected problem type, and injects the skill's full body into the planning prompt. This guides algorithm selection, preprocessing, and evaluation strategy.

## Key Files

| File | Purpose |
|------|---------|
| `agent.py` | `SklearnAgent` class wrapping the graph |
| `graph.py` | Calls `build_ml_graph()` with sklearn-specific overrides |
| `states.py` | `SklearnState` TypedDict (extends `BaseMLState`) |
| `schemas.py` | `SklearnStrategyPlan` (extends base `StrategyPlan`) |
| `utils.py` | `strip_code_fences()` utility |
| `prompts/templates.py` | Planner, code generator, and evaluator prompts |
