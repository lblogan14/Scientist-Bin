/**
 * Expected metric ranges by problem type.
 *
 * Bounds are intentionally generous — ML results vary across runs.
 * The goal is sanity-checking (no NaN, no negative accuracy, etc.),
 * not exact value matching.
 */

export interface MetricRange {
  min: number;
  max: number;
}

export interface ProblemTypeMetrics {
  /** At least one of these keys must appear in the metric cards. */
  requiredAny: string[];
  /** Acceptable value ranges by metric name (case-insensitive match). */
  ranges: Record<string, MetricRange>;
}

// ---------------------------------------------------------------------------
// Definitions
// ---------------------------------------------------------------------------

export const CLASSIFICATION_METRICS: ProblemTypeMetrics = {
  requiredAny: ["accuracy", "f1", "f1_score", "precision", "recall"],
  ranges: {
    accuracy: { min: 0.3, max: 1.0 },
    precision: { min: 0, max: 1.0 },
    recall: { min: 0, max: 1.0 },
    f1: { min: 0, max: 1.0 },
    f1_score: { min: 0, max: 1.0 },
    weighted_f1: { min: 0, max: 1.0 },
    macro_f1: { min: 0, max: 1.0 },
    roc_auc: { min: 0, max: 1.0 },
    log_loss: { min: 0, max: 50 },
  },
};

export const REGRESSION_METRICS: ProblemTypeMetrics = {
  requiredAny: ["r2", "r2_score", "rmse", "mae"],
  ranges: {
    r2: { min: -1, max: 1.0 },
    r2_score: { min: -1, max: 1.0 },
    rmse: { min: 0, max: Infinity },
    mae: { min: 0, max: Infinity },
    mse: { min: 0, max: Infinity },
    mape: { min: 0, max: 1000 },
  },
};

export const CLUSTERING_METRICS: ProblemTypeMetrics = {
  requiredAny: ["silhouette_score", "silhouette", "calinski_harabasz_score"],
  ranges: {
    silhouette_score: { min: -1, max: 1.0 },
    silhouette: { min: -1, max: 1.0 },
    calinski_harabasz_score: { min: 0, max: Infinity },
    davies_bouldin_score: { min: 0, max: Infinity },
    inertia: { min: 0, max: Infinity },
    n_clusters: { min: 1, max: 100 },
  },
};

export const TIMESERIES_METRICS: ProblemTypeMetrics = {
  requiredAny: ["mape", "rmse", "mae", "smape"],
  ranges: {
    mape: { min: 0, max: 1000 },
    smape: { min: 0, max: 200 },
    rmse: { min: 0, max: Infinity },
    mae: { min: 0, max: Infinity },
    mse: { min: 0, max: Infinity },
  },
};

// ---------------------------------------------------------------------------
// Lookup
// ---------------------------------------------------------------------------

export const METRIC_RANGES: Record<string, ProblemTypeMetrics> = {
  classification: CLASSIFICATION_METRICS,
  regression: REGRESSION_METRICS,
  clustering: CLUSTERING_METRICS,
  ts_forecast: TIMESERIES_METRICS,
};

/**
 * Get the metric definition for a problem type.
 * Falls back to classification if unknown.
 */
export function getMetricRanges(problemType: string): ProblemTypeMetrics {
  return METRIC_RANGES[problemType] ?? CLASSIFICATION_METRICS;
}
