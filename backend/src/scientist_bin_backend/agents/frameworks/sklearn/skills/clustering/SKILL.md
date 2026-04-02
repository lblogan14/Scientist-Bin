---
name: clustering
description: Scikit-learn clustering skill for unsupervised learning tasks
---

# Clustering Skill

This skill handles unsupervised clustering tasks using scikit-learn.

## Capabilities

- Partitional clustering (KMeans, MiniBatchKMeans)
- Density-based clustering (DBSCAN, HDBSCAN, OPTICS)
- Hierarchical clustering (AgglomerativeClustering)
- Cluster validation (Silhouette score, Calinski-Harabasz, Davies-Bouldin)
- Optimal cluster number selection (elbow method, silhouette analysis)
- Dimensionality reduction for visualization (PCA, t-SNE)

## When to Use

Use this skill when there are no labels and the objective involves grouping similar data points. Examples:

- "Segment customers into groups based on purchasing behavior"
- "Find natural groupings in the dataset"
- "Identify clusters of similar documents"
- "Group sensor readings into operational modes"

## Approach

1. Load and inspect the dataset (automated EDA)
2. Scale features appropriately (StandardScaler for distance-based methods)
3. Determine optimal number of clusters (elbow, silhouette)
4. Try multiple algorithms (KMeans, DBSCAN, AgglomerativeClustering)
5. Evaluate cluster quality with internal metrics
6. Visualize clusters using PCA/t-SNE reduction
7. Profile clusters (mean feature values per cluster)
8. Generate final report with cluster descriptions
