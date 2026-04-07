# FLAML Classification Reference

## Estimator Selection Guide

| Estimator | Best For | Pros | Cons |
|-----------|----------|------|------|
| `lgbm` | General tabular | Fast, handles missing values, categorical features | Less interpretable |
| `xgboost` | Balanced performance | Robust, good defaults | Slower than lgbm |
| `xgb_limitdepth` | Overfitting control | Depth-limited XGBoost | May underfit complex data |
| `catboost` | High-cardinality categoricals | Native categorical handling | Slow on large datasets |
| `rf` | Small-medium datasets | Robust, interpretable importances | Slow for large param spaces |
| `extra_tree` | Fast baseline | Faster than RF, good baseline | Slightly less accurate |
| `lrl1` | Linear relationships | Fast, interpretable, L1 regularization | Cannot capture non-linearity |

## Metric Selection

- **Balanced classes**: `accuracy` or `f1`
- **Imbalanced classes**: `macro_f1`, `roc_auc`, or `ap` (average precision)
- **Multi-class**: `macro_f1` or `log_loss`
- **Binary with threshold tuning**: `roc_auc`

## Time Budget Guidelines

- Quick exploration: 30-60s
- Standard run: 60-120s
- Production quality: 120-300s
- Large dataset (>100k rows): 300-600s

## Common Pitfalls

1. Do NOT preprocess data with sklearn pipelines — FLAML handles imputation and encoding internally
2. Set `seed=42` for reproducibility
3. Use `verbose=0` to minimize output
4. Set `log_file_name` to capture trial history
5. For imbalanced data, use `sample_weight` parameter or switch metric to `macro_f1`
