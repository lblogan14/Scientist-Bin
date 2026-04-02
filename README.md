# Scientist-Bin

A multi-agent system that automatically trains and evaluates data science models. Describe your objective in plain language, upload a dataset, and the system handles everything from data profiling to model selection.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration and [Google Gemini](https://ai.google.dev/) as the LLM backbone.

## How It Works

Scientist-Bin runs a **5-agent pipeline** that takes a natural-language objective and a dataset, then produces a trained model, evaluation metrics, and a comprehensive report.

```
Central ──> Analyst ──> Plan (HITL) ──> Sklearn ──> Summary
```

| Agent | Role | Model Tier |
|-------|------|------------|
| **Central** | Analyze the request, classify the task, route to the right framework | Flash |
| **Analyst** | Profile the dataset, clean/preprocess, split into train/val/test | Pro |
| **Plan** | Search best practices online, create an execution plan, get human approval | Pro |
| **Sklearn** | Generate scikit-learn code, execute, iteratively refine, evaluate on test set | Pro |
| **Summary** | Review all runs, pick the best model, generate a final report with charts | Flash |

The **Plan** agent includes a human-in-the-loop step -- you can approve the plan, request changes, or let it auto-approve.

**Currently supports scikit-learn.** PyTorch, TensorFlow, Hugging Face Transformers, and Diffusers are planned.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) 10+ (Node package manager)
- A [Google AI API key](https://aistudio.google.com/apikey)

### 1. Clone and configure

```bash
git clone https://github.com/Scientist-Bin/Scientist-Bin.git
cd Scientist-Bin
```

Create `backend/.env` from the example:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set your API key:

```
GOOGLE_API_KEY=your-api-key-here
```

### 2. Install dependencies

```bash
# Backend
cd backend
uv sync --all-groups

# Frontend
cd ../frontend
pnpm install
```

### 3. Run

**Option A: Full stack (web UI)**

```bash
# Terminal 1 -- backend API server
cd backend
uv run scientist-bin serve

# Terminal 2 -- frontend dev server
cd frontend
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173). The frontend proxies API calls to the backend at port 8000.

**Option B: CLI only (no server required)**

```bash
cd backend
uv run scientist-bin train "Classify iris species" \
  --data-file data/iris_data/Iris.csv \
  --auto-approve
```

## CLI Reference

The `scientist-bin` CLI supports both local execution (no server) and remote commands (against a running server).

### Local Commands

```bash
# Full pipeline
uv run scientist-bin train "Classify iris species" --data-file data/iris_data/Iris.csv
uv run scientist-bin train "Classify iris" --data-file data/iris_data/Iris.csv --auto-approve
uv run scientist-bin train "Classify iris" --data "4 features, 3 classes" --quiet

# Individual agents
uv run scientist-bin analyze data/iris_data/Iris.csv --objective "Classify iris"
uv run scientist-bin plan "Classify iris" --data-file data/iris_data/Iris.csv --run-analyst
uv run scientist-bin train-sklearn "Classify iris" --data-dir outputs/runs/<id>/data/ --problem-type classification
uv run scientist-bin summarize <experiment-id>
```

### Remote Commands (requires running server)

```bash
uv run scientist-bin train-remote "Classify iris" --auto-approve   # Submit + stream
uv run scientist-bin watch <experiment-id>                          # Stream events
uv run scientist-bin review <experiment-id> "approve"               # Approve plan
uv run scientist-bin review <experiment-id> "Try XGBoost instead"   # Request revision
uv run scientist-bin download <experiment-id> model -o model.joblib # Download model
uv run scientist-bin download <experiment-id> all                   # Download all artifacts
uv run scientist-bin list --status completed --framework sklearn    # Filter experiments
uv run scientist-bin show <experiment-id>                           # Experiment details
uv run scientist-bin delete <experiment-id>                         # Delete experiment
```

## Output Artifacts

After training, artifacts are saved under `backend/outputs/`:

```
outputs/
├── models/<id>.joblib              # Best trained model
├── results/<id>.json               # Full result data
├── results/<id>_analysis.md        # Data analysis report
├── results/<id>_summary.md         # Summary report
├── results/<id>_plan.json          # Execution plan
├── results/<id>_charts.json        # Structured chart data
└── logs/<id>.jsonl                 # Decision journal
```

## Frontend

The web UI provides five pages for managing the full experiment lifecycle:

| Page | Description |
|------|-------------|
| **Dashboard** | Submit objectives, view stats, see active experiments |
| **Experiments** | Browse, filter, and inspect past experiments |
| **Training Monitor** | Real-time progress (10-phase pipeline), plan review, agent activity log, metrics stream |
| **Results** | 13-tab deep-dive: overview, confusion matrix, CV stability, overfitting, feature importance, hyperparameters, plan, analysis, summary, code, data, journal |
| **Model Selection** | Rank models, compare metrics, tradeoff scatter plots |

Real-time updates are streamed via Server-Sent Events (SSE). Three color themes are available: light, dark, and science.

## API

The backend exposes a REST API at `http://localhost:8000/api/v1/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/train` | Start a new experiment |
| `GET` | `/experiments` | List experiments (with filtering) |
| `GET` | `/experiments/{id}` | Get experiment details |
| `GET` | `/experiments/{id}/events` | SSE event stream |
| `POST` | `/experiments/{id}/review` | Submit plan review (HITL) |
| `GET` | `/experiments/{id}/journal` | Get decision journal |
| `GET` | `/experiments/{id}/plan` | Get execution plan |
| `GET` | `/experiments/{id}/analysis` | Get analysis report |
| `GET` | `/experiments/{id}/summary` | Get summary report |
| `GET` | `/experiments/{id}/artifacts/{type}` | Download artifact |
| `DELETE` | `/experiments/{id}` | Delete experiment |
| `GET` | `/health` | Health check |

## Project Structure

```
Scientist-Bin/
├── backend/
│   ├── src/scientist_bin_backend/
│   │   ├── agents/
│   │   │   ├── base/            # Shared framework agent infrastructure
│   │   │   ├── central/         # Request analysis + routing
│   │   │   ├── analyst/         # Data profiling, cleaning, splitting
│   │   │   ├── plan/            # Online search, plan creation, HITL
│   │   │   ├── frameworks/
│   │   │   │   └── sklearn/     # Scikit-learn code gen + execution
│   │   │   └── summary/         # Best model selection + report
│   │   ├── api/                 # FastAPI routes + experiment store
│   │   ├── config/              # Pydantic Settings (env-based)
│   │   ├── events/              # Event bus for real-time updates
│   │   ├── execution/           # Sandboxed code runner, budgets, journal
│   │   ├── utils/               # LLM helpers, artifacts, naming
│   │   ├── main.py              # FastAPI app entry point
│   │   └── cli.py               # Typer CLI entry point
│   ├── tests/
│   ├── data/                    # Input datasets
│   └── outputs/                 # Generated models, results, logs
├── frontend/
│   ├── src/
│   │   ├── app/                 # Router, providers, layout
│   │   ├── features/            # Feature modules (1 per page)
│   │   ├── components/          # Shared UI, charts, layout
│   │   ├── lib/                 # API client, utilities
│   │   ├── stores/              # Zustand state
│   │   └── types/               # TypeScript interfaces
│   └── ...
└── .github/workflows/ci.yml    # CI: lint + test + build
```

## Tech Stack

### Backend

- **Python 3.11+** with **FastAPI** and **LangGraph**
- **Google Gemini** via `langchain-google-genai` and `google-genai`
- **Pydantic** for schemas and settings
- **Typer** for CLI
- **pandas**, **scikit-learn**, **matplotlib** for data science execution
- **uv** for package management
- **ruff** for linting/formatting, **pytest** for testing

### Frontend

- **React 19** with **TypeScript 5.9** (strict mode)
- **Vite 8** for build tooling
- **shadcn/ui** (Radix + Tailwind CSS v4)
- **React Router v7** for routing
- **TanStack React Query** for server state
- **Zustand** for client state
- **Recharts** for visualizations
- **ky** for HTTP, **react-hook-form** + **Zod** for forms
- **pnpm** for package management
- **Vitest** + **Testing Library** for testing

## Configuration

All environment variables go in `backend/.env`. See `backend/.env.example` for defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | *(required)* | Google AI API key |
| `SCIENTIST_BIN_GEMINI_MODEL` | `gemini-2.0-flash` | Default Gemini model |
| `SCIENTIST_BIN_GEMINI_MODEL_FLASH` | `gemini-3-flash-preview` | Flash tier (Central, Summary) |
| `SCIENTIST_BIN_GEMINI_MODEL_PRO` | `gemini-3.1-pro-preview` | Pro tier (Analyst, Plan, Sklearn) |
| `SCIENTIST_BIN_DEBUG` | `false` | Enable debug logging |
| `SCIENTIST_BIN_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `SCIENTIST_BIN_SANDBOX_TIMEOUT` | `300` | Code execution timeout (seconds) |
| `SCIENTIST_BIN_MAX_ITERATIONS` | `5` | Max refinement iterations |

## Development

```bash
# Backend (from backend/)
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run pytest -v                 # Test

# Frontend (from frontend/)
pnpm lint                        # ESLint
pnpm format                      # Prettier
pnpm test                        # Vitest
pnpm build                       # Type-check + production build
```

## Adding a New Framework

The system is designed to be extensible. To add a new ML framework (e.g., PyTorch):

1. Create `backend/src/scientist_bin_backend/agents/frameworks/pytorch/`
2. Extend `BaseFrameworkAgent` and implement `_build_graph()`
3. Add framework-specific prompts, schemas, and state
4. Register in `FRAMEWORK_REGISTRY` (`agents/central/nodes/router.py`)
5. Add a model entry to `AGENT_MODELS` (`utils/llm.py`)

The routing infrastructure will automatically discover and delegate to the new agent.

## CI

GitHub Actions runs on push/PR to `main` and `develop`:

- **Backend:** ruff lint + pytest
- **Frontend:** ESLint + TypeScript check + Vitest + production build
