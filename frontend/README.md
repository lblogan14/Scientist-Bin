# Scientist-Bin Frontend

React + TypeScript web UI for the Scientist-Bin multi-agent training system.

## Stack

React 19, TypeScript 5.9, Vite 8, shadcn/ui (Radix + Tailwind CSS v4), React Router v7, TanStack React Query, Zustand, Recharts, react-hook-form + Zod, ky.

## Quick Start

```bash
pnpm install
pnpm dev          # Dev server at localhost:5173 (proxies /api to backend)
```

Start the backend first (`uv run scientist-bin serve` from `backend/`).

## Pages

| Route | Tab | Purpose |
|-------|-----|---------|
| `/` | Dashboard | Stats, objective form (with dataset path relative to `backend/data/`), recent experiments |
| `/experiments` | Experiments | List of all experiments, click to view details |
| `/monitor` | Training | Real-time progress (SSE), agent activity log, metrics charts, console output. Auto-selects latest experiment. |
| `/results` | Results | Metric cards, algorithm comparison charts, generated code, data profile, journal. Download buttons for model and results. Auto-selects latest completed experiment. |
| `/models` | Models | Cross-experiment model comparison table and charts |

## Key Features

- **Real-time streaming** via Server-Sent Events with 300ms batched updates
- **Historical activity** — completed experiments show stored progress events in the agent activity log
- **Error display** — failed experiments show error message and collapsible traceback
- **Artifact downloads** — download trained models (.joblib) and results JSON from the Results page
- **Active nav highlighting** — sidebar highlights the current page
- **3 themes** — light, dark, science (toggled via header, persisted in localStorage)