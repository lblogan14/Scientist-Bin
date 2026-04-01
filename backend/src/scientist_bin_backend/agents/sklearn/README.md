# Sklearn Subagent

Scikit-learn framework subagent that iteratively generates training code, executes it in a sandbox, analyzes results, and refines the approach.

## Flow

```mermaid
graph TD
    A[START] --> B[generate_code]
    B --> C[execute_code]
    C --> D[analyze_results]
    D -->|refine / new algo / feature eng| B
    D -->|fix_error| E[error_research]
    E --> B
    D -->|accept / abort| F[finalize]
    F --> G[END]
```

The sklearn agent now receives pre-built execution plans and split data from the upstream plan and analyst agents. It focuses purely on the generate-execute-analyze iteration loop.

### Iteration Loop

After `analyze_results`, the agent decides:
- **accept** / **abort** -- finalize and produce report
- **fix_error** -- web search for error resolution, then regenerate code
- **refine_params** -- adjust hyperparameters (one at a time, IMPROVE pattern)
- **try_new_algo** -- switch algorithm family
- **feature_engineer** -- add feature transformations

Max 5 iterations by default. Deterministic budget limits (wall time, iteration count) stop runaway loops without LLM calls.

## Nodes

| Node | LLM Calls | Source | Description |
|------|-----------|--------|-------------|
| `generate_code` | 1 | `sklearn/nodes/` | Generates complete sklearn code using execution plan, split data paths, analysis report, and experiment history |
| `execute_code` | 0 | `base/nodes/` | Sandboxed subprocess execution with timeout enforcement |
| `analyze_results` | 0-1 | `base/nodes/` | Parses metrics, decides next action, writes to experiment journal |
| `error_research` | 1 (search) | `sklearn/nodes/` | Uses Google Search grounding to find solutions for execution errors |
| `finalize` | 1 | `base/nodes/` | Generates final report |

## Input (from Plan + Analyst)

- `execution_plan` -- structured plan with algorithms, preprocessing, metrics, success criteria
- `split_data_paths` -- `{"train": path, "val": path, "test": path}`
- `analysis_report` -- markdown report from the analyst agent
- `data_profile` -- structured data profile (shape, columns, dtypes, etc.)
- `problem_type` -- classification, regression, clustering, etc.

## Skills

SKILL.md files in `skills/` follow the [Anthropic Agent Skills specification](https://agentskills.io/specification). Each skill defines capabilities, algorithms, metrics, and a recommended approach for a specific problem type.

```
skills/
├── classification/SKILL.md   — Binary/multi-class classification
├── regression/SKILL.md       — Continuous numeric prediction
└── clustering/SKILL.md       — Unsupervised grouping
```

## Key Files

| File | Purpose |
|------|---------|
| `agent.py` | `SklearnAgent` class wrapping the graph |
| `graph.py` | StateGraph: `generate_code -> execute_code -> analyze_results` with iteration loop and error research side-path |
| `states.py` | `SklearnState` TypedDict (execution plan input, iteration tracking, experiment history) |
| `schemas.py` | Sklearn-specific schemas |
| `utils.py` | `strip_code_fences()` utility |
| `nodes/code_generator.py` | Code generation with retry context and experiment history |
| `nodes/error_researcher.py` | Web search for error resolution |
| `prompts/templates.py` | Code generator prompt |

## Model

Uses `gemini-3.1-pro-preview` via `get_agent_model("sklearn")` for code generation. Error research uses Google Search grounding via `search_with_gemini()`.
