# Shared Components

Reusable components used across multiple features. These are application-level shared components (not shadcn/ui primitives from `components/ui/`).

## ExperimentSelector.tsx

Dropdown selector for switching between experiments. Built on shadcn's `Select` component and fetches experiments via `listExperiments()`.

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `statusFilter` | `string[]` | `undefined` | Filter experiments by status (e.g., `["running", "pending"]` or `["completed"]`) |
| `value` | `string \| null` | required | Currently selected experiment ID |
| `onChange` | `(id: string) => void` | required | Callback when selection changes |
| `showAllOption` | `boolean` | `false` | When true, adds an "All experiments" option at the top of the list |
| `className` | `string` | `undefined` | Additional CSS classes for the trigger |

**Usage across pages:**

- **Training Monitor** -- filtered to `["running", "pending"]` for switching between active experiments
- **Results** -- filtered to `["completed"]` for browsing finished experiments
- **Model Selection** -- shows all completed experiments with `showAllOption` for aggregate vs. per-experiment views

Each dropdown item shows a truncated objective (35 chars) with a status label badge (live, done, queued, err).

## MarkdownRenderer.tsx

Renders markdown content using `react-markdown` with `remark-gfm` for GitHub-flavored markdown support. Provides styled heading, paragraph, list, table, code block, and blockquote components via the `Components` override pattern.

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `content` | `string` | Markdown text to render |
| `className` | `string` | Additional CSS classes for the wrapper |

Used by `PlanReviewPanel` (plan markdown), `AnalysisTabAdapter` (analysis report), `SummaryTabAdapter` (summary report), and other tabs that display agent-generated markdown.
