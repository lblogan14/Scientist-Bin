# FLAML Time Series Forecasting Reference

## Estimator Selection Guide

| Estimator | Type | Best For | Notes |
|-----------|------|----------|-------|
| `prophet` | Statistical | Seasonal data with holidays | Facebook Prophet, handles missing data |
| `arima` | Statistical | Stationary/trending data | Auto-ARIMA via statsmodels |
| `sarimax` | Statistical | Seasonal + exogenous | ARIMA with seasonal component |
| `lgbm` | ML | Complex patterns, exogenous features | FLAML auto-creates lag features |
| `xgboost` | ML | Robust tabular forecasting | Good with many exogenous features |
| `rf` | ML | Moderate datasets | Ensemble of decision trees |
| `extra_tree` | ML | Fast baseline | Randomized splits |
| `catboost` | ML | Categorical exogenous features | Native categorical handling |

## How FLAML Handles Time Series

- **ML estimators** (lgbm, xgboost, etc.): FLAML automatically creates lagged features
  of the target and exogenous variables, transforming forecasting into supervised regression
- **Statistical models** (prophet, arima, sarimax): Handle temporal dependencies natively

## Period Parameter

The `period` parameter defines the forecast horizon:
- Daily data, predict 30 days: `period=30`
- Monthly data, predict 12 months: `period=12`
- Hourly data, predict 24 hours: `period=24`

## Data Preparation

1. Ensure the temporal column is `datetime64` dtype
2. Sort data chronologically
3. X_train must include at minimum the temporal column
4. y_train contains the target values
5. FLAML expects the temporal column in X, not as the index

## Metric Selection

- **General forecasting**: `mape` (mean absolute percentage error)
- **Avoid near-zero targets**: `rmse` or `mae` instead of `mape`
- **Symmetric error**: Use custom SMAPE if needed

## Common Pitfalls

1. FLAML's `period` must match the validation set size for correct evaluation
2. Statistical models (prophet, arima) may be slow — reduce time_budget or exclude them
3. For very long horizons, ML models often outperform statistical ones
4. Always ensure data is sorted chronologically before splitting
5. Model serialization: prophet models may not serialize with joblib — use pickle as fallback
