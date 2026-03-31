# Events

Real-time event system for experiment progress streaming.

## Modules

| File | Purpose |
|------|---------|
| `bus.py` | `EventBus` — per-experiment pub/sub backed by `asyncio.Queue`, supports multiple subscribers |
| `types.py` | `ExperimentEvent` model with SSE formatting |

## Event Types

| Type | When | Data |
|------|------|------|
| `phase_change` | Agent enters a new phase | `{phase, message}` |
| `metric_update` | Training reports a metric | `{name, value, step, run_id}` |
| `agent_activity` | Agent node starts/completes | `{action, iteration}` |
| `log_output` | stdout/stderr line | `{line, stream}` |
| `run_started` | Subprocess launched | `{run_id, iteration}` |
| `run_completed` | Subprocess finished | `{run_id, status, wall_time}` |
| `error` | Something went wrong | `{message, run_id}` |
| `experiment_done` | Pipeline complete | `{best_model, best_metrics}` |

## Usage

The API exposes `GET /api/v1/experiments/{id}/events` as an SSE endpoint. The frontend connects via `EventSource` for real-time updates.
