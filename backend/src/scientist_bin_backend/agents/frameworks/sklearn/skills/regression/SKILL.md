---
name: regression
description: Scikit-learn regression skill for supervised learning tasks with continuous numeric targets
---

# Regression Skill

This skill handles supervised regression tasks using scikit-learn.

## Capabilities

- Linear and non-linear regression
- Algorithm selection (LinearRegression, Ridge, Lasso, ElasticNet, RandomForestRegressor, GradientBoostingRegressor, SVR)
- Preprocessing pipelines (scaling, encoding, imputation)
- Cross-validation and hyperparameter tuning
- Metric evaluation (MAE, RMSE, R-squared, explained variance)
- Feature importance and partial dependence analysis

## When to Use

Use this skill when the objective involves predicting a continuous numeric value. Examples:

- "Predict house prices from features"
- "Estimate customer lifetime value"
- "Forecast sales revenue"
- "Predict temperature from sensor readings"

## Approach

1. Load and inspect the dataset (automated EDA)
2. Analyze target distribution (skewness, outliers)
3. Identify feature types and correlations with target
4. Build preprocessing pipeline (imputer -> scaler/encoder via ColumnTransformer)
5. Start with linear models as baseline (LinearRegression, Ridge)
6. Progress to tree-based models (RandomForest, GradientBoosting)
7. Tune hyperparameters via cross-validated search
8. Compare metrics (MAE, RMSE, R2) and select best model
9. Analyze residuals for model diagnostics
10. Generate final evaluation report

## Reference

See `reference.md` in this directory for comprehensive algorithm decision trees,
parameter tuning grids, residual analysis patterns, and metric selection guidance.
