# Clustering Reference

Comprehensive guide for building clustering models with scikit-learn.

## Table of Contents
1. [Algorithm Catalog](#algorithm-catalog)
2. [Algorithm Selection Decision Tree](#algorithm-selection-decision-tree)
3. [Implementation Patterns](#implementation-patterns)
4. [Evaluation Metrics](#evaluation-metrics)
5. [Determining Optimal Cluster Count](#determining-optimal-cluster-count)
6. [Visualization Techniques](#visualization-techniques)

---

## Algorithm Catalog

### KMeans

Best for: well-separated, roughly spherical clusters of similar size when k is known or estimable.

```python
from sklearn.cluster import KMeans

model = KMeans(
    n_clusters=5,
    init='k-means++',      # Smart initialization (default)
    n_init='auto',          # Number of random initializations
    max_iter=300,
    random_state=42
)
```

Requirements: features must be scaled. Sensitive to outliers. Time complexity: O(n * k * iterations * features).

Key hyperparameter: `n_clusters` — use the Elbow Method or Silhouette Analysis to determine.

### MiniBatchKMeans

Best for: very large datasets where standard KMeans is too slow.

```python
from sklearn.cluster import MiniBatchKMeans

model = MiniBatchKMeans(
    n_clusters=5,
    batch_size=1024,
    random_state=42
)
```

Trades some accuracy for significantly faster training. Results are close to KMeans for large n.

### DBSCAN

Best for: discovering clusters of arbitrary shape, automatic noise detection, unknown number of clusters.

```python
from sklearn.cluster import DBSCAN

model = DBSCAN(
    eps=0.5,             # Maximum distance between two samples in the same neighborhood
    min_samples=5,       # Minimum points to form a dense region (core point)
    metric='euclidean',
    n_jobs=-1
)
```

Does NOT require specifying number of clusters. Labels noise points as -1. Requires feature scaling.

Key hyperparameters:
- `eps` — too small = everything is noise; too large = one giant cluster. Use a k-distance plot to estimate.
- `min_samples` — rule of thumb: `2 * n_features` as a starting point.

### HDBSCAN

Best for: improved DBSCAN with varying density clusters, less parameter sensitivity.

```python
from sklearn.cluster import HDBSCAN

model = HDBSCAN(
    min_cluster_size=15,     # Minimum cluster membership
    min_samples=5,           # Core distance parameter
    cluster_selection_epsilon=0.0
)
```

Available in scikit-learn >= 1.3. More robust than DBSCAN — handles clusters of varying density.

### Agglomerative (Hierarchical) Clustering

Best for: when you want a hierarchy of clusters, dendrogram visualization.

```python
from sklearn.cluster import AgglomerativeClustering

model = AgglomerativeClustering(
    n_clusters=5,           # Or set to None and use distance_threshold
    linkage='ward',         # 'ward', 'complete', 'average', 'single'
    metric='euclidean'
)
```

Linkage options:
- `ward` — minimizes within-cluster variance (default, usually best)
- `complete` — max distance between clusters
- `average` — average distance between clusters
- `single` — min distance (can produce elongated clusters)

### Gaussian Mixture Model (GMM)

Best for: soft/probabilistic cluster assignments, ellipsoidal clusters.

```python
from sklearn.mixture import GaussianMixture

model = GaussianMixture(
    n_components=5,
    covariance_type='full',  # 'full', 'tied', 'diag', 'spherical'
    max_iter=200,
    random_state=42
)

model.fit(X_scaled)
labels = model.predict(X_scaled)
probabilities = model.predict_proba(X_scaled)  # Soft assignments
```

Supports BIC/AIC for model selection (number of components).

### Mean Shift

Best for: discovering clusters without specifying count, blob-like cluster shapes.

```python
from sklearn.cluster import MeanShift, estimate_bandwidth

bandwidth = estimate_bandwidth(X_scaled, quantile=0.2, n_samples=500)
model = MeanShift(bandwidth=bandwidth, bin_seeding=True)
```

Automatically determines number of clusters. Can be slow for large datasets.

### Spectral Clustering

Best for: non-convex clusters, graph-based grouping.

```python
from sklearn.cluster import SpectralClustering

model = SpectralClustering(
    n_clusters=5,
    affinity='rbf',       # 'rbf', 'nearest_neighbors', 'precomputed'
    gamma=1.0,
    random_state=42
)
```

Does not scale to very large datasets. No predict method — can only label training data.

---

## Algorithm Selection Decision Tree

```
Do you know the number of clusters?
├── Yes
│   ├── Need probabilistic memberships? → GaussianMixture
│   ├── Dataset > 100k samples? → MiniBatchKMeans
│   ├── Want hierarchy/dendrogram? → AgglomerativeClustering
│   ├── Non-convex cluster shapes? → SpectralClustering (if < 10k)
│   └── Default → KMeans
└── No
    ├── Expect noise/outliers? → DBSCAN or HDBSCAN
    ├── Clusters of varying density? → HDBSCAN
    ├── Want automatic discovery? → MeanShift or DBSCAN
    └── Default → HDBSCAN (most flexible)
```

**Default recommendation**: Start with `KMeans` (use Silhouette Analysis to pick k), then try `HDBSCAN` if clusters are non-spherical or noisy.

---

## Implementation Patterns

### Standard Clustering Pipeline

```python
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Prepare features — clustering uses no target variable
X = df.select_dtypes(include=['number']).copy()

# Pipeline (scaling is critical for distance-based clustering)
pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
    ('clusterer', KMeans(n_clusters=4, random_state=42))
])

# Fit and get labels
labels = pipeline.fit_predict(X)

# Evaluate
X_scaled = pipeline[:-1].transform(X)  # Get scaled features for scoring
sil_score = silhouette_score(X_scaled, labels)
print(f"Silhouette Score: {sil_score:.4f}")

# Add cluster labels back to DataFrame
df['cluster'] = labels
```

### Clustering with Categorical Features

Encode categoricals before clustering:

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

numeric_features = X.select_dtypes(include=['number']).columns.tolist()
categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()

preprocessor = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ]), numeric_features),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(sparse_output=False))
    ]), categorical_features)
])

X_processed = preprocessor.fit_transform(X)
```

### Dimensionality Reduction Before Clustering

For high-dimensional data, reduce dimensions first:

```python
from sklearn.decomposition import PCA

# Reduce to explained variance threshold
pca = PCA(n_components=0.95, random_state=42)  # Keep 95% variance
X_reduced = pca.fit_transform(X_scaled)
print(f"Reduced from {X_scaled.shape[1]} to {X_reduced.shape[1]} dimensions")

# Then cluster on reduced data
kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(X_reduced)
```

---

## Evaluation Metrics

### Without Ground Truth Labels (typical for clustering)

| Metric | Range | Best Value | Use Case |
|---|---|---|---|
| Silhouette Score | -1 to 1 | Higher is better | General-purpose, compares compactness vs separation |
| Calinski-Harabasz | > 0 | Higher is better | Favors convex, well-separated clusters |
| Davies-Bouldin | ≥ 0 | Lower is better | Measures avg cluster similarity |
| Inertia (KMeans) | ≥ 0 | Lower is better | Within-cluster sum of squares (Elbow Method) |

### With Ground Truth Labels (validation scenarios)

| Metric | Range | Best Value | Use Case |
|---|---|---|---|
| Adjusted Rand Index | -1 to 1 | 1.0 | Compares cluster assignments to true labels |
| Adjusted Mutual Info | 0 to 1 | 1.0 | Information-theoretic comparison |
| Homogeneity | 0 to 1 | 1.0 | Each cluster contains only one class |
| Completeness | 0 to 1 | 1.0 | All members of a class are in the same cluster |
| V-measure | 0 to 1 | 1.0 | Harmonic mean of homogeneity and completeness |

### Computing Evaluation Metrics

```python
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score,
    davies_bouldin_score, adjusted_rand_score,
    normalized_mutual_info_score
)

# Without ground truth
sil = silhouette_score(X_scaled, labels)
ch = calinski_harabasz_score(X_scaled, labels)
db = davies_bouldin_score(X_scaled, labels)

print(f"Silhouette Score:       {sil:.4f}")
print(f"Calinski-Harabasz:      {ch:.4f}")
print(f"Davies-Bouldin:         {db:.4f}")

# With ground truth (if available)
ari = adjusted_rand_score(y_true, labels)
nmi = normalized_mutual_info_score(y_true, labels)
print(f"Adjusted Rand Index:    {ari:.4f}")
print(f"Normalized Mutual Info: {nmi:.4f}")
```

---

## Determining Optimal Cluster Count

### Elbow Method (KMeans)

```python
import matplotlib.pyplot as plt

inertias = []
K_range = range(2, 11)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init='auto')
    km.fit(X_scaled)
    inertias.append(km.inertia_)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(K_range, inertias, 'bo-')
ax.set_xlabel('Number of Clusters (k)')
ax.set_ylabel('Inertia')
ax.set_title('Elbow Method')
plt.tight_layout()
plt.savefig('elbow_plot.png', dpi=150)
plt.close()
```

### Silhouette Analysis

```python
sil_scores = []
K_range = range(2, 11)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = km.fit_predict(X_scaled)
    sil_scores.append(silhouette_score(X_scaled, labels))

best_k = K_range[np.argmax(sil_scores)]
print(f"Best k by silhouette: {best_k}")

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(K_range, sil_scores, 'bo-')
ax.axvline(best_k, color='red', linestyle='--', label=f'Best k={best_k}')
ax.set_xlabel('Number of Clusters (k)')
ax.set_ylabel('Silhouette Score')
ax.set_title('Silhouette Analysis')
ax.legend()
plt.tight_layout()
plt.savefig('silhouette_analysis.png', dpi=150)
plt.close()
```

### BIC/AIC for Gaussian Mixture

```python
bics = []
aics = []
K_range = range(2, 11)

for k in K_range:
    gmm = GaussianMixture(n_components=k, random_state=42)
    gmm.fit(X_scaled)
    bics.append(gmm.bic(X_scaled))
    aics.append(gmm.aic(X_scaled))

best_k_bic = K_range[np.argmin(bics)]
print(f"Best k by BIC: {best_k_bic}")
```

### K-Distance Plot for DBSCAN eps

```python
from sklearn.neighbors import NearestNeighbors

k = 2 * X_scaled.shape[1]  # Rule of thumb: 2 * n_features
nn = NearestNeighbors(n_neighbors=k)
nn.fit(X_scaled)
distances, _ = nn.kneighbors(X_scaled)

# Sort k-th nearest neighbor distances
k_distances = np.sort(distances[:, -1])

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(k_distances)
ax.set_xlabel('Points (sorted by distance)')
ax.set_ylabel(f'{k}-th Nearest Neighbor Distance')
ax.set_title('K-Distance Plot (look for the "knee")')
plt.tight_layout()
plt.savefig('k_distance_plot.png', dpi=150)
plt.close()
```

---

## Visualization Techniques

### 2D Cluster Scatter Plot

```python
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Reduce to 2D for visualization
pca_2d = PCA(n_components=2, random_state=42)
X_2d = pca_2d.fit_transform(X_scaled)

fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap='viridis',
                     alpha=0.6, s=20, edgecolors='k', linewidths=0.3)
plt.colorbar(scatter, label='Cluster')
ax.set_xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]:.1%} variance)')
ax.set_ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]:.1%} variance)')
ax.set_title('Cluster Assignments (PCA 2D projection)')
plt.tight_layout()
plt.savefig('cluster_scatter.png', dpi=150)
plt.close()
```

### Cluster Profile (Radar/Summary Table)

```python
# Create a summary of cluster characteristics
cluster_summary = df.groupby('cluster').agg(['mean', 'median', 'count'])
print(cluster_summary)

# Or a more focused profile
for col in numeric_features:
    print(f"\n{col}:")
    print(df.groupby('cluster')[col].describe()[['mean', 'std', 'min', 'max']])
```

### Dendrogram (Hierarchical)

```python
from scipy.cluster.hierarchy import dendrogram, linkage

Z = linkage(X_scaled[:500], method='ward')  # Subsample if large

fig, ax = plt.subplots(figsize=(12, 6))
dendrogram(Z, truncate_mode='level', p=5, ax=ax)
ax.set_title('Hierarchical Clustering Dendrogram')
ax.set_xlabel('Sample Index (or Cluster Size)')
ax.set_ylabel('Distance')
plt.tight_layout()
plt.savefig('dendrogram.png', dpi=150)
plt.close()
```
