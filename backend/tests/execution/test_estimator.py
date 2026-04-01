"""Tests for the duration estimator."""

from scientist_bin_backend.execution.estimator import (
    compute_dynamic_timeout,
    estimate_training_duration,
    suggest_data_subset_size,
)


def test_estimate_small_dataset():
    """Small dataset should estimate under 30 seconds."""
    duration = estimate_training_duration(n_rows=150, n_cols=4, n_algorithms=3)
    assert duration >= 10.0  # minimum
    assert duration < 60.0  # should be fast for iris-sized data


def test_estimate_large_dataset():
    """Large dataset should estimate significantly longer."""
    small = estimate_training_duration(n_rows=100, n_cols=10)
    large = estimate_training_duration(n_rows=100_000, n_cols=10)
    assert large > small


def test_estimate_more_algorithms_takes_longer():
    # Use large enough dataset to avoid hitting the 10s floor
    one = estimate_training_duration(n_rows=50000, n_cols=20, n_algorithms=1)
    five = estimate_training_duration(n_rows=50000, n_cols=20, n_algorithms=5)
    assert five > one


def test_dynamic_timeout_bounds():
    timeout = compute_dynamic_timeout(10.0, min_timeout=60, max_timeout=1800)
    assert timeout >= 60
    assert timeout <= 1800


def test_dynamic_timeout_large_estimate():
    timeout = compute_dynamic_timeout(1000.0, max_timeout=1800)
    assert timeout == 1800  # clamped to max


def test_suggest_subset_none_for_small_data():
    """Small datasets should not need subsetting."""
    result = suggest_data_subset_size(n_rows=150, n_cols=4, n_algorithms=3)
    assert result is None


def test_suggest_subset_for_large_data():
    """Large datasets should get a subset suggestion."""
    result = suggest_data_subset_size(
        n_rows=1_000_000, n_cols=100, n_algorithms=5, target_duration_seconds=30.0
    )
    assert result is not None
    assert result < 1_000_000
    assert result >= 100  # minimum
