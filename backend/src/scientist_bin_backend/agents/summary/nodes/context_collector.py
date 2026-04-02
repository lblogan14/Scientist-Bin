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
    all_cluster_stats: dict[str, dict] = {}

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

        cluster_stats = record.get("cluster_stats")
        if cluster_stats:
            all_cluster_stats[algo] = cluster_stats

    # Include test-set diagnostics if available
    if test_diagnostics:
        if test_diagnostics.get("confusion_matrix"):
            # Store under a special key so we know it's test-set
            all_confusion_matrices["__test__"] = test_diagnostics["confusion_matrix"]
        if test_diagnostics.get("residual_stats"):
            all_residual_stats["__test__"] = test_diagnostics["residual_stats"]
        if test_diagnostics.get("cluster_stats"):
            all_cluster_stats["__test__"] = test_diagnostics["cluster_stats"]

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
        "cluster_stats": all_cluster_stats,
        "test_metrics": test_metrics,
        "test_diagnostics": test_diagnostics,
        "algorithms_tried": algorithms_tried,
        "total_training_time": total_training_time,
        "total_iterations": len(experiment_history),
    }

    logger.info(
        "Collected context: %d experiments, %d algorithms, "
        "cv_folds=%d, importances=%d, confusion=%d, residuals=%d, clusters=%d",
        len(experiment_history),
        len(algorithms_tried),
        len(all_cv_fold_scores),
        len(all_feature_importances),
        len(all_confusion_matrices),
        len(all_residual_stats),
        len(all_cluster_stats),
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
