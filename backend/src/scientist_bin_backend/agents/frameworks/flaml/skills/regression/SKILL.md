---
name: regression
description: FLAML AutoML regression — estimator selection, metrics, and parameter guidance
keywords: [regression, prediction, flaml, automl]
---

Use FLAML AutoML for regression tasks. FLAML automatically selects the best
estimator and hyperparameters within the given time budget.

Key configuration:
- task="regression"
- Default estimators: lgbm, rf, catboost, xgboost, extra_tree
- Metrics: r2 (default), rmse, mse, mae
- Use eval_method="holdout" with X_val/y_val for fast iteration

See reference.md for detailed estimator guidance and parameter recommendations.
