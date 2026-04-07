# Preprocessing & Pipelines Reference

Comprehensive guide for data preprocessing and sklearn Pipeline construction.

## Table of Contents
1. [Data Loading Patterns](#data-loading-patterns)
2. [Missing Value Handling](#missing-value-handling)
3. [Feature Scaling](#feature-scaling)
4. [Categorical Encoding](#categorical-encoding)
5. [Feature Engineering](#feature-engineering)
6. [Pipeline Construction](#pipeline-construction)
7. [Dimensionality Reduction](#dimensionality-reduction)

---

## Data Loading Patterns

```python
import pandas as pd
import numpy as np

# CSV
df = pd.read_csv('data.csv')

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# With type hints
df = pd.read_csv('data.csv', dtype={'id': str, 'amount': float}, parse_dates=['date'])

# Inspect immediately
print(f"Shape: {df.shape}")
print(f"Dtypes:\n{df.dtypes}\n")
print(f"Missing:\n{df.isnull().sum()}\n")
print(f"Duplicates: {df.duplicated().sum()}")
print(df.describe(include='all'))
```

### Identifying Feature Types

```python
numeric_features = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_features = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
datetime_features = df.select_dtypes(include=['datetime64']).columns.tolist()

# Remove the target from feature lists
target_col = 'target'
for lst in [numeric_features, categorical_features]:
    if target_col in lst:
        lst.remove(target_col)
```

---

## Missing Value Handling

### Strategy Selection

| Data Type | Strategy | When to Use |
|---|---|---|
| Numeric, symmetric dist | `strategy='mean'` | Default for normal-ish distributions |
| Numeric, skewed dist | `strategy='median'` | Robust to outliers (preferred default) |
| Categorical | `strategy='most_frequent'` | Fills with mode |
| Any | `strategy='constant'` | When missing has meaning (e.g., fill_value=0) |
| Numeric, complex patterns | KNNImputer | When missingness relates to other features |
| Numeric, many columns | IterativeImputer | Multivariate imputation (experimental) |

### Implementation

```python
from sklearn.impute import SimpleImputer, KNNImputer

# Simple
num_imputer = SimpleImputer(strategy='median')
cat_imputer = SimpleImputer(strategy='most_frequent')

# KNN-based (uses distance to k nearest complete neighbors)
knn_imputer = KNNImputer(n_neighbors=5, weights='distance')

# Iterative (MICE-like)
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
iter_imputer = IterativeImputer(max_iter=10, random_state=42)
```

### When to Drop

Drop rows/columns when:
- A column has > 50% missing values (usually not informative)
- A row has the majority of columns missing
- The target variable is missing

```python
# Drop columns with > 50% missing
threshold = 0.5
cols_to_drop = df.columns[df.isnull().mean() > threshold].tolist()
df = df.drop(columns=cols_to_drop)

# Drop rows where target is missing
df = df.dropna(subset=[target_col])
```

---

## Feature Scaling

### Which Scaler to Use

| Scaler | Effect | When to Use |
|---|---|---|
| StandardScaler | Zero mean, unit variance | Default for most models (SVM, KNN, PCA, linear) |
| MinMaxScaler | Scales to [0, 1] | When bounded range needed, neural nets |
| RobustScaler | Uses median/IQR | When dataset contains outliers |
| MaxAbsScaler | Scales by max absolute value | Sparse data (preserves zeros) |
| Normalizer | Unit norm per sample | Text/TF-IDF, cosine similarity |

### Which Models Need Scaling

**Require scaling**: SVM, KNN, KMeans, DBSCAN, PCA, Logistic Regression (with regularization), Neural Networks, Linear Regression (with regularization)

**Do NOT require scaling**: Decision Trees, Random Forest, Gradient Boosting, Naive Bayes, all tree-based models

Even for tree-based models, scaling doesn't hurt — so when in doubt, scale.

### Implementation

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Use same fit as training
```

---

## Categorical Encoding

### Encoding Strategy

| Method | When to Use | Example |
|---|---|---|
| OneHotEncoder | Nominal (no order): color, city | [red, blue] → [[1,0], [0,1]] |
| OrdinalEncoder | Ordinal (has order): low/med/high | [low, med, high] → [0, 1, 2] |
| LabelEncoder | Target variable only | [cat, dog, fish] → [0, 1, 2] |
| TargetEncoder | High cardinality categoricals | Encodes by mean target per category |

### Implementation

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, LabelEncoder

# OneHot — use in pipelines
ohe = OneHotEncoder(
    handle_unknown='ignore',    # Handles unseen categories at predict time
    sparse_output=False,        # Returns dense array
    drop='if_binary'            # Drops one column for binary features
)

# Ordinal — specify order explicitly
oe = OrdinalEncoder(
    categories=[['low', 'medium', 'high']],  # Explicit order
    handle_unknown='use_encoded_value',
    unknown_value=-1
)

# Target encoder (sklearn >= 1.3)
from sklearn.preprocessing import TargetEncoder
te = TargetEncoder(smooth='auto')
```

### High Cardinality Categoricals

When a categorical column has many unique values (e.g., zip codes, user IDs):
1. **TargetEncoder**: Replaces categories with smoothed mean of target
2. **Frequency encoding**: Replace with count/frequency of each category
3. **Group rare categories**: Combine categories with < N occurrences into "other"

```python
# Frequency encoding (manual)
freq_map = df['city'].value_counts(normalize=True).to_dict()
df['city_freq'] = df['city'].map(freq_map)

# Group rare
threshold = 50
value_counts = df['city'].value_counts()
rare_cats = value_counts[value_counts < threshold].index
df['city_grouped'] = df['city'].replace(rare_cats, 'other')
```

---

## Feature Engineering

### Datetime Features

```python
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek
df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
df['quarter'] = df['date'].dt.quarter
df['days_since_ref'] = (df['date'] - df['date'].min()).dt.days
```

### Interaction Features

```python
from sklearn.preprocessing import PolynomialFeatures

poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_interactions = poly.fit_transform(X_numeric)
```

### Binning / Discretization

```python
from sklearn.preprocessing import KBinsDiscretizer

binner = KBinsDiscretizer(n_bins=5, encode='ordinal', strategy='quantile')
X_binned = binner.fit_transform(X[['age']])
```

### Log Transform (for right-skewed features)

```python
from sklearn.preprocessing import FunctionTransformer

log_transformer = FunctionTransformer(np.log1p, inverse_func=np.expm1)
```

### Feature Selection

```python
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif

# Statistical test (ANOVA F-value for classification)
selector = SelectKBest(score_func=f_classif, k=20)

# Mutual information (captures nonlinear relationships)
selector = SelectKBest(score_func=mutual_info_classif, k=20)

# Model-based selection
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestClassifier

selector = SelectFromModel(
    RandomForestClassifier(n_estimators=100, random_state=42),
    threshold='median'
)
```

---

## Pipeline Construction

### Why Pipelines Are Mandatory

Pipelines prevent data leakage: if you fit a scaler on the full dataset before splitting, information from the test set leaks into training. Pipelines ensure all transformations are fit only on training data during cross-validation.

### Basic Pipeline

```python
from sklearn.pipeline import Pipeline, make_pipeline

# Named steps (explicit)
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])

# Shorthand (auto-named by class)
pipeline = make_pipeline(StandardScaler(), LogisticRegression())
```

### ColumnTransformer for Mixed Types

The most common real-world pattern — different preprocessing for numeric vs categorical:

```python
from sklearn.compose import ColumnTransformer

preprocessor = ColumnTransformer(
    transformers=[
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), numeric_features),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]), categorical_features)
    ],
    remainder='drop'  # 'drop' (default), 'passthrough', or a transformer
)

# Full pipeline
full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestClassifier(random_state=42))
])
```

### FeatureUnion for Parallel Transformations

Combine outputs from multiple transformers side by side:

```python
from sklearn.pipeline import FeatureUnion
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest

combined = FeatureUnion([
    ('pca', PCA(n_components=5)),
    ('select_best', SelectKBest(k=10))
])

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('features', combined),
    ('model', SVC())
])
```

### Accessing Pipeline Components

```python
# Get feature names after transformation
feature_names = full_pipeline.named_steps['preprocessor'].get_feature_names_out()

# Access the model inside the pipeline
model = full_pipeline.named_steps['model']

# Set parameters with __ syntax
full_pipeline.set_params(model__n_estimators=300)
```

### Custom Transformer

```python
from sklearn.base import BaseEstimator, TransformerMixin

class LogTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns=None):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        if self.columns:
            X[self.columns] = np.log1p(X[self.columns])
        else:
            X = np.log1p(X)
        return X
```

---

## Dimensionality Reduction

### PCA (Principal Component Analysis)

```python
from sklearn.decomposition import PCA

# Keep fixed number of components
pca = PCA(n_components=10, random_state=42)

# Keep enough to explain 95% variance
pca = PCA(n_components=0.95, random_state=42)

# Inspect explained variance
pca.fit(X_scaled)
print(f"Components: {pca.n_components_}")
print(f"Explained variance: {pca.explained_variance_ratio_}")
print(f"Cumulative: {np.cumsum(pca.explained_variance_ratio_)}")
```

### t-SNE (Visualization Only)

```python
from sklearn.manifold import TSNE

tsne = TSNE(n_components=2, perplexity=30, random_state=42)
X_tsne = tsne.fit_transform(X_scaled)
# Use only for 2D/3D visualization — not as input to a model
```

### UMAP (if installed)

```python
# pip install umap-learn
import umap

reducer = umap.UMAP(n_components=2, random_state=42)
X_umap = reducer.fit_transform(X_scaled)
```

### Truncated SVD (for sparse data)

```python
from sklearn.decomposition import TruncatedSVD

svd = TruncatedSVD(n_components=50, random_state=42)
X_reduced = svd.fit_transform(X_sparse)
```
