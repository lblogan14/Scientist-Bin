# Scientist-Bin Backend

Multi-agent system for automated data science model training and evaluation. Built with Python, LangGraph, FastAPI, and Google Gemini.

## Quick Start

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
# Windows
start.bat

# Linux / macOS
./start.sh
```

Or manually:

```bash
cp .env.example .env          # Edit .env and set GOOGLE_API_KEY
uv sync --all-groups          # Install all dependencies
uv run uvicorn scientist_bin_backend.main:app --reload  # Start dev server
```

The API runs at `http://localhost:8000`. Docs at `/docs`, health check at `/api/v1/health`.

## Architecture

```
Central Agent (orchestrator)
  |
  +-- analyze (determine task type)
  +-- route (select framework)
  +-- delegate to framework subagent
        |
        Sklearn Subagent (7-node pipeline)
          |
          classify_problem  (1 LLM call — detect problem type)
          analyze_data      (0 LLM calls — deterministic EDA via subprocess)
          plan_strategy     (1-2 LLM calls — loads SKILL.md, Google Search, structured plan)
          generate_code     (1 LLM call — complete sklearn training script)
          execute_code      (0 LLM calls — sandboxed subprocess, real metrics)
          analyze_results   (0-1 LLM calls — parse metrics, decide next action)
          finalize          (1 LLM call — final report)
```

The agent iterates (generate -> execute -> analyze) up to 5 times, modifying one component per iteration (IMPROVE pattern). Iteration stops when metrics meet success criteria or budget is exhausted.

## Project Structure

```
backend/
├── start.bat / start.sh           # Startup scripts
├── pyproject.toml                 # Dependencies, build config
├── .env.example                   # Environment template
├── data/                          # Input datasets
│   └── iris_data/Iris.csv         # Example dataset (150 rows, 3 classes)
├── outputs/                       # Agent-generated output (git-ignored)
│   ├── models/                    # Best model per experiment (<id>.joblib)
│   ├── results/                   # Result JSON per experiment (<id>.json)
│   ├── logs/                      # Decision journal per experiment (<id>.jsonl)
│   └── runs/                      # Raw per-run execution artifacts (scripts, stdout, stderr)
├── src/scientist_bin_backend/     # Main package
│   ├── agents/
│   │   ├── base/                  # Reusable graph topology (build_ml_graph factory)
│   │   ├── central/               # Orchestrator (analyze -> route -> delegate)
│   │   └── sklearn/               # Sklearn subagent + SKILL.md skills
│   ├── execution/                 # Sandboxed code runner, budget, journal, estimator
│   ├── events/                    # SSE event bus for real-time streaming
│   ├── api/                       # FastAPI routes + experiment store
│   ├── config/                    # Pydantic settings
│   └── utils/                     # LLM helpers, SKILL.md loader
└── tests/                         # 92 tests (pytest)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/train` | Submit training request (runs agent in background) |
| `GET` | `/api/v1/experiments` | List all experiments |
| `GET` | `/api/v1/experiments/{id}` | Get experiment details |
| `GET` | `/api/v1/experiments/{id}/events` | SSE stream of real-time events |
| `GET` | `/api/v1/experiments/{id}/journal` | Agent decision journal |
| `DELETE` | `/api/v1/experiments/{id}` | Delete experiment |
| `GET` | `/api/v1/health` | Health check |

## CLI

```bash
uv run scientist-bin serve                                              # Start server
uv run scientist-bin train "Classify iris" --data-file data/iris_data/Iris.csv  # Train locally
uv run scientist-bin train "Classify iris" --data-file data/iris_data/Iris.csv -q  # JSON only
uv run scientist-bin train-remote "Classify iris"                       # Submit to server
uv run scientist-bin list                                               # List experiments
uv run scientist-bin show <id> --json                                   # Show experiment
uv run scientist-bin delete <id>                                        # Delete experiment
```

The `train` command prints real-time progress as the agent runs:

```
  Scientist-Bin  |  Training Agent
  Experiment: 42ab3ddd43e8
  Objective:  Classify iris species
  Data file:  C:\...\data\iris_data\Iris.csv

  [classify] Classified as classification
  [eda] Shape: 150 rows x 6 columns ...
  [planning] A comprehensive classification workflow ...
  [iter 0] generate_code
  [run] Started (timeout: 60s, estimated: 10s)
  [run] completed in 3.6s
  [iter 1] analyze_results -> accept
  [done] Best model: LogisticRegression (accuracy=1.0000)

  [saved] Results  -> ...\outputs\results\42ab3ddd43e8.json
  [saved] Model    -> ...\outputs\models\42ab3ddd43e8.joblib
  [saved] Journal  -> ...\outputs\logs\42ab3ddd43e8.jsonl
```

Use `--quiet` / `-q` to suppress progress output and emit only the final JSON result. Data file paths (`--data-file`) are resolved to absolute and validated before the agent starts. The `.env` file is always loaded from `backend/` regardless of the current working directory.

## Key Design Decisions

- **Real code execution**: Generated code runs in sandboxed subprocesses (not `exec()`). Process isolation, timeout enforcement, stdout/stderr capture.
- **Token efficiency**: LLM is only called at decision points (3-5 calls per iteration). Zero tokens during code execution.
- **SKILL.md integration**: Skills follow the [Anthropic Agent Skills spec](https://agentskills.io/specification). The planner loads the matching skill and injects its body into the prompt.
- **Experiment journal**: Append-only JSONL log per experiment captures decisions, reflections, and heuristics (ERL pattern).
- **Duration estimation**: Predicts training time from dataset size and adjusts subprocess timeout dynamically.
- **Reusable template**: `build_ml_graph()` factory lets new framework subagents provide just 2 functions (`plan_strategy`, `generate_code`) to get the full pipeline.

## Development

```bash
uv run pytest -v              # Run all tests (92 tests)
uv run pytest -k "iris"       # Integration tests with real data
uv run ruff check .           # Lint
uv run ruff format .          # Format
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google Gemini API key |
| `SCIENTIST_BIN_GEMINI_MODEL` | `gemini-3-flash` | Gemini model |
| `SCIENTIST_BIN_DEBUG` | `false` | Debug mode |
| `SCIENTIST_BIN_CORS_ORIGINS` | `["http://localhost:5173"]` | CORS origins |
| `SCIENTIST_BIN_SANDBOX_TIMEOUT` | `300` | Seconds per code execution |
| `SCIENTIST_BIN_MAX_ITERATIONS` | `5` | Max iteration cycles |

## Adding a New Framework Subagent

1. Create `agents/myframework/` with `graph.py`, `agent.py`, `states.py`, `schemas.py`, `nodes/`, `prompts/`, `skills/`
2. Implement `plan_strategy()` and `generate_code()` functions
3. Call `build_ml_graph(plan_strategy_fn=..., generate_code_fn=..., state_schema=...)`
4. Add SKILL.md files under `skills/` per problem type
5. Register in `agents/central/nodes/router.py` (`SUPPORTED_FRAMEWORKS`) and `agents/central/graph.py`
