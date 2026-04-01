# API

FastAPI REST endpoints for the Scientist-Bin backend.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/train` | Submit a new training request (validates data file path, launches agent in background, saves artifacts on completion) |
| `GET` | `/api/v1/experiments` | List all experiments, most recent first |
| `GET` | `/api/v1/experiments/{id}` | Get a single experiment by ID |
| `GET` | `/api/v1/experiments/{id}/events` | Stream experiment events via SSE |
| `GET` | `/api/v1/experiments/{id}/journal` | Get the experiment decision journal |
| `GET` | `/api/v1/experiments/{id}/artifacts/model` | Download trained model (.joblib) |
| `GET` | `/api/v1/experiments/{id}/artifacts/results` | Download results JSON |
| `DELETE` | `/api/v1/experiments/{id}` | Delete an experiment |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/` | Root endpoint with API info |

## Data File Resolution

When `data_file_path` is provided in a train request, it is resolved in this order:

1. `backend/data/<path>` — the recommended convention
2. `backend/<path>` — backwards-compatible
3. `<project_root>/<path>`
4. The path as given (absolute or relative to CWD)

If the resolved path does not point to an existing file, the endpoint returns HTTP 400.

## Modules

- `routes.py` — FastAPI router with all endpoint definitions, SSE streaming, data file validation, and artifact download endpoints.
- `experiments.py` — Thread-safe in-memory `ExperimentStore` with `Experiment`, `Run`, and `MetricPoint` models.
