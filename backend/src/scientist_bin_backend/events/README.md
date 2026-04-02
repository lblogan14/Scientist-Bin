# Events

Real-time event system for experiment progress streaming.

## Modules

| File | Purpose |
|------|---------|
| `bus.py` | `EventBus` -- per-experiment pub/sub backed by `asyncio.Queue`, supports multiple subscribers |
| `types.py` | `ExperimentEvent` model with SSE formatting, `EventType` literal union |

## Event Types

| Type | When | Data |
|------|------|------|
| `phase_change` | Agent enters a new phase | `{phase, message}` |
| `metric_update` | Training reports a metric | `{name, value, step, run_id}` |
| `agent_activity` | Agent node starts/completes | `{action, iteration}` or `{agent, node, summary}` |
| `log_output` | stdout/stderr line | `{line, stream}` |
| `run_started` | Subprocess launched | `{run_id, iteration}` |
| `run_completed` | Subprocess finished | `{run_id, status, wall_time}` |
| `error` | Something went wrong | `{message, run_id}` or `{phase, message}` |
| `experiment_done` | Pipeline complete | `{best_model, best_metrics}` |
| `plan_review_pending` | Plan ready for human review | `{plan_markdown, revision_count}` |
| `plan_review_submitted` | Human responded to plan review | `{approved, feedback?, revision_count?}` |
| `plan_completed` | Plan agent finished | `{plan_approved}` |
| `analysis_completed` | Analyst agent finished | `{has_report}` or `{phase, message, report_path}` |
| `sklearn_completed` | Sklearn agent finished | `{iterations}` |
| `framework_completed` | Framework agent finished | `{framework, iterations}` |
| `summary_completed` | Summary agent finished | `{best_model}` or `{phase, report_path, best_model}` |

## Usage

The API exposes `GET /api/v1/experiments/{id}/events` as an SSE endpoint. The frontend connects via `EventSource` for real-time updates.

Events are also mirrored into the `ExperimentStore` by `_sync_events_from_queue()` in `routes.py`, so polling clients (GET /experiments/{id}) see up-to-date phase and progress without relying solely on the SSE stream.

## Race-Free Event Consumption

To guarantee no events are lost (e.g. in background tasks that start before the consumer loop), use `pre_register()` + `consume()` instead of `subscribe()`:

```python
queue = event_bus.pre_register(experiment_id)   # register BEFORE agent starts
sync_task = asyncio.create_task(process_events(experiment_id, queue))
result = await agent.run(...)                    # events buffered in queue
await event_bus.close(experiment_id)
await sync_task
```

`subscribe()` is still available for cases where the race is not a concern (e.g. SSE streaming endpoint).
