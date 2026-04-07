# FLAML Regression Reference

## Estimator Selection Guide

| Estimator | Best For | Notes |
|-----------|----------|-------|
| `lgbm` | General tabular | Fast, handles missing values natively |
| `xgboost` | Robust performance | Good L1/L2 regularization |
| `catboost` | Categorical-heavy data | Native categorical support |
| `rf` | Small-medium datasets | Good feature importance estimates |
| `extra_tree` | Fast baseline | Randomized splits, faster than RF |

## Metric Selection

- **General**: `r2` (higher is better, default)
- **Error-focused**: `rmse` or `mse` (lower is better)
- **Robust to outliers**: `mae` (lower is better)
- **Percentage error**: `mape` (lower is better, avoid if targets near zero)

## Time Budget Guidelines

- Quick exploration: 30-60s
- Standard run: 60-120s
- Production quality: 120-300s
- Large dataset (>100k rows): 300-600s

## Enrichment Outputs

The generated code should extract:
1. **Feature importances**: From `automl.model.estimator.feature_importances_`
2. **Residual statistics**: mean, std, max_abs, percentiles of (y_actual - y_pred)
3. **Actual vs predicted**: Scatter data for visualization (max 2000 points)
4. **Trial history**: From FLAML log file for convergence analysis
