"""Diagnostics computer node — pure computation, zero LLM calls.

Computes derived analytics from experiment data:
- CV stability analysis (fold-score variance per algorithm)
- Overfitting detection (train-val gap)
- Hyperparameter sensitivity ranking
- Pareto frontier (performance vs training time)
- Chart data for frontend visualisation
"""

from __future__ import annotations

import logging
from statistics import mean, stdev

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public node
# ---------------------------------------------------------------------------


async def compute_diagnostics(state: dict) -> dict:
    """Compute derived analytics from experiment data. Zero LLM calls."""
    ctx = state.get("summary_context") or {}
    problem_type = state.get("problem_type", "classification")

    cv_stability = _compute_cv_stability(ctx.get("cv_fold_scores", {}))
    overfit_analyses = _compute_overfit_analysis(ctx.get("experiment_history", []))
    sensitivities = _compute_hyperparam_sensitivity(ctx.get("cv_results", {}))
    pareto = _compute_pareto_frontier(ctx.get("experiment_history", []), problem_type)
    chart_data = _build_chart_data(ctx, problem_type)

    diagnostics = {
        "cv_stability": cv_stability,
        "overfit_analyses": overfit_analyses,
        "hyperparam_sensitivities": sensitivities,
        "pareto_optimal_models": pareto,
        "chart_data": chart_data,
    }

    logger.info(
        "Diagnostics computed: cv_stability=%d, overfit=%d, sensitivities=%d, pareto=%d",
        len(cv_stability),
        len(overfit_analyses),
        len(sensitivities),
        len(pareto),
    )

    return {
        "diagnostics": diagnostics,
        "messages": [HumanMessage(content="Diagnostics computed.")],
    }


# ---------------------------------------------------------------------------
# CV stability
# ---------------------------------------------------------------------------


def _compute_cv_stability(
    cv_fold_scores: dict[str, dict[str, list[float]]],
) -> list[dict]:
    """Compute mean, std, and CV coefficient for each algorithm+metric."""
    results: list[dict] = []

    for algo, metric_scores in cv_fold_scores.items():
        for metric_name, scores in metric_scores.items():
            if not scores or len(scores) < 2:
                continue

            m = mean(scores)
            s = stdev(scores)
            cv_coeff = s / m if m != 0 else 0.0

            results.append(
                {
                    "algorithm": algo,
                    "metric_name": metric_name,
                    "fold_scores": scores,
                    "mean": round(m, 6),
                    "std": round(s, 6),
                    "cv_coefficient_of_variation": round(cv_coeff, 6),
                    "min_fold": round(min(scores), 6),
                    "max_fold": round(max(scores), 6),
                }
            )

    return results


# ---------------------------------------------------------------------------
# Overfitting detection
# ---------------------------------------------------------------------------


def _compute_overfit_analysis(experiment_history: list[dict]) -> list[dict]:
    """Detect overfitting by comparing train vs val metrics."""
    results: list[dict] = []

    for record in experiment_history:
        algo = record.get("algorithm", "unknown")
        metrics = record.get("metrics", {})

        # Find matching train_/val_ metric pairs
        val_metrics = {k: v for k, v in metrics.items() if k.startswith("val_")}

        for val_key, val_value in val_metrics.items():
            base_name = val_key[4:]  # strip "val_"
            train_key = f"train_{base_name}"
            train_value = metrics.get(train_key)

            if train_value is None or not isinstance(val_value, (int, float)):
                continue
            if not isinstance(train_value, (int, float)):
                continue

            gap = train_value - val_value
            gap_pct = (gap / train_value * 100) if train_value != 0 else 0.0

            if abs(gap_pct) < 5:
                risk = "low"
            elif abs(gap_pct) < 15:
                risk = "moderate"
            else:
                risk = "high"

            results.append(
                {
                    "algorithm": algo,
                    "metric_name": base_name,
                    "train_value": round(train_value, 6),
                    "val_value": round(val_value, 6),
                    "gap": round(gap, 6),
                    "gap_percentage": round(gap_pct, 2),
                    "overfit_risk": risk,
                }
            )

    return results


# ---------------------------------------------------------------------------
# Hyperparameter sensitivity
# ---------------------------------------------------------------------------


def _compute_hyperparam_sensitivity(
    cv_results: dict[str, list[dict]],
) -> list[dict]:
    """Estimate which hyperparameters have the highest impact on score."""
    results: list[dict] = []

    for algo, top_n in cv_results.items():
        if not top_n or len(top_n) < 2:
            continue

        # Collect all param names seen
        param_names: set[str] = set()
        for entry in top_n:
            params = entry.get("params", {})
            param_names.update(params.keys())

        for param_name in param_names:
            # Group scores by param value
            scores_by_value: dict[str, list[float]] = {}
            for entry in top_n:
                value = entry.get("params", {}).get(param_name)
                if value is None:
                    continue
                key = str(value)
                scores_by_value.setdefault(key, []).append(entry.get("mean_score", 0))

            if len(scores_by_value) < 2:
                continue

            # Compute mean score per value, then score range
            mean_by_value = {k: mean(v) for k, v in scores_by_value.items()}
            score_range = max(mean_by_value.values()) - min(mean_by_value.values())
            best_value_key = max(mean_by_value, key=mean_by_value.get)  # type: ignore[arg-type]

            results.append(
                {
                    "algorithm": algo,
                    "param_name": param_name,
                    "score_range": round(score_range, 6),
                    "best_value": best_value_key,
                    "values_tried": len(scores_by_value),
                }
            )

    # Sort by score_range descending (most impactful first)
    results.sort(key=lambda x: x["score_range"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Pareto frontier
# ---------------------------------------------------------------------------


def _compute_pareto_frontier(experiment_history: list[dict], problem_type: str) -> list[str]:
    """Find Pareto-optimal models on primary metric vs training time."""
    if not experiment_history:
        return []

    # Pick primary metric heuristically
    primary_prefix = "val_"
    candidates: list[tuple[str, float, float]] = []

    for record in experiment_history:
        algo = record.get("algorithm", "unknown")
        metrics = record.get("metrics", {})
        time_s = record.get("training_time_seconds", 0)

        # Find the first val_ metric as proxy
        val_metric_value = None
        for k, v in metrics.items():
            if k.startswith(primary_prefix) and isinstance(v, (int, float)):
                val_metric_value = v
                break

        if val_metric_value is not None:
            candidates.append((algo, val_metric_value, time_s))

    if not candidates:
        return []

    # Pareto: a model is dominated if another has >= metric AND <= time
    pareto: list[str] = []
    for i, (algo_i, metric_i, time_i) in enumerate(candidates):
        dominated = False
        for j, (_, metric_j, time_j) in enumerate(candidates):
            if i == j:
                continue
            if metric_j >= metric_i and time_j <= time_i:
                if metric_j > metric_i or time_j < time_i:
                    dominated = True
                    break
        if not dominated:
            pareto.append(algo_i)

    return pareto


# ---------------------------------------------------------------------------
# Chart data (for frontend)
# ---------------------------------------------------------------------------


def _build_chart_data(ctx: dict, problem_type: str) -> dict:
    """Build JSON-serializable chart data for the frontend.

    Returns a plain dict matching the ChartData schema from
    ``agents.summary.schemas``.
    """
    charts: dict = {}

    experiment_history = ctx.get("experiment_history", [])

    # 1. Model comparison bar chart
    charts["model_comparison"] = [
        {
            "algorithm": r.get("algorithm", "unknown"),
            "training_time_seconds": r.get("training_time_seconds", 0),
            **{k: v for k, v in r.get("metrics", {}).items() if isinstance(v, (int, float))},
        }
        for r in experiment_history
    ]

    # 2. CV fold scores (box plot data)
    cv_fold_scores = ctx.get("cv_fold_scores", {})
    if cv_fold_scores:
        charts["cv_fold_scores"] = {}
        for algo, metric_scores in cv_fold_scores.items():
            charts["cv_fold_scores"][algo] = {}
            for metric_name, scores in metric_scores.items():
                if scores:
                    charts["cv_fold_scores"][algo][metric_name] = {
                        "scores": scores,
                        "mean": round(mean(scores), 6) if scores else 0,
                    }

    # 3. Feature importances (horizontal bar — top 15)
    feature_importances = ctx.get("feature_importances", {})
    if feature_importances:
        # Use the last algorithm's importances (typically the best)
        for algo in reversed(ctx.get("algorithms_tried", [])):
            if algo in feature_importances:
                charts["feature_importances"] = {
                    "algorithm": algo,
                    "features": feature_importances[algo][:15],
                }
                break

    # 4. Confusion matrices (heatmap)
    confusion_matrices = ctx.get("confusion_matrices", {})
    if confusion_matrices:
        charts["confusion_matrices"] = confusion_matrices

    # 5. Training time comparison
    charts["training_times"] = [
        {
            "algorithm": r.get("algorithm", "unknown"),
            "time_seconds": r.get("training_time_seconds", 0),
        }
        for r in experiment_history
    ]

    # 6. Hyperparameter search landscape
    cv_results = ctx.get("cv_results", {})
    if cv_results:
        charts["hyperparam_search"] = cv_results

    # 7. Residual stats (regression)
    residual_stats = ctx.get("residual_stats", {})
    if residual_stats:
        charts["residual_stats"] = residual_stats

    return charts
