# API

FastAPI REST endpoints for the Scientist-Bin backend.

## Endpoints

- `POST /api/v1/train` — Submit a new training request (launches agent in background).
- `GET /api/v1/experiments` — List all experiments, most recent first.
- `GET /api/v1/experiments/{id}` — Get a single experiment by ID.
- `DELETE /api/v1/experiments/{id}` — Delete an experiment.
- `GET /api/v1/health` — Health check.
- `GET /` — Root endpoint with API info.

## Modules

- `routes.py` — FastAPI router with all endpoint definitions.
- `experiments.py` — Thread-safe in-memory `ExperimentStore` with CRUD operations.
