# Scientist-Bin Frontend

React + TypeScript web UI for the Scientist-Bin multi-agent training system.

## Stack

React 19, TypeScript 5.9, Vite 8, shadcn/ui (Radix + Tailwind CSS v4), React Router v7, TanStack React Query, Zustand, Recharts, react-hook-form + Zod, ky, react-markdown, prism-react-renderer.

## Quick Start

```bash
pnpm install
pnpm dev          # Dev server at localhost:5173 (proxies /api to backend)
```

Start the backend first (`uv run scientist-bin serve` from `backend/`).

## Pages

| Route            | Tab         | Purpose |
|------------------|-------------|---------|
| `/`              | Dashboard   | 5 stat cards (total/running/completed/avg accuracy/avg time), objective form with auto-approve toggle, active plan review banner, recent experiments with phase badges |
| `/experiments`   | Experiments | Filterable/searchable experiment list (status, framework, text search), detail panel with plan summary, iteration count, action links |
| `/monitor`       | Training    | 8-phase progress pipeline (Classify→EDA→Plan→Review→Execute→Analyze→Summary→Done), plan review HITL panel, agent activity log, live metrics, console output |
| `/results`       | Results     | 13-tab layout: Overview (executive summary, best model, Pareto chart), Experiments (comparison charts, radar), Confusion Matrix (heatmap), CV Stability (box plots), Overfitting (train-val gap), Features (importance bars), Hyperparams (search landscape), Plan (structured + markdown), Analysis (analyst report), Summary (accordion sections), Code (syntax-highlighted), Data Profile, Journal |
| `/results/:id`   | Results     | Deep-link to specific experiment |
| `/models`        | Models      | Model ranking cards, metric grouped bar chart, performance-vs-time scatter, cross-experiment comparison table |

## Key Features

- **Plan Review (HITL)** — when the Plan agent creates an execution plan, a review panel appears in the Training page with Approve/Revise buttons. The sidebar shows an amber notification dot and the dashboard shows a banner.
- **Real-time streaming** via Server-Sent Events with 300ms batched updates. Handles 15+ event types including plan review, analysis completion, and summary completion.
- **Rich visualizations** — 14 chart components: confusion matrix heatmaps (CSS Grid), feature importance bars, CV fold box plots, overfitting gauges, Pareto frontier, hyperparameter search tables, radar charts, grouped bars, scatter plots, and more.
- **Markdown rendering** — analyst reports, summary reports, execution plans, and selection reasoning rendered as styled markdown via react-markdown + remark-gfm.
- **Syntax-highlighted code** — generated Python code displayed with prism-react-renderer (Night Owl theme) and line numbers.
- **Historical activity** — completed experiments show stored progress events in the agent activity log.
- **Error display** — failed experiments show error message and collapsible traceback.
- **Artifact downloads** — download models (.joblib), results JSON, charts JSON, analysis reports, summary reports, and execution plans.
- **Active nav highlighting** — sidebar highlights the current page.
- **3 themes** — light, dark, science (toggled via header, persisted in localStorage).

## Testing

```bash
pnpm test         # Run vitest tests
pnpm lint         # ESLint
pnpm format       # Prettier
pnpm build        # Type-check + production build
```
