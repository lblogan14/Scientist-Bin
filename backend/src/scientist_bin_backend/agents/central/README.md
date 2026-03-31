# Central Agent

Orchestrator agent that coordinates the training pipeline.

## Flow

`START → analyze → route → [framework subagent] → END`

## Nodes

- `analyzer.py` — Analyzes the training request to determine task type and data characteristics.
- `router.py` — Selects the appropriate framework subagent via structured LLM output.

## Key Files

- `states.py` — `CentralState` TypedDict with `add_messages` annotation.
- `schemas.py` — `TrainRequest`, `FrameworkSelection`, `AgentResponse` Pydantic models.
- `graph.py` — StateGraph definition and compilation.
- `agent.py` — `CentralAgent` class wrapping the graph.
