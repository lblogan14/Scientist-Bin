# Training Monitor Feature

Real-time training progress display with SSE streaming, a 10-phase pipeline visualization, human-in-the-loop plan review, live metrics, and console output.

## SSE Event Handling

### useExperimentEvents Hook

The `useExperimentEvents` hook (`hooks/use-experiment-events.ts`) manages the SSE connection to `GET /api/v1/experiments/{id}/events`. It is the core of the real-time experience.

**Batching:** Events are accumulated in refs and flushed every 300ms to prevent excessive re-renders and chart jank. Metrics are windowed to the last 200 points per metric name.

**Connection lifecycle:**
- `onopen` -- sets `isConnected = true`
- `onerror` without prior open -- closes the source (prevents auto-reconnect on 404)
- `onerror` after open -- sets `isReconnecting = true`, lets the browser auto-reconnect
- `experiment_done` event -- flushes pending data, sets `isDone = true`, closes the source

**15 SSE event types handled:**

| Event | Effect |
|-------|--------|
| `phase_change` | Activity entry with phase name |
| `agent_activity` | Activity entry with action + decision |
| `metric_update` | Appended to metrics map (name -> points) |
| `log_output` | Appended to console log lines |
| `run_started` | Activity entry with run ID |
| `run_completed` | Activity entry with status + wall time |
| `error` | Activity entry with error message |
| `plan_review_pending` | Sets `planReview` state, triggers HITL UI |
| `plan_review_submitted` | Clears `planReview`, logs approval/revision |
| `plan_completed` | Stores execution plan JSON |
| `analysis_completed` | Stores analysis report markdown |
| `framework_completed` | Activity entry with framework + iteration count |
| `summary_completed` | Stores summary report markdown |
| `experiment_done` | Final flush, marks done, auto-navigates to results |

**Return value:** `{ activities, logLines, metrics, isConnected, isDone, isReconnecting, planReview, executionPlan, analysisReport, summaryReport }`

## Components

### TrainingMonitorPage

Page component that orchestrates the monitor:

1. Resolves experiment ID from URL params or auto-detects the latest running/pending experiment.
2. Fetches experiment status via `useTrainingStatus()`.
3. Connects SSE via `useExperimentEvents()`.
4. Falls back to stored `progress_events` when no live SSE activities exist (e.g., page refresh after experiment completes).
5. Auto-navigates to `/results?id=<id>` 1.5 seconds after `isDone` fires.
6. Displays error state via `ErrorDisplay` if the experiment failed.

### ProgressDisplay

Visual 10-phase pipeline with step indicators:

```
Init -> Classify -> EDA -> Data -> Plan -> Review -> Execute -> Analyze -> Summary -> Done
```

Each step shows a check (completed), spinner (current), amber pulse (plan_review), or empty circle (pending). Also displays an iteration progress bar (current / 5) and experiment metadata.

### PlanReviewPanel

Human-in-the-loop panel triggered by the `plan_review_pending` SSE event:

- Renders the execution plan as markdown via `MarkdownRenderer`.
- "Approve Plan" button sends `"approve"` via `submitPlanReview()`.
- "Request Revision" button expands a textarea for feedback, then submits.
- Shows revision count badge when the plan has been revised.
- Uses `usePlanReview()` hook for the mutation.

### AgentActivityLog

Scrollable list of timestamped agent activities. Each entry shows the agent name, action, timestamp, and optional details.

### MetricsStream

Renders live metric charts in a 2-column grid. Each metric name gets its own `MetricLineChart`. Problem-type-agnostic -- it displays whatever metrics the backend emits (accuracy for classification, RMSE for regression, silhouette for clustering, etc.).

### ConsoleOutput

Monospace log viewer for stdout/stderr from code execution. Auto-scrolls to the bottom as new lines arrive.

## Key Files

- `hooks/use-experiment-events.ts` -- SSE connection, event dispatch, batching
- `hooks/use-training-status.ts` -- polling hook for experiment status
- `hooks/use-plan-review.ts` -- plan review mutation
- `components/TrainingMonitorPage.tsx` -- page layout, routing, fallback logic
- `components/ProgressDisplay.tsx` -- 10-phase pipeline visualization
- `components/PlanReviewPanel.tsx` -- HITL plan review UI
- `components/AgentActivityLog.tsx` -- activity log
- `components/MetricsStream.tsx` -- live metric charts
- `components/ConsoleOutput.tsx` -- console output viewer
