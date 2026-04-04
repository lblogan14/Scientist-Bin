# Chart Components

Reusable chart components built on Recharts. Used across the Results, Model Selection, and Training Monitor features.

## ChartContainer

Wrapper component that provides a consistent card layout (title, responsive container) for all charts. All Recharts-based charts should be rendered inside a `ChartContainer` or use it indirectly via their own card wrapper.

```
ChartContainer
  -> Card + CardHeader (title)
  -> ResponsiveContainer (width 100%, configurable height, default 300px)
     -> [Recharts chart element]
```

## Component Inventory

### Universal Charts

These charts are used across multiple problem types and features.

| Component | Chart Type | Usage |
|-----------|-----------|-------|
| `MetricLineChart` | Line chart | Live metrics stream (Training Monitor), learning curves |
| `GroupedBarChart` | Grouped bar chart | Best metrics comparison (Model Selection) |
| `MetricScatterChart` | Scatter plot | Metric vs. training time tradeoff (Model Selection) |
| `MetricBarChart` | Single-series bar | Generic metric bar visualization |
| `HorizontalBarChart` | Horizontal bar | Ranked metric display |
| `MetricPieChart` | Pie chart | Proportion visualization |
| `MetricRadarChart` | Radar chart | Multi-metric comparison |
| `BoxPlotChart` | Box plot | CV fold score distribution (CV Stability tab) |
| `HyperparamHeatmap` | Heatmap (CSS Grid) | Hyperparameter search results |
| `FeatureImportanceChart` | Horizontal bar | Feature importance ranking |
| `ParetoFrontierChart` | Scatter + line | Pareto frontier of metric vs. cost |
| `OverfitGaugeChart` | Gauge/arc | Train-vs-validation gap visualization |

### Classification-Specific

| Component | Description |
|-----------|-------------|
| `ConfusionMatrixHeatmap` | CSS Grid-based heatmap for confusion matrices. Not a Recharts chart -- uses styled `<div>` cells with color intensity based on normalized values. |

### Regression-Specific

Regression visualizations are handled at the tab level rather than as standalone chart components:

- `ActualVsPredictedTab` -- scatter plot of predicted vs. actual values
- `ResidualPlotTab` -- residual distribution and residual vs. predicted scatter
- `CoefficientTab` -- horizontal bar chart of model coefficients
- `LearningCurveTab` -- training/validation score over sample sizes

These tab components use `MetricScatterChart`, `MetricLineChart`, and `HorizontalBarChart` internally.

### Clustering-Specific

Clustering visualizations are also handled at the tab level:

- `ClusterScatterTab` -- 2D scatter with cluster coloring
- `ElbowCurveTab` -- inertia vs. number of clusters line chart
- `SilhouetteTab` -- per-sample silhouette coefficient visualization
- `ClusterProfileTab` -- radar or bar charts of cluster centroids

These tab components use `MetricScatterChart`, `MetricLineChart`, and `MetricRadarChart` internally.

## Conventions

- All charts accept a `title` prop (displayed in the card header).
- Data is passed as an array of objects with typed keys.
- Charts are responsive by default via Recharts `ResponsiveContainer`.
- Color palettes use CSS variables from the theme (via `hsl(var(--chart-1))` etc.).

## Key Files

- `ChartContainer.tsx` -- shared card + responsive container wrapper
- `MetricLineChart.tsx` -- generic line chart (used in live metrics, learning curves)
- `GroupedBarChart.tsx` -- multi-series bar chart
- `MetricScatterChart.tsx` -- scatter plot
- `ConfusionMatrixHeatmap.tsx` -- CSS Grid confusion matrix (not Recharts)
- `BoxPlotChart.tsx` -- box-and-whisker for CV stability
- `OverfitGaugeChart.tsx` -- train/val gap gauge
- `HyperparamHeatmap.tsx` -- CSS Grid heatmap for hyperparam search
- `FeatureImportanceChart.tsx` -- ranked feature importance bars
- `ParetoFrontierChart.tsx` -- Pareto frontier scatter + line
