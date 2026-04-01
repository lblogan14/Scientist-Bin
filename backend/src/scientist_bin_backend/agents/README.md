# Agents

Multi-agent system with a central orchestrator, a reusable base module, and framework-specific subagents.

## Architecture

```
agents/
├── base/       — Reusable graph topology and shared nodes for all ML frameworks
├── central/    — Orchestrator that analyzes requests, selects a framework, delegates
└── sklearn/    — Scikit-learn subagent (classification, regression, clustering)
```

- **`base/`** provides `build_ml_graph()`, a factory that assembles the standard 7-node pipeline (classify -> EDA -> plan -> generate -> execute -> analyze -> finalize). Framework subagents supply two functions (`plan_strategy`, `generate_code`) and get the full pipeline for free.
- **`central/`** analyzes user requests, routes to the appropriate framework subagent.
- **`sklearn/`** implements sklearn-specific planning and code generation, with SKILL.md files guiding algorithm selection per problem type.

## Adding a New Framework Subagent

1. Create a new directory (e.g., `pytorch/`) with the standard structure.
2. Implement `plan_strategy()` and `generate_code()` node functions.
3. Create a `states.py` that mirrors `SklearnState` with any framework-specific fields.
4. Call `build_ml_graph(plan_strategy_fn=..., generate_code_fn=..., state_schema=...)` in your `graph.py`.
5. Add SKILL.md files under `skills/` for each problem type.
6. Register in `central/nodes/router.py` by adding to `SUPPORTED_FRAMEWORKS` and the conditional edges in `central/graph.py`.
