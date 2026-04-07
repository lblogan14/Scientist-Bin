# Deploy Module

Generates Docker inference containers from trained experiment models. Produces all necessary artifacts (Dockerfile, serve.py, requirements.txt, metadata.json) and optionally builds and pushes Docker images.

## CLI Usage

```bash
# Generate artifacts + build Docker image
uv run scientist-bin deploy <experiment-id>

# Generate artifacts only (no Docker build)
uv run scientist-bin deploy <experiment-id> --no-build

# Custom output directory
uv run scientist-bin deploy <experiment-id> --output-dir ./my-deploy/

# Custom image tag
uv run scientist-bin deploy <experiment-id> --tag my-registry/my-model:v1

# Build and push to registry
uv run scientist-bin deploy <experiment-id> --push
```

## How It Works

1. **Locate artifacts** -- finds `outputs/models/{id}.joblib` and `outputs/results/{id}.json`
2. **Build metadata** -- extracts algorithm, problem type, framework, hyperparameters, test metrics, and feature columns from the result JSON
3. **Generate files** -- writes Dockerfile, serve.py, requirements.txt, and metadata.json to `outputs/deploy/{id}/`. Package versions in requirements.txt are resolved from the framework venv if provisioned, falling back to the core venv
4. **Copy model** -- copies the trained `.joblib` model into the deploy directory
5. **Build image** (optional) -- runs `docker build` to create the container image
6. **Push image** (optional) -- runs `docker push` to a registry

## Generated Artifacts

| File | Purpose |
|------|---------|
| `Dockerfile` | Python 3.11-slim base, installs deps, copies model + server, exposes port 8080, runs uvicorn |
| `serve.py` | FastAPI inference server with `/predict`, `/health`, `/info` endpoints |
| `requirements.txt` | Pinned versions of scikit-learn, pandas, numpy, joblib, fastapi, uvicorn |
| `metadata.json` | Experiment metadata (algorithm, problem type, hyperparameters, test metrics, feature columns) |
| `model.joblib` | Copy of the trained model |

## Docker Image Structure

```
/app/
├── model.joblib         — Trained sklearn model
├── metadata.json        — Experiment metadata
├── serve.py             — FastAPI inference server
└── requirements.txt     — Python dependencies
```

- **Base image**: `python:3.11-slim`
- **Exposed port**: `8080`
- **Healthcheck**: Polls `/health` every 30s
- **Entrypoint**: `uvicorn serve:app --host 0.0.0.0 --port 8080`
- **Default tag**: `scientist-bin/{experiment-id}:latest`

## Inference API Endpoints

### `POST /predict`

Run inference on provided instances.

**Request body:**
```json
{
  "instances": [
    {"feature_1": 5.1, "feature_2": 3.5, "feature_3": 1.4}
  ]
}
```

**Response body:**
```json
{
  "predictions": ["setosa"],
  "probabilities": [[0.97, 0.02, 0.01]]
}
```

The `probabilities` field is only returned for classification models that support `predict_proba()`. For regression and clustering models, it is `null`.

### `GET /health`

Returns model status, algorithm name, and experiment ID.

### `GET /info`

Returns full experiment metadata (algorithm, problem type, hyperparameters, test metrics, feature columns).

## Problem-Type-Aware Serving

| Problem Type | `predictions` | `probabilities` |
|---|---|---|
| Classification | Class labels | Per-class probability vectors (if supported) |
| Regression | Numeric values | `null` |
| Clustering | Cluster labels | `null` |

## Key Files

| File | Purpose |
|------|---------|
| `builder.py` | `generate_deploy_artifacts()`, `build_docker_image()`, `push_docker_image()` |
| `templates.py` | `DOCKERFILE_TEMPLATE`, `REQUIREMENTS_TEMPLATE`, `SERVE_TEMPLATE` |
