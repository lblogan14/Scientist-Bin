# Results Feature

Displays experiment results across classification, regression, and clustering problem types using a dynamic tab-based layout.

## Architecture

### Tab Registry (`tab-registry.tsx`)

The tab registry is the central mechanism that drives the Results page. It decouples tab definitions from the page component, so adding a new problem type or tab requires only editing the registry.

**Key types:**

- `TabDefinition` -- id, label, component, `isAvailable(ctx)` predicate, and sort order
- `TabContext` -- unified context passed to every tab: result, chartData, experimentHistory, experimentId, experiment

**Public API:**

- `getTabsForResult(problemType, ctx)` -- merges common tabs with problem-type-specific tabs, filters by `isAvailable()`, and sorts by `order`

### How Tabs Work

1. `ResultsPage` fetches the experiment and builds a `TabContext`.
2. `getTabsForResult()` selects which tabs to show based on the `problem_type` from the result.
3. Each tab's `isAvailable(ctx)` predicate checks whether the required data exists (e.g., confusion matrix data, CV fold scores, residual stats).
4. Available tabs are rendered inside a `<Tabs>` component with `<Suspense>` for lazy loading.

### Lazy Loading

All tab components are loaded via `React.lazy()` with dynamic imports. This keeps the initial bundle lean -- only the tabs the user navigates to are fetched.

## Tab Inventory

### Shared Tabs (all problem types)

| Tab | Component | Order | Availability |
|-----|-----------|-------|--------------|
| Overview | `OverviewTabAdapter` | 0 | Always |
| Experiments | `ExperimentsTab` | 1 | Always |
| Plan | `PlanTabAdapter` | 80 | Always |
| Analysis | `AnalysisTabAdapter` | 81 | Always |
| Summary | `SummaryTabAdapter` | 82 | Always |
| Code | `CodeTab` | 83 | Always |
| Data | `DataTab` | 84 | When `data_profile` exists |
| Journal | `JournalTab` | 85 | Always |

### Classification Tabs

| Tab | Component | Order | Availability |
|-----|-----------|-------|--------------|
| Confusion Matrix | `ConfusionMatrixTabWrapper` | 10 | When confusion matrix data exists |
| CV Stability | `CVStabilityTabWrapper` | 11 | When CV fold scores exist |
| Overfitting | `OverfitTabWrapper` | 12 | Always |
| Features | `FeatureTabWrapper` | 13 | When feature importances exist |
| Hyperparams | `HyperparamTabWrapper` | 14 | When hyperparam search data exists |

### Regression Tabs

| Tab | Component | Order | Availability |
|-----|-----------|-------|--------------|
| Predicted vs Actual | `ActualVsPredictedTab` | 10 | When actual_vs_predicted data exists |
| Residuals | `ResidualPlotTab` | 11 | When residual_stats exist |
| Coefficients | `CoefficientTab` | 12 | When coefficient data exists |
| Learning Curve | `LearningCurveTab` | 13 | When learning curve data exists |
| CV Stability | `CVStabilityTabWrapper` | 14 | When CV fold scores exist |
| Overfitting | `OverfitTabWrapper` | 15 | Always |
| Features | `FeatureTabWrapper` | 16 | When feature importances exist |
| Hyperparams | `HyperparamTabWrapper` | 17 | When hyperparam search data exists |

### Clustering Tabs

| Tab | Component | Order | Availability |
|-----|-----------|-------|--------------|
| Clusters | `ClusterScatterTab` | 10 | When cluster scatter data exists |
| Elbow Curve | `ElbowCurveTab` | 11 | When elbow data exists |
| Silhouette | `SilhouetteTab` | 12 | When silhouette data exists |
| Cluster Profiles | `ClusterProfileTab` | 13 | When cluster profile data exists |

## ResultsPage Component

`ResultsPage.tsx` orchestrates the feature. Includes an `ExperimentSelector` (from `@/components/shared/ExperimentSelector`) filtered to `["completed"]` experiments for switching between results. The selected experiment ID is synced between the URL query parameter and Zustand store via `useExperimentIdSync`.

1. Resolves experiment ID from URL params, Zustand store, or auto-detects the latest completed experiment.
2. Fetches experiment data via `useResult()` hook.
3. Renders `MetricCards` at the top for a quick summary of best metrics.
4. Builds `TabContext` and calls `getTabsForResult()` to determine visible tabs.
5. Renders tabs with `<ErrorBoundary>` and `<Suspense>` wrappers.
6. Provides download buttons for Results JSON, Model (.joblib), and Charts data.

## Adding a New Tab

1. Create the tab component in `components/`.
2. Add a lazy import in `tab-registry.tsx`.
3. Add an availability helper function if the tab has data prerequisites.
4. Add a `TabDefinition` entry to the appropriate array (`COMMON_TABS`, `CLASSIFICATION_TABS`, `REGRESSION_TABS`, or `CLUSTERING_TABS`).
5. The tab will automatically appear when its `isAvailable()` returns true.

## Key Files

- `tab-registry.tsx` -- tab definitions, availability predicates, `getTabsForResult()`
- `components/ResultsPage.tsx` -- page component, routing, data fetching
- `components/MetricCards.tsx` -- top-level metric summary cards
- `components/ErrorDisplay.tsx` -- error/traceback display for failed experiments
- `hooks/use-result.ts` -- data fetching hook for experiment results
