# Classification Reference

Comprehensive guide for building classification models with scikit-learn.

## Table of Contents
1. [Algorithm Catalog](#algorithm-catalog)
2. [Algorithm Selection Decision Tree](#algorithm-selection-decision-tree)
3. [Implementation Patterns](#implementation-patterns)
4. [Evaluation Metrics](#evaluation-metrics)
5. [Handling Class Imbalance](#handling-class-imbalance)
6. [Multi-class and Multi-label](#multi-class-and-multi-label)

---

## Algorithm Catalog

### Logistic Regression
Best for: binary and multi-class problems with roughly linear decision boundaries.

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    C=1.0,                    # Inverse regularization strength (smaller = stronger regularization)
    penalty='l2',             # 'l1', 'l2', 'elasticnet', None
    solver='lbfgs',           # 'lbfgs' (default), 'liblinear' (small data), 'saga' (large data)
    max_iter=1000,            # Increase if convergence warnings appear
    class_weight='balanced',  # Use when classes are imbalanced
    random_state=42
)
```

Key hyperparameters to tune: `C` (try `np.logspace(-4, 4, 9)`), `penalty`.

### Support Vector Machines (SVM)

Best for: high-dimensional data, clear margin of separation, small-to-medium datasets.

```python
from sklearn.svm import SVC

model = SVC(
    kernel='rbf',       # 'linear', 'poly', 'rbf', 'sigmoid'
    C=1.0,              # Regularization (higher = less regularization)
    gamma='scale',      # Kernel coefficient: 'scale', 'auto', or float
    probability=True,   # Enable if you need predict_proba (slower training)
    class_weight='balanced',
    random_state=42
)
```

For large datasets, use `LinearSVC` or `SGDClassifier(loss='hinge')` instead — `SVC` with RBF kernel does not scale well past ~10k samples.

Key hyperparameters to tune: `C` (try `np.logspace(-2, 3, 6)`), `gamma` (try `np.logspace(-4, 1, 6)`).

### Random Forest

Best for: general-purpose classification, feature importance, minimal preprocessing needed.

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=200,         # Number of trees
    max_depth=None,           # None = fully grown trees
    min_samples_split=2,      # Minimum samples to split a node
    min_samples_leaf=1,       # Minimum samples in a leaf
    max_features='sqrt',      # Features considered per split
    class_weight='balanced',
    n_jobs=-1,
    random_state=42
)
```

Key hyperparameters to tune: `n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`.

### Gradient Boosting

Best for: highest accuracy on structured/tabular data.

```python
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,        # Shrinkage: smaller = more trees needed but often better
    max_depth=3,              # Usually 3-8 for boosting
    subsample=0.8,            # Stochastic gradient boosting
    random_state=42
)
```

For larger datasets, prefer `HistGradientBoostingClassifier` which is much faster and handles missing values natively:

```python
from sklearn.ensemble import HistGradientBoostingClassifier

model = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.1,
    max_depth=None,           # Uses max_leaf_nodes instead
    max_leaf_nodes=31,
    random_state=42
)
```

### K-Nearest Neighbors (KNN)

Best for: simple problems, few features, instance-based reasoning.

```python
from sklearn.neighbors import KNeighborsClassifier

model = KNeighborsClassifier(
    n_neighbors=5,
    weights='distance',   # 'uniform' or 'distance'
    metric='minkowski',   # 'euclidean', 'manhattan', etc.
    n_jobs=-1
)
```

Requires feature scaling. Does not scale well to high dimensions (curse of dimensionality).

### Naive Bayes

Best for: text classification, very fast training, baseline models.

```python
from sklearn.naive_bayes import GaussianNB      # Continuous features
from sklearn.naive_bayes import MultinomialNB    # Count data / text (TF-IDF)
from sklearn.naive_bayes import BernoulliNB      # Binary features

model = GaussianNB()
# or
model = MultinomialNB(alpha=1.0)  # Laplace smoothing
```

### Decision Tree

Best for: interpretability, rule extraction, visualization.

```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(
    max_depth=5,              # Prevent overfitting
    min_samples_split=10,
    min_samples_leaf=5,
    class_weight='balanced',
    random_state=42
)
```

Prone to overfitting — prefer Random Forest or Gradient Boosting for production.

---

## Algorithm Selection Decision Tree

```
Is interpretability the top priority?
├── Yes → LogisticRegression (linear) or DecisionTree (nonlinear)
└── No
    ├── Is the dataset > 100k rows?
    │   ├── Yes → HistGradientBoostingClassifier or SGDClassifier
    │   └── No
    │       ├── Are features mostly text / very sparse?
    │       │   ├── Yes → MultinomialNB or LinearSVC
    │       │   └── No
    │       │       ├── Need best accuracy?
    │       │       │   ├── Yes → GradientBoostingClassifier (tune carefully)
    │       │       │   └── No → RandomForestClassifier (robust default)
    │       │       └── Few features + small data?
    │       │           └── KNeighborsClassifier or SVC(kernel='rbf')
```

**Default recommendation**: Start with `RandomForestClassifier` as baseline, then try `GradientBoostingClassifier` or `HistGradientBoostingClassifier` if more accuracy is needed.

---

## Implementation Patterns

### Binary Classification Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
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
    ('classifier', RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1))
])

# Cross-validation score
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='f1_weighted')
print(f"CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Final evaluation
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
y_proba = pipeline.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred))
print(f"ROC AUC: {roc_auc_score(y_test, y_proba):.4f}")
```

### Multi-class Classification

Same pattern, but use `scoring='f1_weighted'` or `scoring='accuracy'`, and `roc_auc_score(y_test, y_proba, multi_class='ovr')` for AUC.

---

## Evaluation Metrics

### Which Metric to Use

| Scenario | Primary Metric | Why |
|---|---|---|
| Balanced classes, simple | Accuracy | Easy to understand |
| Imbalanced classes | F1-score (weighted or macro) | Balances precision and recall |
| Cost of false positives is high | Precision | Minimize false alarms |
| Cost of false negatives is high | Recall | Minimize missed cases |
| Need ranking / threshold tuning | ROC AUC | Threshold-independent |
| Probability calibration matters | Log loss (cross-entropy) | Penalizes confident wrong predictions |

### Computing All Key Metrics

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

# Text report
print(classification_report(y_test, y_pred, digits=4))

# Individual metrics
print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred, average='weighted'):.4f}")
print(f"Recall:    {recall_score(y_test, y_pred, average='weighted'):.4f}")
print(f"F1:        {f1_score(y_test, y_pred, average='weighted'):.4f}")

# Confusion matrix visualization
fig, ax = plt.subplots(figsize=(8, 6))
ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax, cmap='Blues')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150)
plt.close()
```

### ROC Curve

```python
from sklearn.metrics import RocCurveDisplay

fig, ax = plt.subplots(figsize=(8, 6))
RocCurveDisplay.from_estimator(pipeline, X_test, y_test, ax=ax)
plt.title('ROC Curve')
plt.tight_layout()
plt.savefig('roc_curve.png', dpi=150)
plt.close()
```

---

## Handling Class Imbalance

### Option 1: Class Weights (simplest)
Most sklearn classifiers accept `class_weight='balanced'` which adjusts sample weights inversely proportional to class frequency.

### Option 2: Resampling
```python
# Oversampling with SMOTE (requires imbalanced-learn)
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

pipeline = ImbPipeline([
    ('preprocessor', preprocessor),
    ('smote', SMOTE(random_state=42)),
    ('classifier', RandomForestClassifier(random_state=42))
])
```

### Option 3: Threshold Adjustment
```python
y_proba = pipeline.predict_proba(X_test)[:, 1]
threshold = 0.3  # Lower threshold to catch more positives
y_pred_adjusted = (y_proba >= threshold).astype(int)
```

---

## Multi-class and Multi-label

### Multi-class (mutually exclusive classes)
Most sklearn classifiers handle multi-class natively. Use `average='weighted'` for metrics.

### Multi-label (multiple labels per sample)
```python
from sklearn.multioutput import MultiOutputClassifier

multi_model = MultiOutputClassifier(RandomForestClassifier(random_state=42))
multi_model.fit(X_train, y_train_multilabel)
```

### One-vs-Rest wrapper
```python
from sklearn.multiclass import OneVsRestClassifier

ovr_model = OneVsRestClassifier(SVC(kernel='linear'))
ovr_model.fit(X_train, y_train)
```
