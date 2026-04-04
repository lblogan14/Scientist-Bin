# Experiment Setup Feature

Filterable experiment list with detail panel. Mounted at `/experiments`.

## Components

### ExperimentSetupPage

Two-column layout:

- **Left column**: `ExperimentList` -- filterable table of all experiments
- **Right column**: `ExperimentDetail` + `HyperparameterForm` -- detail card for the selected experiment

Selection state (`selectedId`) is managed locally. Clicking a row in the list populates the detail panel.

### ExperimentFilterBar

Four filter controls rendered in a horizontal flex row:

| Filter | Type | Options |
|--------|------|---------|
| Search | Text input | Matches against objective text and experiment ID |
| Status | Select dropdown | All, Pending, Running, Completed, Failed |
| Framework | Select dropdown | All, Scikit-learn, PyTorch, TensorFlow |
| Problem Type | Select dropdown | All, Classification, Regression, Clustering |

All filters are controlled components with state lifted to `ExperimentList`.

### ExperimentList

Fetches experiments via `listExperiments()` and applies client-side filtering using `useMemo`:

- Status filter: exact match on `exp.status`
- Framework filter: exact match on `exp.framework`
- Problem type filter: checks `exp.problem_type` or falls back to `exp.result.problem_type`
- Search filter: case-insensitive substring match on `exp.objective` or `exp.id`

Renders a table with columns: Objective, Framework, Status, Phase, Created, and action icons (Monitor for running, Results for completed). Shows a count of filtered vs. total experiments.

### ExperimentDetail

Card displaying full experiment metadata for the selected experiment:

- Status, framework, creation time, data file path, current phase, iteration count
- Execution plan summary with algorithm badges
- Action buttons: Monitor (running), View Results (completed), Analysis, Delete

Uses `useExperiment(id)` for data fetching and `useDeleteExperiment()` for the delete mutation.

### HyperparameterForm

Form for configuring hyperparameter overrides (placeholder for future use).

## Key Files

- `components/ExperimentSetupPage.tsx` -- page layout with selection state
- `components/ExperimentFilterBar.tsx` -- four filter controls
- `components/ExperimentList.tsx` -- filtered table with client-side filtering
- `components/ExperimentDetail.tsx` -- experiment detail card with actions
- `api/index.ts` -- re-exports API functions for the feature
- `hooks/use-experiment.ts` -- single experiment fetch
- `hooks/use-delete-experiment.ts` -- delete mutation
