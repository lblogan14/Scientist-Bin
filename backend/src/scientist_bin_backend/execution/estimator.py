"""Duration estimation and dynamic timeout adjustment.

Estimates training time based on dataset characteristics and model complexity,
then adjusts subprocess timeouts accordingly. Uses a simple heuristic model
that improves as more experiments are tracked.
"""

from __future__ import annotations

import math


def estimate_training_duration(
    n_rows: int,
    n_cols: int,
    n_algorithms: int = 1,
    use_grid_search: bool = True,
    grid_size: int = 10,
    n_cv_folds: int = 5,
) -> float:
    """Estimate training duration in seconds based on dataset and experiment params.

    Uses empirical scaling laws for sklearn:
    - Linear models: O(n_rows * n_cols)
    - Tree models: O(n_rows * n_cols * log(n_rows))
    - GridSearchCV multiplier: grid_size * n_cv_folds

    Returns estimated seconds. Always includes a 20% buffer.
    """
    # Base time per model fit (empirical for sklearn on modern hardware)
    # ~0.001s per 1000 rows for linear, ~0.005s for tree-based
    base_time_per_fit = 0.001 * (n_rows / 1000) * (n_cols / 10)

    # Tree-based models scale with log(n_rows)
    tree_multiplier = 1 + math.log2(max(n_rows, 2)) / 10

    # Average between linear and tree-based (we'll train both)
    avg_fit_time = base_time_per_fit * (1 + tree_multiplier) / 2

    # Grid search multiplier
    search_multiplier = grid_size * n_cv_folds if use_grid_search else n_cv_folds

    # Total for all algorithms
    total = avg_fit_time * search_multiplier * n_algorithms

    # Minimum 10 seconds, add 20% buffer
    return max(10.0, total * 1.2)


def compute_dynamic_timeout(
    estimated_duration: float,
    min_timeout: int = 60,
    max_timeout: int = 1800,
    buffer_factor: float = 3.0,
) -> int:
    """Compute a dynamic timeout from the estimated duration.

    Uses buffer_factor to account for estimation error.
    Clamped to [min_timeout, max_timeout].
    """
    timeout = int(estimated_duration * buffer_factor)
    return max(min_timeout, min(timeout, max_timeout))


def suggest_data_subset_size(
    n_rows: int,
    target_duration_seconds: float = 30.0,
    n_cols: int = 10,
    n_algorithms: int = 3,
) -> int | None:
    """Suggest a data subset size for progressive training.

    Returns None if the full dataset is already fast enough.
    Returns a row count for the initial subset otherwise.

    Progressive training strategy:
    1. Start with subset (fast feedback)
    2. If results are promising, scale to full dataset
    3. Saves compute on obviously bad configurations
    """
    full_estimate = estimate_training_duration(n_rows, n_cols, n_algorithms)

    if full_estimate <= target_duration_seconds:
        return None  # Full dataset is fast enough

    # Find subset size that fits target duration
    # Rough inverse: subset_rows = n_rows * (target / estimate)^(1/0.7)
    # Using 0.7 because sklearn scales sub-linearly with data size
    ratio = target_duration_seconds / full_estimate
    subset_rows = int(n_rows * (ratio ** (1 / 0.7)))

    # Minimum 100 rows, at least 10% of data
    return max(100, max(subset_rows, n_rows // 10))
