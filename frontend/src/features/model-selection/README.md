# Model Selection Feature

Compares and ranks trained models across experiments with direction-aware metric handling for classification, regression, and clustering problem types.

## Metric Direction Awareness

The core challenge: not all metrics improve in the same direction. Accuracy goes up when better; RMSE goes down. This feature uses shared utilities from `@/lib/metric-utils.ts` to handle this correctly throughout.

- **Error metrics** (lower is better): `rmse`, `mse`, `mae`, `mape`, `davies_bouldin`
- **Performance metrics** (higher is better): `accuracy`, `f1`, `r2`, `silhouette_score`, etc.

### Primary Metric Selection

`pickPrimaryMetric(metrics, problemType)` selects the most meaningful metric per problem type:

- **Classification**: `val_accuracy` > `accuracy` > `val_f1_macro` > `f1_macro` > `val_f1` > `f1`
- **Regression**: `val_r2` > `r2` > `val_rmse` > `rmse` > `val_mae` > `mae`
- **Clustering**: `silhouette_score` > `calinski_harabasz` > `calinski_harabasz_score`
- **Fallback**: first available metric in the record

## Components

### ModelRankingCard

Displays up to 6 ranked model cards. For each completed experiment:

1. Finds the best experiment record (matching `best_model` algorithm).
2. Calls `pickPrimaryMetric()` to determine the headline metric and value.
3. Sorts models using `compareMetricValues()` -- this ensures RMSE-best models rank first (lowest value) while accuracy-best models also rank first (highest value).
4. Highlights the top-ranked model with a primary border and award icon.
5. Each card shows: algorithm name, primary metric + value, training time, deploy button.

### ModelComparisonTable

Flat table of all experiment runs across all experiments:

1. Flattens `experiment_history` from every completed experiment.
2. Collects up to 4 unique metric names across all records.
3. Uses `getBestValue(values, metricKey)` to find the best value per metric column -- applies `Math.min` for error metrics, `Math.max` for performance metrics.
4. Highlights cells where the value matches the best value for that metric.
5. Links each row back to its experiment results page.

### ModelMetricChart

Grouped bar chart comparing best metrics across experiments using `GroupedBarChart`.

### ModelTradeoffScatter

Scatter plot of primary metric vs. training time for all experiment runs, using `MetricScatterChart`. Helps identify the speed/accuracy tradeoff.

### ModelSelectionPage

Page component that ties everything together:

1. Fetches completed experiments via `useModels()`.
2. Renders `DeploymentCard` for the best model.
3. Lays out ranking cards, metric chart + tradeoff scatter (2-column grid), and comparison table.

### DeploymentCard

Deployment UI for the selected model. Calls `deployModel()` / `undeployModel()` API endpoints.

## Key Files

- `components/ModelRankingCard.tsx` -- direction-aware ranking with `pickPrimaryMetric()` and `compareMetricValues()`
- `components/ModelComparisonTable.tsx` -- direction-aware best-value highlighting with `getBestValue()`
- `components/ModelMetricChart.tsx` -- grouped bar chart of best metrics
- `components/ModelTradeoffScatter.tsx` -- metric vs. training time scatter
- `components/ModelSelectionPage.tsx` -- page layout and data orchestration
- `components/DeploymentCard.tsx` -- model deployment UI
- `hooks/use-models.ts` -- data fetching hook (completed experiments)
