# API

FastAPI REST endpoints for the Scientist-Bin backend.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/train` | Submit a new training request (validates data file path, launches 5-agent pipeline in background, saves artifacts on completion) |
| `GET` | `/api/v1/experiments` | List all experiments, most recent first |
| `GET` | `/api/v1/experiments/{id}` | Get a single experiment by ID |
| `GET` | `/api/v1/experiments/{id}/events` | Stream experiment events via SSE |
| `GET` | `/api/v1/experiments/{id}/journal` | Get the experiment decision journal |
| `GET` | `/api/v1/experiments/{id}/plan` | Get the execution plan for an experiment |
| `GET` | `/api/v1/experiments/{id}/analysis` | Get the analyst report and split data paths |
| `GET` | `/api/v1/experiments/{id}/summary` | Get the summary report |
| `GET` | `/api/v1/experiments/{id}/artifacts/model` | Download trained model (.joblib) |
| `GET` | `/api/v1/experiments/{id}/artifacts/results` | Download results JSON |
| `DELETE` | `/api/v1/experiments/{id}` | Delete an experiment |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/` | Root endpoint with API info |

## Request Body: `POST /api/v1/train`

```json
{
  "objective": "Classify iris species",
  "data_description": "150 samples, 4 features, 3 classes",
  "data_file_path": "iris_data/Iris.csv",
  "framework_preference": "sklearn",
  "auto_approve_plan": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `objective` | `str` | (required) | What the user wants to achieve |
| `data_description` | `str` | `""` | Free-text description of the dataset |
| `data_file_path` | `str?` | `null` | Path to dataset file (resolved relative to `backend/data/`) |
| `framework_preference` | `str?` | `null` | Optional framework preference (e.g. `sklearn`) |
| `auto_approve_plan` | `bool` | `false` | Skip human-in-the-loop plan review |

## Data File Resolution

When `data_file_path` is provided in a train request, it is resolved in this order:

1. `backend/data/<path>` -- the recommended convention
2. `backend/<path>` -- backwards-compatible
3. `<project_root>/<path>`
4. The path as given (absolute or relative to CWD)

If the resolved path does not point to an existing file, the endpoint returns HTTP 400.

## Experiment Model

The `Experiment` model in `experiments.py` tracks the full pipeline state:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique experiment ID |
| `objective` | `str` | Training objective |
| `status` | `str` | `pending`, `running`, `completed`, `failed` |
| `phase` | `str?` | Current pipeline phase (see `ExperimentPhase` enum) |
| `execution_plan` | `dict?` | Structured plan from the plan agent |
| `analysis_report` | `str?` | Markdown report from the analyst agent |
| `summary_report` | `str?` | Markdown report from the summary agent |
| `split_data_paths` | `dict?` | `{"train": path, "val": path, "test": path}` |
| `runs` | `list[Run]` | Per-iteration training runs |
| `result` | `dict?` | Full result from the agent pipeline |

### Experiment Phases

`initializing` -> `planning` -> `plan_review` -> `data_analysis` -> `classify` -> `eda` -> `execution` -> `analysis` -> `summarizing` -> `done`

## Modules

- `routes.py` -- FastAPI router with all endpoint definitions, SSE streaming, data file validation, artifact download endpoints, and background training task.
- `experiments.py` -- Thread-safe `ExperimentStore` with JSON file persistence. Models: `Experiment`, `Run`, `MetricPoint`. Enums: `ExperimentStatus`, `ExperimentPhase`, `Framework`.
