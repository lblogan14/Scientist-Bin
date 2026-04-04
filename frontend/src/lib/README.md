# Lib

Shared utilities and the API client used across all features.

## api-client.ts

Full API client built on [ky](https://github.com/sindresorhus/ky). All requests are prefixed with `/api/v1` and proxied to the backend by Vite in development.

### Functions

| Function | Method | Endpoint | Returns |
|----------|--------|----------|---------|
| `submitTrainRequest(request)` | POST | `/train` | `Experiment` |
| `listExperiments(params?)` | GET | `/experiments` | `PaginatedExperiments` |
| `getExperiment(id)` | GET | `/experiments/{id}` | `Experiment` |
| `deleteExperiment(id)` | DELETE | `/experiments/{id}` | `void` |
| `getExperimentJournal(id)` | GET | `/experiments/{id}/journal` | `JournalEntry[]` |
| `submitPlanReview(id, review)` | POST | `/experiments/{id}/review` | `{ status }` |
| `checkHealth()` | GET | `/health` | `HealthResponse` |
| `getExperimentPlan(id)` | GET | `/experiments/{id}/plan` | `{ execution_plan }` |
| `getExperimentAnalysis(id)` | GET | `/experiments/{id}/analysis` | `{ analysis_report, split_data_paths }` |
| `getExperimentSummary(id)` | GET | `/experiments/{id}/summary` | `{ summary_report }` |
| `deployModel(id)` | POST | `/experiments/{id}/deploy` | `DeploymentInfo` |
| `undeployModel(id)` | POST | `/experiments/{id}/undeploy` | `{ status }` |
| `getDeployment(id)` | GET | `/experiments/{id}/deployment` | `DeploymentInfo` |

### SSE & Download Helpers

- `createExperimentEventSource(id)` -- returns a native `EventSource` for `/experiments/{id}/events`
- `getArtifactDownloadUrl(id, type)` -- returns URL for `/experiments/{id}/artifacts/{type}`
- `getModelDownloadUrl(id)` / `getResultsDownloadUrl(id)` -- convenience wrappers
- `extractErrorMessage(error)` -- extracts human-readable message from ky `HTTPError` or generic `Error`

## metric-utils.ts

Direction-aware metric utilities used by Dashboard, Model Selection, and Results features. Solves the problem of correctly sorting and highlighting metrics where lower can be better (error metrics) or higher can be better (performance metrics).

### Metric Classification Sets

- `ERROR_METRICS` -- metrics where lower is better: `rmse`, `mse`, `mae`, `mape`, `davies_bouldin`, and their `val_` prefixed variants
- `RATIO_METRICS` -- metrics bounded roughly in [0, 1] where higher is better: `accuracy`, `f1`, `r2`, `roc_auc`, `silhouette_score`, and variants

### Key Functions

| Function | Purpose |
|----------|---------|
| `isErrorMetric(key)` | Returns true if lower is better |
| `isRatioMetric(key)` | Returns true if bounded in [0, 1] |
| `pickPrimaryMetric(metrics, problemType)` | Selects the best primary metric for a given problem type. Tries a ranked list of preferred keys per type. |
| `getBestValue(values, metricKey)` | Returns `Math.min` for error metrics, `Math.max` for performance metrics |
| `compareMetricValues(a, b, metricKey)` | Direction-aware comparison for sorting (negative = a is better) |
| `getMetricColor(key, value)` | CSS class for ratio metrics: green (>=0.9), yellow (>=0.7), red (<0.7) |
| `getBarColor(key, value)` | Progress bar CSS class with same thresholds |
| `getPrimaryMetricLabel(problemType)` | Dashboard stat card label: "Avg Best Accuracy", "Avg Best R2", or "Avg Silhouette" |

### Primary Metric Priority

| Problem Type | Metric Priority (first available wins) |
|-------------|----------------------------------------|
| Classification | `val_accuracy` > `accuracy` > `val_f1_macro` > `f1_macro` > `val_f1` > `f1` |
| Regression | `val_r2` > `r2` > `val_rmse` > `rmse` > `val_mae` > `mae` |
| Clustering | `silhouette_score` > `calinski_harabasz` > `calinski_harabasz_score` |

## utils.ts

General utility: `cn()` -- merges Tailwind CSS classes using `clsx` + `tailwind-merge`. Used throughout all components for conditional class composition.
