# Scientist-Bin Frontend

React + TypeScript web UI for the Scientist-Bin multi-agent training system.

## Stack

React 19, TypeScript 5.9, Vite 6, shadcn/ui (Radix + Tailwind CSS v4), React Router v7, TanStack React Query, Zustand, Recharts, react-hook-form + Zod, ky, react-markdown, prism-react-renderer.

## Quick Start

```bash
pnpm install
pnpm dev          # Dev server at localhost:5173 (proxies /api to backend)
```

Start the backend first (`uv run scientist-bin serve` from `backend/`).

## Pages

| Route            | Tab         | Purpose |
|------------------|-------------|---------|
| `/`              | Dashboard   | 5 stat cards (total/running/completed/avg accuracy/avg time), objective form with auto-approve toggle and Deep Research mode toggle (budget, time limit settings), active plan review banner, recent experiments with phase badges |
| `/experiments`   | Experiments | Filterable/searchable experiment list (status, framework, problem_type, text search), detail panel with plan summary, iteration count, action links, data-driven HyperparameterForm |
| `/monitor`       | Training    | 10-phase progress pipeline (Init-Classify-EDA-Data-Plan-Review-Execute-Analyze-Summary-Done), plan review HITL panel, agent activity log with error retry indicators, live metrics, console output. ExperimentSelector shows all experiment statuses (running + completed) |
| `/results`       | Results     | Problem-type-aware tab layout via tab-registry (8 common + up to 8 task-specific tabs). Classification adds Confusion Matrix, CV Stability, Overfitting, Features, Hyperparams; regression adds Predicted vs Actual, Residuals, Coefficients, Learning Curve, CV Stability, Overfitting, Features, Hyperparams; clustering adds Clusters, Elbow Curve, Silhouette, Cluster Profiles. ExperimentSelector for switching between experiments |
| `/results/:id`   | Results     | Deep-link to specific experiment |
| `/models`        | Models      | Model ranking cards, metric grouped bar chart, performance-vs-time scatter, cross-experiment comparison table. Per-experiment filtering with "All experiments" option |

## Key Features

- **Deep Research Mode** — dashboard toggle activates the campaign orchestrator with configurable budget (max iterations) and time limit.
- **Cross-page experiment persistence** — selecting an experiment on any page carries over when navigating to other pages (Results, Training, Models). Powered by Zustand store + URL param sync via `useExperimentIdSync`.
- **Plan Review (HITL)** — when the Plan agent creates an execution plan, a review panel appears in the Training page with Approve/Revise buttons. The sidebar shows an amber notification dot and the dashboard shows a banner.
- **Real-time streaming** via Server-Sent Events with 300ms batched updates. Handles 15+ event types including plan review, analysis completion, and summary completion.
- **Problem-type-aware metrics** — metric cards, charts, ranking, and comparison table adapt to classification, regression, and clustering metrics using shared `metric-utils.ts` (direction-aware: lower-is-better for error metrics, higher-is-better for scores).
- **Per-experiment model filtering** — Models page filters by selected experiment with an "All experiments" aggregate option.
- **Rich visualizations** — 13 chart components: confusion matrix heatmaps (CSS Grid), feature importance bars, CV fold box plots, overfitting gauges, Pareto frontier, hyperparameter search tables, radar charts, grouped bars, scatter plots, and more. Dynamic chart axis widths.
- **Enhanced markdown styling** — colored headings, tinted blockquotes, and styled tables in analyst reports, summary reports, execution plans, and selection reasoning via react-markdown + remark-gfm.
- **Syntax-highlighted code** — generated Python code displayed with prism-react-renderer (Night Owl theme) and line numbers.
- **Error retry indicators** — Training Monitor shows error retry counts separately from optimization iterations.
- **Historical activity** — completed experiments show stored progress events in the agent activity log.
- **Error display** — failed experiments show error message and collapsible traceback.
- **Artifact downloads** — download models (.joblib), results JSON, charts JSON, analysis reports, summary reports, and execution plans.
- **Active nav highlighting** — sidebar highlights the current page.
- **3 themes** — light, dark, science (toggled via header, persisted in localStorage).

## Directory Structure

```
src/
├── app/                    # Entry point, router, providers
├── components/
│   ├── charts/             # 13 Recharts chart components
│   ├── feedback/           # EmptyState, ErrorBoundary, LoadingSpinner
│   ├── layout/             # AppSidebar, Header
│   ├── shared/             # ExperimentSelector, MarkdownRenderer
│   └── ui/                 # shadcn/ui primitives (auto-generated)
├── features/
│   ├── dashboard/          # Stats, objective form (with Deep Research toggle), recent experiments
│   ├── experiment-setup/   # Filterable experiment list, detail panel, HyperparameterForm
│   ├── model-selection/    # Model ranking, comparison, tradeoff (per-experiment filtering)
│   ├── results/            # Problem-type-aware results tabs (with ExperimentSelector)
│   └── training-monitor/   # Progress pipeline, HITL, agent log, error retry indicators
├── hooks/                  # Shared hooks (useExperimentIdSync, useCssVars, useMobile)
├── lib/                    # API client (ky-based), metric-utils.ts
├── stores/                 # Zustand store (app-store with selectedExperimentId)
└── types/                  # TypeScript interfaces (api.ts)
```

## Cross-Page Experiment Persistence

Selecting an experiment on any page carries over when navigating between pages:

- The **Zustand store** (`app-store.ts`) holds `selectedExperimentId`
- The **`useExperimentIdSync`** hook (`hooks/use-experiment-id-sync.ts`) bridges URL `?id=` params and the store -- URL wins on page load, store wins on navigation
- Used by Results, Training Monitor, and Models pages so the user can switch pages without losing their selection

## Metric Direction Awareness

Shared utilities in `lib/metric-utils.ts` provide consistent metric handling across the app:

- **`ERROR_METRICS`** -- metrics where lower is better (RMSE, MSE, MAE, Davies-Bouldin, etc.)
- **`RATIO_METRICS`** -- metrics bounded in [0, 1] where higher is better (accuracy, F1, R2, silhouette, etc.)
- **`isErrorMetric()`** / **`isRatioMetric()`** -- predicates for direction-aware comparisons
- **`pickPrimaryMetric()`** -- selects the most appropriate metric for a given problem type

Used by: DashboardStats, ModelRankingCard, ModelComparisonTable, MetricCards, OverviewTab.

## Testing

### Unit Tests (Vitest)

```bash
pnpm test         # Run all 167+ vitest tests
```

### E2E Tests (Playwright)

```bash
pnpm e2e              # Run all Playwright tests (smoke + lifecycle)
pnpm e2e:smoke        # Smoke tests only (page loads, navigation, form validation — no API key needed)
pnpm e2e:lifecycle    # Lifecycle tests (real training pipelines — requires GOOGLE_API_KEY on backend)
pnpm e2e:report       # View HTML report from last run
```

The Playwright config (`playwright.config.ts`) auto-starts both the backend (port 8000) and frontend (port 5173) servers. Two test projects:

- **smoke** (60s timeout): Page loads, sidebar navigation, form validation, framework dropdown, health indicator. Runs on every PR in CI.
- **lifecycle** (600s timeout): Full training pipelines for sklearn (classification, regression, clustering) and FLAML (classification, regression, time-series forecast), plus plan review HITL, error handling, artifact downloads, and model selection page. Runs nightly in CI.

E2E test fixtures live in `e2e/fixtures/`:
- `page-objects.ts` -- DashboardPO, MonitorPO, ResultsPO, ModelsPO for reusable selectors
- `experiment-api.ts` -- API helper for seeding/polling experiments directly

### Other

```bash
pnpm lint         # ESLint
pnpm format       # Prettier
pnpm build        # Type-check + production build
```

Backend-frontend contract tests live in `backend/tests/test_contracts.py` and validate that API response shapes match the TypeScript interfaces in `src/types/api.ts`.
