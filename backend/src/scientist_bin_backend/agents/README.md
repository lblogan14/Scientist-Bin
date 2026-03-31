# Agents

Multi-agent system with a central orchestrator and framework-specific subagents.

- `central/` — Orchestrator agent that analyzes requests, selects a framework, and delegates to subagents.
- `sklearn/` — Scikit-learn subagent that plans, generates code, and evaluates results.

## Adding a New Framework Subagent

1. Copy the `sklearn/` directory structure.
2. Implement the standard agent files (`graph.py`, `agent.py`, `states.py`, `schemas.py`, `utils.py`, `nodes/`, `prompts/`, `skills/`).
3. Register the new subagent in `central/nodes/router.py` by adding it to `SUPPORTED_FRAMEWORKS` and the conditional edges in `central/graph.py`.
