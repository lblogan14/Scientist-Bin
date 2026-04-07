/**
 * Shared metric utilities for problem-type-aware metric handling.
 *
 * Provides direction-awareness (higher-is-better vs lower-is-better),
 * primary metric selection by problem type, and ratio metric detection.
 */

// ---------------------------------------------------------------------------
// Metric classification sets
// ---------------------------------------------------------------------------

/** Error metrics where lower values indicate better performance. */
const ERROR_METRICS = new Set([
  "rmse",
  "mse",
  "mae",
  "mape",
  "val_rmse",
  "val_mse",
  "val_mae",
  "val_mape",
  "davies_bouldin",
  "davies_bouldin_score",
  "smape",
  "val_smape",
  "mase",
  "val_mase",
]);

/** Ratio/score metrics bounded roughly in [0, 1] (higher is better). */
const RATIO_METRICS = new Set([
  "accuracy",
  "f1",
  "macro_f1",
  "micro_f1",
  "weighted_f1",
  "f1_macro",
  "f1_micro",
  "f1_weighted",
  "precision",
  "recall",
  "r2",
  "roc_auc",
  "val_accuracy",
  "val_f1",
  "val_f1_macro",
  "val_r2",
  "val_roc_auc",
  "silhouette_score",
]);

// ---------------------------------------------------------------------------
// Predicates
// ---------------------------------------------------------------------------

/** Returns true if the metric is an error metric (lower is better). */
export function isErrorMetric(key: string): boolean {
  return ERROR_METRICS.has(key.toLowerCase());
}

/** Returns true if the metric is a ratio metric bounded in [0, 1]. */
export function isRatioMetric(key: string): boolean {
  return RATIO_METRICS.has(key.toLowerCase());
}

// ---------------------------------------------------------------------------
// Primary metric selection
// ---------------------------------------------------------------------------

export interface PrimaryMetric {
  key: string;
  value: number;
}

/**
 * Pick the most appropriate primary metric based on problem type.
 * Returns the best available metric key and value.
 */
export function pickPrimaryMetric(
  metrics: Record<string, number>,
  problemType: string | null | undefined,
): PrimaryMetric {
  const tryKeys = (keys: string[]): PrimaryMetric | null => {
    for (const key of keys) {
      if (metrics[key] != null) {
        return { key, value: metrics[key] };
      }
    }
    return null;
  };

  let result: PrimaryMetric | null = null;

  if (problemType === "regression") {
    result = tryKeys(["val_r2", "r2", "val_rmse", "rmse", "val_mae", "mae"]);
  } else if (problemType === "clustering") {
    result = tryKeys([
      "silhouette_score",
      "calinski_harabasz",
      "calinski_harabasz_score",
    ]);
  } else if (problemType === "ts_forecast") {
    result = tryKeys([
      "val_mape",
      "mape",
      "val_rmse",
      "rmse",
      "val_mae",
      "mae",
    ]);
  } else {
    // Classification (default)
    result = tryKeys([
      "val_accuracy",
      "accuracy",
      "val_f1_macro",
      "f1_macro",
      "val_f1",
      "f1",
    ]);
  }

  if (result) return result;

  // Fallback: first available metric
  const firstKey = Object.keys(metrics)[0];
  return firstKey
    ? { key: firstKey, value: metrics[firstKey] ?? 0 }
    : { key: "", value: 0 };
}

// ---------------------------------------------------------------------------
// Comparison utilities
// ---------------------------------------------------------------------------

/**
 * Find the best value from an array of numbers for a given metric.
 * Uses Math.min for error metrics, Math.max for performance metrics.
 */
export function getBestValue(values: number[], metricKey: string): number {
  if (values.length === 0) return 0;
  return isErrorMetric(metricKey) ? Math.min(...values) : Math.max(...values);
}

/**
 * Compare two metric values. Returns negative if a is better, positive if b is better.
 * For error metrics (lower is better), lower a means a is better (returns negative).
 * For performance metrics (higher is better), higher a means a is better (returns negative).
 */
export function compareMetricValues(
  a: number,
  b: number,
  metricKey: string,
): number {
  return isErrorMetric(metricKey) ? a - b : b - a;
}

// ---------------------------------------------------------------------------
// Color helpers
// ---------------------------------------------------------------------------

/** Get text color class for a metric value (ratio metrics only). */
export function getMetricColor(key: string, value: number): string {
  if (isErrorMetric(key)) {
    // For error metrics, we don't apply ratio-based coloring
    return "";
  }
  if (!isRatioMetric(key)) return "";
  if (value >= 0.9) return "text-success";
  if (value >= 0.7) return "text-warning";
  return "text-destructive";
}

/** Get progress bar color class for a metric value. */
export function getBarColor(key: string, value: number): string {
  if (!isRatioMetric(key)) return "bg-primary";
  if (value >= 0.9) return "bg-success";
  if (value >= 0.7) return "bg-warning";
  return "bg-destructive";
}

