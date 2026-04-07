"""Context collector node — normalizes all upstream data.

Zero LLM calls. Pure data transformation that extracts enriched diagnostic
fields from experiment_history records into organized collections.

This is the framework-agnostic adapter layer. For sklearn, it extracts
cv_fold_scores, feature_importances, etc. For a future pytorch agent, it
would extract epoch_metrics, learning_rate_schedule, gradient_norms, etc.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


async def collect_context(state: dict) -> dict:
    """Normalize all upstream data into a unified summary context.

    Extracts enriched diagnostic fields from experiment_history records
    and organizes them by algorithm for downstream computation.
    """
    experiment_history = state.get("experiment_history", [])
    test_metrics = state.get("test_metrics")
    test_diagnostics = state.get("test_diagnostics")

    # Extract enriched data keyed by algorithm
    all_cv_fold_scores: dict[str, dict] = {}
    all_cv_results: dict[str, list[dict]] = {}
    all_feature_importances: dict[str, list[dict]] = {}
    all_confusion_matrices: dict[str, dict] = {}
    all_residual_stats: dict[str, dict] = {}
    # Clustering-specific enrichment fields
    all_cluster_scatter: dict[str, list] = {}
    all_elbow_data: dict[str, list] = {}
    all_cluster_sizes: dict[str, list] = {}
    all_cluster_profiles: dict[str, list] = {}
    all_silhouette_per_sample: dict[str, list] = {}
    # FLAML / time series-specific enrichment fields
    all_forecast_data: dict[str, list] = {}
    all_trial_history: dict[str, list] = {}
    all_estimator_comparison: dict[str, list] = {}

    for record in experiment_history:
        algo = record.get("algorithm", "unknown")

        cv_fold_scores = record.get("cv_fold_scores")
        if cv_fold_scores:
            all_cv_fold_scores[algo] = cv_fold_scores

        cv_results_top_n = record.get("cv_results_top_n")
        if cv_results_top_n:
            all_cv_results[algo] = cv_results_top_n

        feature_importances = record.get("feature_importances")
        if feature_importances:
            all_feature_importances[algo] = feature_importances

        confusion_matrix = record.get("confusion_matrix")
        if confusion_matrix:
            all_confusion_matrices[algo] = confusion_matrix

        residual_stats = record.get("residual_stats")
        if residual_stats:
            all_residual_stats[algo] = residual_stats

        # Clustering-specific fields
        cluster_scatter = record.get("cluster_scatter")
        if cluster_scatter:
            all_cluster_scatter[algo] = cluster_scatter

        elbow_data = record.get("elbow_data")
        if elbow_data:
            all_elbow_data[algo] = elbow_data

        cluster_sizes = record.get("cluster_sizes")
        if cluster_sizes:
            all_cluster_sizes[algo] = cluster_sizes

        cluster_profiles = record.get("cluster_profiles")
        if cluster_profiles:
            all_cluster_profiles[algo] = cluster_profiles

        silhouette_per_sample = record.get("silhouette_per_sample")
        if silhouette_per_sample:
            all_silhouette_per_sample[algo] = silhouette_per_sample

        # FLAML / time series-specific fields
        forecast_data = record.get("forecast_data")
        if forecast_data:
            all_forecast_data[algo] = forecast_data

        trial_history = record.get("trial_history")
        if trial_history:
            all_trial_history[algo] = trial_history

        estimator_comparison = record.get("estimator_comparison")
        if estimator_comparison:
            all_estimator_comparison[algo] = estimator_comparison

    # Include test-set diagnostics if available
    if test_diagnostics:
        if test_diagnostics.get("confusion_matrix"):
            # Store under a special key so we know it's test-set
            all_confusion_matrices["__test__"] = test_diagnostics["confusion_matrix"]
        if test_diagnostics.get("residual_stats"):
            all_residual_stats["__test__"] = test_diagnostics["residual_stats"]
        if test_diagnostics.get("cluster_scatter"):
            all_cluster_scatter["__test__"] = test_diagnostics["cluster_scatter"]
        if test_diagnostics.get("cluster_profiles"):
            all_cluster_profiles["__test__"] = test_diagnostics["cluster_profiles"]

    # Compute aggregates
    algorithms_tried = []
    seen = set()
    for record in experiment_history:
        algo = record.get("algorithm", "unknown")
        if algo not in seen:
            algorithms_tried.append(algo)
            seen.add(algo)

    total_training_time = sum(
        record.get("training_time_seconds", 0) for record in experiment_history
    )

    summary_context = {
        "experiment_history": experiment_history,
        "cv_fold_scores": all_cv_fold_scores,
        "cv_results": all_cv_results,
        "feature_importances": all_feature_importances,
        "confusion_matrices": all_confusion_matrices,
        "residual_stats": all_residual_stats,
        "cluster_scatter": all_cluster_scatter,
        "elbow_data": all_elbow_data,
        "cluster_sizes": all_cluster_sizes,
        "cluster_profiles": all_cluster_profiles,
        "silhouette_per_sample": all_silhouette_per_sample,
        "forecast_data": all_forecast_data,
        "trial_history": all_trial_history,
        "estimator_comparison": all_estimator_comparison,
        "test_metrics": test_metrics,
        "test_diagnostics": test_diagnostics,
        "algorithms_tried": algorithms_tried,
        "total_training_time": total_training_time,
        "total_iterations": len(experiment_history),
    }

    logger.info(
        "Collected context: %d experiments, %d algorithms, "
        "cv_folds=%d, importances=%d, confusion=%d, residuals=%d, "
        "clusters=%d, elbow=%d",
        len(experiment_history),
        len(algorithms_tried),
        len(all_cv_fold_scores),
        len(all_feature_importances),
        len(all_confusion_matrices),
        len(all_residual_stats),
        len(all_cluster_scatter),
        len(all_elbow_data),
    )

    return {
        "summary_context": summary_context,
        "messages": [
            HumanMessage(
                content=(
                    f"Context collected: {len(experiment_history)} experiments, "
                    f"{len(algorithms_tried)} algorithms."
                )
            )
        ],
    }
