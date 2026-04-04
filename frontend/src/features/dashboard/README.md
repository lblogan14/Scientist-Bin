# Dashboard Feature

The landing page of the application. Provides an overview of experiment activity, a form to launch new experiments, and a notification system for plan reviews.

## Components

### DashboardPage

Layout component that composes the dashboard from four sections:

1. `ActiveExperimentBanner` -- plan-review notification (top)
2. `DashboardStats` -- five stat cards (below banner)
3. `ObjectiveForm` -- new experiment launcher (left column)
4. `RecentExperiments` -- latest experiments list (right column)

### DashboardStats

Displays five stat cards computed from all experiments:

| Card | Source |
|------|--------|
| Total Experiments | `experiments.length` |
| Running | Count where `status === "running"` |
| Completed | Count where `status === "completed"` |
| Avg Best Score | Dynamic per-experiment primary metric average |
| Avg Training Time | Average total training time across completed experiments |

**Dynamic "Avg Best Score" calculation:**

The stat card uses `pickPrimaryMetric()` from `@/lib/metric-utils.ts` to select the appropriate metric per experiment based on its problem type. This means a dashboard with mixed classification (accuracy), regression (R2), and clustering (silhouette) experiments will average the correct primary metric for each. The label adapts via `getPrimaryMetricLabel()` (though the current card uses the generic "Avg Best Score" label).

For each completed experiment, the code iterates through `experiment_history`, finds the first record with metrics, calls `pickPrimaryMetric(metrics, problemType)`, and accumulates the values for averaging.

### ActiveExperimentBanner

Amber alert banner that appears when any experiment is in the `plan_review` phase. Shows the experiment objective and a "Review Plan" button that links to `/monitor?id=<id>`. This is the dashboard-level counterpart to the sidebar notification dot.

### ObjectiveForm

Form with fields for training objective, data file path, data description, framework selector, auto-approve toggle, and a **Deep Research** toggle. Submits via `submitTrainRequest()` and navigates to the training monitor on success.

**Deep Research toggle:** When enabled, the form submits `deep_research: true` which routes the backend to the `CampaignAgent` instead of a single pipeline run. Enabling Deep Research automatically turns on auto-approve (campaigns are autonomous). An "Advanced Campaign Settings" accordion expands with:

- **Max iterations** (1-100, default 10) -- maps to `budget_max_iterations`
- **Time limit** in hours (0.1-168, default 4) -- converted to `budget_time_limit_seconds`

The submit button label changes to "Launch Deep Research" / "Launching Campaign..." when the toggle is active.

### RecentExperiments

Displays the most recent experiments in a compact list with status badges and quick-action links (Monitor for running, Results for completed).

## Hooks

- `use-experiments.ts` -- fetches the full experiment list via `listExperiments()`

## Key Files

- `components/DashboardPage.tsx` -- page layout
- `components/DashboardStats.tsx` -- stat cards with `pickPrimaryMetric()`
- `components/ActiveExperimentBanner.tsx` -- plan-review notification
- `components/ObjectiveForm.tsx` -- new experiment form
- `components/RecentExperiments.tsx` -- recent experiments list
