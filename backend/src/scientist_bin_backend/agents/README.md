# Agents

Multi-agent system with a central orchestrator, planning agent, data analyst agent, framework-specific subagents, and a summary agent.

## Architecture

```mermaid
graph LR
    Central["Central<br/>(orchestrator)"] --> Plan["Plan<br/>(HITL)"]
    Plan --> Analyst["Analyst<br/>(data prep)"]
    Analyst --> Sklearn["Sklearn<br/>(iterative training)"]
    Sklearn --> Summary["Summary<br/>(report)"]

    style Central fill:#4a9eff,color:#fff
    style Plan fill:#ff9f43,color:#fff
    style Analyst fill:#26de81,color:#fff
    style Sklearn fill:#a55eea,color:#fff
    style Summary fill:#fd9644,color:#fff
```

```
agents/
├── base/       — Shared nodes (code_executor, results_analyzer) and schemas
├── central/    — Orchestrator: analyze -> route -> delegate to 4-agent pipeline
├── plan/       — Query rewriting, web research, execution plan generation, HITL review
├── analyst/    — Data profiling, cleaning, train/val/test splitting, analysis report
├── sklearn/    — Iterative code generation, execution, and refinement loop
└── summary/    — Experiment review, best model selection, comprehensive report
```

## Agent Pipeline

| Step | Agent | Input | Output |
|------|-------|-------|--------|
| 1 | **Central** | User objective, data file | Framework selection |
| 2 | **Plan** | Objective, data description | Execution plan (structured + markdown), HITL approval |
| 3 | **Analyst** | Objective, data file, execution plan | Data profile, cleaned CSV, train/val/test splits, analysis report |
| 4 | **Sklearn** | Execution plan, split data, analysis report | Experiment history, best run, generated code |
| 5 | **Summary** | All upstream outputs | Model rankings, best model selection, comprehensive markdown report |

## Data Flow

```mermaid
graph TD
    User["User Request"] --> Central
    Central -->|objective, framework| Plan
    Plan -->|execution_plan, plan_markdown| Analyst
    Analyst -->|split_data_paths, data_profile,<br/>analysis_report| Sklearn
    Sklearn -->|experiment_history,<br/>best_run, generated_code| Summary
    Summary -->|summary_report,<br/>best_model, best_metrics| Result["Final Result"]
```

## Per-Agent Model Assignment

| Agent | Model | Rationale |
|-------|-------|-----------|
| Central | `gemini-3-flash-preview` | Fast analysis and routing decisions |
| Plan | `gemini-3.1-pro-preview` | Detailed research, complex plan generation |
| Analyst | `gemini-3.1-pro-preview` | Data profiling, cleaning code generation |
| Sklearn | `gemini-3.1-pro-preview` | Code generation, error resolution |
| Summary | `gemini-3-flash-preview` | Experiment review, report generation |

Model assignments are defined in `utils/llm.py` via the `AGENT_MODELS` dict and accessed with `get_agent_model(agent_name)`.

## Adding a New Framework Subagent

1. Create a new directory (e.g., `pytorch/`) with the standard structure: `graph.py`, `agent.py`, `states.py`, `schemas.py`, `nodes/`, `prompts/`.
2. The agent receives `execution_plan`, `split_data_paths`, `analysis_report`, `data_profile`, and `problem_type` from the upstream plan and analyst agents.
3. Implement a training loop (generate -> execute -> analyze) using shared nodes from `base/` (`execute_code`, `analyze_results`, `finalize`).
4. Register in `central/nodes/router.py` by adding to `SUPPORTED_FRAMEWORKS` and add a delegate node in `central/graph.py`.
