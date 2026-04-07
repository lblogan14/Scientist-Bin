# Evaluation & Model Selection Reference

Comprehensive guide for model evaluation, hyperparameter tuning, and model comparison.

## Table of Contents
1. [Cross-Validation](#cross-validation)
2. [Hyperparameter Tuning](#hyperparameter-tuning)
3. [Model Comparison](#model-comparison)
4. [Learning Curves and Diagnostics](#learning-curves-and-diagnostics)
5. [Model Persistence](#model-persistence)
6. [Scoring Reference Table](#scoring-reference-table)

---

## Cross-Validation

Cross-validation gives a more reliable estimate of model performance than a single train/test split.

### Basic Cross-Validation

```python
from sklearn.model_selection import cross_val_score, cross_validate

# Single metric
scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='f1_weighted')
print(f"F1: {scores.mean():.4f} ± {scores.std():.4f}")

# Multiple metrics at once
results = cross_validate(
    pipeline, X_train, y_train, cv=5,
    scoring=['accuracy', 'f1_weighted', 'roc_auc_ovr'],
    return_train_score=True
)
for metric in ['accuracy', 'f1_weighted', 'roc_auc_ovr']:
    test = results[f'test_{metric}']
    train = results[f'train_{metric}']
    print(f"{metric}: test={test.mean():.4f}±{test.std():.4f}  train={train.mean():.4f}")
```

### CV Strategies

| Strategy | When to Use | Code |
|---|---|---|
| KFold | Regression, large balanced data | `KFold(n_splits=5, shuffle=True, random_state=42)` |
| StratifiedKFold | Classification (preserves class ratios) | `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` |
| RepeatedStratifiedKFold | Small datasets, need robust estimate | `RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)` |
| LeaveOneOut | Very small datasets (< 50 samples) | `LeaveOneOut()` |
| TimeSeriesSplit | Temporal data (no future leakage) | `TimeSeriesSplit(n_splits=5)` |
| GroupKFold | Groups shouldn't be split (e.g., patients) | `GroupKFold(n_splits=5)` |

```python
from sklearn.model_selection import (
    KFold, StratifiedKFold, RepeatedStratifiedKFold,
    TimeSeriesSplit, GroupKFold
)

# Classification default
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Regression default
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Time series
cv = TimeSeriesSplit(n_splits=5)

# Pass to cross_val_score
scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='f1_weighted')
```

---

## Hyperparameter Tuning

### GridSearchCV (Exhaustive)

Tries all combinations. Best for small parameter spaces (< 100 combinations).

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'preprocessor__num__scaler': [StandardScaler(), RobustScaler()],
    'model__n_estimators': [100, 200, 300],
    'model__max_depth': [None, 10, 20],
    'model__min_samples_leaf': [1, 2, 5]
}

search = GridSearchCV(
    pipeline,
    param_grid,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='f1_weighted',
    n_jobs=-1,
    verbose=1,
    return_train_score=True
)

search.fit(X_train, y_train)

print(f"Best score: {search.best_score_:.4f}")
print(f"Best params: {search.best_params_}")

# Evaluate best model on test set
y_pred = search.predict(X_test)
```

### RandomizedSearchCV (Efficient)

Samples from parameter distributions. Best for large spaces or many hyperparameters.

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform, loguniform

param_distributions = {
    'model__n_estimators': randint(50, 500),
    'model__max_depth': [None, 5, 10, 15, 20, 30],
    'model__min_samples_split': randint(2, 20),
    'model__min_samples_leaf': randint(1, 10),
    'model__max_features': uniform(0.1, 0.9),
}

search = RandomizedSearchCV(
    pipeline,
    param_distributions,
    n_iter=50,              # Number of random combinations to try
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='f1_weighted',
    n_jobs=-1,
    random_state=42,
    verbose=1
)

search.fit(X_train, y_train)
print(f"Best score: {search.best_score_:.4f}")
print(f"Best params: {search.best_params_}")
```

### Common Hyperparameter Grids

#### Random Forest
```python
param_grid = {
    'model__n_estimators': [100, 200, 300, 500],
    'model__max_depth': [None, 10, 20, 30],
    'model__min_samples_split': [2, 5, 10],
    'model__min_samples_leaf': [1, 2, 4],
    'model__max_features': ['sqrt', 'log2', 0.5],
}
```

#### Gradient Boosting
```python
param_grid = {
    'model__n_estimators': [100, 200, 300],
    'model__learning_rate': [0.01, 0.05, 0.1, 0.2],
    'model__max_depth': [3, 4, 5, 6],
    'model__subsample': [0.7, 0.8, 0.9, 1.0],
    'model__min_samples_leaf': [1, 2, 5],
}
```

#### SVM
```python
param_grid = {
    'model__C': np.logspace(-2, 3, 6),
    'model__gamma': np.logspace(-4, 1, 6),
    'model__kernel': ['rbf', 'linear'],
}
```

#### Logistic Regression
```python
param_grid = {
    'model__C': np.logspace(-4, 4, 9),
    'model__penalty': ['l1', 'l2'],
    'model__solver': ['liblinear', 'saga'],
}
```

#### KMeans
```python
# No GridSearchCV — use manual loop with silhouette scores
param_grid_manual = {
    'n_clusters': range(2, 15),
}
```

---

## Model Comparison

### Compare Multiple Algorithms

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', random_state=42),
    'KNN': KNeighborsClassifier(n_neighbors=5),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

for name, model in models.items():
    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring='f1_weighted')
    results[name] = scores
    print(f"{name:25s}  F1: {scores.mean():.4f} ± {scores.std():.4f}")
```

### Visualization: Box Plot Comparison

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
ax.boxplot(results.values(), labels=results.keys())
ax.set_ylabel('F1 Score (CV)')
ax.set_title('Model Comparison')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('model_comparison.png', dpi=150)
plt.close()
```

---

## Learning Curves and Diagnostics

### Learning Curve (Overfitting vs Underfitting)

```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, val_scores = learning_curve(
    pipeline, X_train, y_train,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5, scoring='f1_weighted', n_jobs=-1
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(train_sizes, train_scores.mean(axis=1), 'o-', label='Training')
ax.plot(train_sizes, val_scores.mean(axis=1), 'o-', label='Validation')
ax.fill_between(train_sizes,
    train_scores.mean(axis=1) - train_scores.std(axis=1),
    train_scores.mean(axis=1) + train_scores.std(axis=1), alpha=0.1)
ax.fill_between(train_sizes,
    val_scores.mean(axis=1) - val_scores.std(axis=1),
    val_scores.mean(axis=1) + val_scores.std(axis=1), alpha=0.1)
ax.set_xlabel('Training Set Size')
ax.set_ylabel('Score')
ax.set_title('Learning Curve')
ax.legend()
plt.tight_layout()
plt.savefig('learning_curve.png', dpi=150)
plt.close()
```

Interpretation:
- **High train, low val** → Overfitting (reduce model complexity, add regularization, get more data)
- **Both low** → Underfitting (increase model complexity, add features)
- **Both high, converging** → Good fit

### Validation Curve (Single Hyperparameter Effect)

```python
from sklearn.model_selection import validation_curve

param_range = [1, 5, 10, 20, 50, 100]
train_scores, val_scores = validation_curve(
    pipeline, X_train, y_train,
    param_name='model__max_depth',
    param_range=param_range,
    cv=5, scoring='f1_weighted', n_jobs=-1
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(param_range, train_scores.mean(axis=1), 'o-', label='Training')
ax.plot(param_range, val_scores.mean(axis=1), 'o-', label='Validation')
ax.set_xlabel('max_depth')
ax.set_ylabel('Score')
ax.set_title('Validation Curve')
ax.legend()
plt.tight_layout()
plt.savefig('validation_curve.png', dpi=150)
plt.close()
```

---

## Model Persistence

### Saving and Loading Models

```python
import joblib

# Save the entire pipeline (includes preprocessing + model)
joblib.dump(pipeline, 'model_pipeline.pkl')

# Load
loaded_pipeline = joblib.load('model_pipeline.pkl')

# Predict with loaded model
predictions = loaded_pipeline.predict(new_data)
```

### Saving Metadata

Always save model metadata alongside the model file:

```python
import json
from datetime import datetime

metadata = {
    'model_type': type(pipeline.named_steps['model']).__name__,
    'best_params': search.best_params_ if hasattr(search, 'best_params_') else {},
    'cv_score': float(search.best_score_) if hasattr(search, 'best_score_') else None,
    'test_metrics': {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'f1_weighted': float(f1_score(y_test, y_pred, average='weighted')),
    },
    'feature_columns': list(X.columns),
    'target_column': target_col,
    'training_samples': len(X_train),
    'sklearn_version': sklearn.__version__,
    'trained_at': datetime.now().isoformat(),
}

with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
```

---

## Scoring Reference Table

### Classification Scoring Strings

| String | Function | Notes |
|---|---|---|
| `'accuracy'` | accuracy_score | Default for classifiers |
| `'balanced_accuracy'` | balanced_accuracy_score | Adjusts for imbalanced classes |
| `'f1'` | f1_score (binary) | Binary classification only |
| `'f1_weighted'` | f1_score(average='weighted') | Multi-class, weighted by class support |
| `'f1_macro'` | f1_score(average='macro') | Multi-class, equal weight per class |
| `'precision_weighted'` | precision_score(average='weighted') | |
| `'recall_weighted'` | recall_score(average='weighted') | |
| `'roc_auc'` | roc_auc_score | Binary, requires predict_proba |
| `'roc_auc_ovr'` | roc_auc_score(multi_class='ovr') | Multi-class AUC |
| `'log_loss'` | log_loss | Cross-entropy loss |

### Regression Scoring Strings

| String | Function | Notes |
|---|---|---|
| `'r2'` | r2_score | Default for regressors |
| `'neg_mean_absolute_error'` | -MAE | Negated (higher is better for sklearn) |
| `'neg_mean_squared_error'` | -MSE | Negated |
| `'neg_root_mean_squared_error'` | -RMSE | Negated |
| `'neg_mean_absolute_percentage_error'` | -MAPE | Negated |
| `'neg_median_absolute_error'` | -MedianAE | Negated, robust |

Regression metrics are negated because sklearn's scoring convention requires higher = better. Extract actual value with `-scores.mean()`.

### Clustering Scoring

Clustering metrics are not directly usable with `cross_val_score` since there's no target. Evaluate manually:

```python
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

sil = silhouette_score(X_scaled, labels)
ch = calinski_harabasz_score(X_scaled, labels)
db = davies_bouldin_score(X_scaled, labels)
```
