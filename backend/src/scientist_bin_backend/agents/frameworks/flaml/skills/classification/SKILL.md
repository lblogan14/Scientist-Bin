---
name: classification
description: FLAML AutoML classification — estimator selection, metrics, and parameter guidance
keywords: [classification, binary, multiclass, flaml, automl]
---

Use FLAML AutoML for classification tasks. FLAML automatically selects the best
estimator and hyperparameters within the given time budget.

Key configuration:
- task="classification"
- Default estimators: lgbm, xgboost, xgb_limitdepth, catboost, rf, extra_tree, lrl1
- Metrics: accuracy (default), log_loss, f1, macro_f1, micro_f1, roc_auc, ap
- Use eval_method="holdout" with X_val/y_val for fast iteration
- Use eval_method="cv" with n_splits=5 for more robust evaluation

See reference.md for detailed estimator guidance and parameter recommendations.
