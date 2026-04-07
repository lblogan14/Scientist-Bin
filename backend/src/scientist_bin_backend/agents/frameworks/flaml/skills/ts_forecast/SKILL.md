---
name: ts_forecast
description: FLAML AutoML time series forecasting — estimator selection, period, and parameter guidance
keywords: [time series, forecasting, ts_forecast, flaml, automl, prophet, arima]
---

Use FLAML AutoML for time series forecasting tasks. FLAML supports both
statistical models (Prophet, ARIMA, SARIMAX) and ML models (LightGBM, XGBoost)
with automatic lag feature creation.

Key configuration:
- task="ts_forecast"
- period parameter required (forecast horizon in number of time steps)
- Default estimators: lgbm, xgboost, rf, extra_tree, catboost, prophet, arima, sarimax
- Metrics: mape (default), rmse, mae
- Data must have a datetime column as index or feature

See reference.md for detailed forecasting guidance.
