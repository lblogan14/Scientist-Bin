# Central Agent

Orchestrator agent that coordinates the training pipeline.

## Flow

`START -> analyze -> route -> [framework subagent] -> END`

## Nodes

- `analyzer.py` — Analyzes the training request to determine task type and data characteristics.
- `router.py` — Selects the appropriate framework subagent via structured LLM output.

## Key Files

| File | Purpose |
|------|---------|
| `states.py` | `CentralState` TypedDict with `data_file_path` support |
| `schemas.py` | `TrainRequest`, `FrameworkSelection`, `AgentResponse` |
| `graph.py` | StateGraph definition with `_sklearn_delegate` |
| `agent.py` | `CentralAgent` class wrapping the graph |
