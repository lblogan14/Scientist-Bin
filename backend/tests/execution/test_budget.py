"""Tests for the iteration budget system."""

import time

from scientist_bin_backend.execution.budget import BudgetTracker, IterationBudget


def test_budget_tracker_max_iterations():
    budget = IterationBudget(max_iterations=3)
    tracker = BudgetTracker(budget=budget)

    tracker.record_iteration()
    assert tracker.should_stop() == (False, "")

    tracker.record_iteration()
    assert tracker.should_stop() == (False, "")

    tracker.record_iteration()
    stop, reason = tracker.should_stop()
    assert stop is True
    assert "Max iterations" in reason


def test_budget_tracker_target_threshold():
    budget = IterationBudget(
        max_iterations=10,
        target_metric="accuracy",
        target_threshold=0.95,
    )
    tracker = BudgetTracker(budget=budget)

    tracker.record_iteration(metrics={"accuracy": 0.80})
    assert tracker.should_stop() == (False, "")

    tracker.record_iteration(metrics={"accuracy": 0.96})
    stop, reason = tracker.should_stop()
    assert stop is True
    assert "Target threshold met" in reason


def test_budget_tracker_patience():
    budget = IterationBudget(
        max_iterations=10,
        target_metric="accuracy",
        target_threshold=0.99,
        patience=2,
        min_improvement=0.01,
    )
    tracker = BudgetTracker(budget=budget)

    tracker.record_iteration(metrics={"accuracy": 0.90})
    assert tracker.should_stop() == (False, "")

    # No improvement
    tracker.record_iteration(metrics={"accuracy": 0.90})
    assert tracker.should_stop() == (False, "")

    # Still no improvement -> patience exhausted
    tracker.record_iteration(metrics={"accuracy": 0.905})
    stop, reason = tracker.should_stop()
    assert stop is True
    assert "No improvement" in reason


def test_budget_tracker_wall_time():
    budget = IterationBudget(max_wall_time_seconds=0)  # immediate timeout
    tracker = BudgetTracker(budget=budget, start_time=time.monotonic() - 1)
    stop, reason = tracker.should_stop()
    assert stop is True
    assert "Wall time" in reason


def test_budget_tracker_remaining_iterations():
    budget = IterationBudget(max_iterations=5)
    tracker = BudgetTracker(budget=budget)
    assert tracker.remaining_iterations == 5

    tracker.record_iteration()
    tracker.record_iteration()
    assert tracker.remaining_iterations == 3


def test_budget_tracker_max_runs():
    budget = IterationBudget(max_runs=2, max_iterations=10)
    tracker = BudgetTracker(budget=budget)

    tracker.record_iteration(num_runs=1)
    assert tracker.should_stop() == (False, "")

    tracker.record_iteration(num_runs=1)
    stop, reason = tracker.should_stop()
    assert stop is True
    assert "Max runs" in reason
