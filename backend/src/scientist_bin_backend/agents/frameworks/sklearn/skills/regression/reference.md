# Regression Reference

Comprehensive guide for building regression models with scikit-learn.

## Table of Contents
1. [Algorithm Catalog](#algorithm-catalog)
2. [Algorithm Selection Decision Tree](#algorithm-selection-decision-tree)
3. [Implementation Patterns](#implementation-patterns)
4. [Evaluation Metrics](#evaluation-metrics)
5. [Regularization Strategies](#regularization-strategies)
6. [Feature Importance and Interpretation](#feature-importance-and-interpretation)

---

## Algorithm Catalog

### Linear Regression (OLS)

Best for: baseline model, interpretable coefficients, truly linear relationships.

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression(
    fit_intercept=True,
    n_jobs=-1
)
```

No hyperparameters to tune. Assumes features are not highly correlated (multicollinearity degrades coefficient estimates but not predictions). Check with `np.corrcoef()` or VIF.

### Ridge Regression (L2 Regularization)

Best for: preventing overfitting when features are correlated, when all features are expected to contribute.

```python
from sklearn.linear_model import Ridge

model = Ridge(
    alpha=1.0,     # Regularization strength (higher = more regularization)
    random_state=42
)
```

Key hyperparameter: `alpha` (try `np.logspace(-3, 3, 7)`).

### Lasso Regression (L1 Regularization)

Best for: feature selection (drives unimportant coefficients to exactly zero).

```python
from sklearn.linear_model import Lasso

model = Lasso(
    alpha=0.1,     # Regularization strength
    max_iter=10000,
    random_state=42
)
```

Key hyperparameter: `alpha`. Check `model.coef_` — zero coefficients are eliminated features.

### ElasticNet (L1 + L2)

Best for: combining Lasso's feature selection with Ridge's stability.

```python
from sklearn.linear_model import ElasticNet

model = ElasticNet(
    alpha=0.1,
    l1_ratio=0.5,    # 0 = Ridge, 1 = Lasso, between = mix
    max_iter=10000,
    random_state=42
)
```

Key hyperparameters: `alpha` and `l1_ratio`.

### Support Vector Regression (SVR)

Best for: non-linear regression with epsilon-insensitive loss, small-to-medium datasets.

```python
from sklearn.svm import SVR

model = SVR(
    kernel='rbf',
    C=1.0,
    epsilon=0.1,   # Width of the insensitive tube
    gamma='scale'
)
```

Requires feature scaling. Does not scale well past ~10k samples — use `LinearSVR` for large datasets.

### Random Forest Regressor

Best for: robust general-purpose regression, handles non-linearity, feature importance.

```python
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features=1.0,      # For regression, try 1.0 (all features) or 0.33
    n_jobs=-1,
    random_state=42
)
```

Key hyperparameters: `n_estimators`, `max_depth`, `min_samples_leaf`.

### Gradient Boosting Regressor

Best for: highest accuracy on structured/tabular data.

```python
from sklearn.ensemble import GradientBoostingRegressor

model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=3,
    subsample=0.8,
    loss='squared_error',   # 'squared_error', 'absolute_error', 'huber', 'quantile'
    random_state=42
)
```

For larger datasets, prefer `HistGradientBoostingRegressor`:

```python
from sklearn.ensemble import HistGradientBoostingRegressor

model = HistGradientBoostingRegressor(
    max_iter=200,
    learning_rate=0.1,
    max_leaf_nodes=31,
    random_state=42
)
```

Handles missing values natively — no imputation needed.

### K-Nearest Neighbors Regressor

Best for: simple problems, few features, local patterns.

```python
from sklearn.neighbors import KNeighborsRegressor

model = KNeighborsRegressor(
    n_neighbors=5,
    weights='distance',
    n_jobs=-1
)
```

Requires feature scaling. Does not extrapolate beyond training data range.

### Huber Regressor

Best for: regression with outliers (robust to outliers in the target).

```python
from sklearn.linear_model import HuberRegressor

model = HuberRegressor(
    epsilon=1.35,    # Threshold for outlier vs inlier
    max_iter=1000
)
```

---

## Algorithm Selection Decision Tree

```
Is the relationship expected to be linear?
├── Yes
│   ├── Many correlated features? → Ridge
│   ├── Want automatic feature selection? → Lasso or ElasticNet
│   └── Simple, no regularization needed? → LinearRegression
└── No / Unknown
    ├── Is the dataset > 100k rows?
    │   └── Yes → HistGradientBoostingRegressor
    ├── Are there outliers in the target?
    │   └── Yes → HuberRegressor (linear) or GradientBoosting with loss='huber'
    ├── Need highest accuracy?
    │   └── GradientBoostingRegressor (tune carefully)
    └── Default → RandomForestRegressor (robust starting point)
```

**Default recommendation**: Start with `RandomForestRegressor`, compare against `Ridge` (linear baseline), then try `GradientBoostingRegressor` if you need more accuracy.

---

## Implementation Patterns

### Standard Regression Pipeline

```python
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Split — no stratification for regression
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Preprocessing
numeric_features = X.select_dtypes(include=['number']).columns.tolist()
categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()

preprocessor = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ]), numeric_features),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ]), categorical_features)
])

# Full pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1))
])

# Cross-validation
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5,
                            scoring='neg_mean_absolute_error')
print(f"CV MAE: {-cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Final evaluation
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
```

### Target Transformation

When the target distribution is skewed, transform it:

```python
from sklearn.compose import TransformedTargetRegressor

model = TransformedTargetRegressor(
    regressor=RandomForestRegressor(random_state=42),
    func=np.log1p,          # log(1 + y) to handle skew
    inverse_func=np.expm1   # inverse: exp(y) - 1
)
```

---

## Evaluation Metrics

### Which Metric to Use

| Metric | Formula Intuition | When to Use |
|---|---|---|
| MAE | Average absolute error | Default, intuitive units, robust to outliers |
| RMSE | Root of average squared error | Penalizes large errors more |
| R² | Fraction of variance explained | Comparing models, 1.0 = perfect |
| MAPE | Average percentage error | When relative error matters (forecasting) |
| Median AE | Median of absolute errors | Very robust to outliers |

### Computing All Key Metrics

```python
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    median_absolute_error, mean_absolute_percentage_error
)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mape = mean_absolute_percentage_error(y_test, y_pred)
medae = median_absolute_error(y_test, y_pred)

print(f"MAE:       {mae:.4f}")
print(f"RMSE:      {rmse:.4f}")
print(f"R²:        {r2:.4f}")
print(f"MAPE:      {mape:.4%}")
print(f"Median AE: {medae:.4f}")
```

### Residual Analysis

```python
import matplotlib.pyplot as plt

residuals = y_test - y_pred

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Predicted vs Actual
axes[0].scatter(y_pred, y_test, alpha=0.5, s=10)
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
axes[0].set_xlabel('Predicted')
axes[0].set_ylabel('Actual')
axes[0].set_title('Predicted vs Actual')

# Residual distribution
axes[1].hist(residuals, bins=50, edgecolor='black')
axes[1].axvline(0, color='red', linestyle='--')
axes[1].set_xlabel('Residual')
axes[1].set_title('Residual Distribution')

plt.tight_layout()
plt.savefig('residual_analysis.png', dpi=150)
plt.close()
```

---

## Regularization Strategies

### Choosing Between Ridge, Lasso, and ElasticNet

- **Ridge** (L2): Shrinks all coefficients — use when you believe all features contribute.
- **Lasso** (L1): Zeroes out weak features — use for automatic feature selection.
- **ElasticNet**: Hybrid — use when features are correlated AND you want selection.

### RidgeCV and LassoCV (auto-tuning)

```python
from sklearn.linear_model import RidgeCV, LassoCV

# Automatically picks best alpha via cross-validation
ridge = RidgeCV(alphas=np.logspace(-3, 3, 50), cv=5)
lasso = LassoCV(alphas=np.logspace(-3, 1, 50), cv=5, max_iter=10000)
```

---

## Feature Importance and Interpretation

### Tree-based Feature Importance

```python
# After fitting a pipeline with a tree-based model
model = pipeline.named_steps['regressor']
importances = model.feature_importances_

# Get feature names (works with ColumnTransformer)
feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()

# Sort and plot
sorted_idx = np.argsort(importances)[-20:]  # top 20
fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(range(len(sorted_idx)), importances[sorted_idx])
ax.set_yticks(range(len(sorted_idx)))
ax.set_yticklabels(feature_names[sorted_idx])
ax.set_title('Top 20 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150)
plt.close()
```

### Permutation Importance (model-agnostic)

```python
from sklearn.inspection import permutation_importance

perm_result = permutation_importance(
    pipeline, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1
)

sorted_idx = perm_result.importances_mean.argsort()[-20:]
fig, ax = plt.subplots(figsize=(10, 8))
ax.boxplot(
    perm_result.importances[sorted_idx].T,
    vert=False,
    labels=X.columns[sorted_idx]
)
ax.set_title('Permutation Importance (Test Set)')
plt.tight_layout()
plt.savefig('permutation_importance.png', dpi=150)
plt.close()
```

### Linear Model Coefficients

```python
# For Ridge, Lasso, ElasticNet, LinearRegression
coef_df = pd.DataFrame({
    'feature': feature_names,
    'coefficient': model.coef_
}).sort_values('coefficient', key=abs, ascending=False)
print(coef_df.head(20))
```
