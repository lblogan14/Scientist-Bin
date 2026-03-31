"""Iteration budget system for controlling experiment loops."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class IterationBudget:
    """Multi-dimensional budget for experiment iteration."""

    max_iterations: int = 5
    max_wall_time_seconds: int = 1800  # 30 minutes
    max_runs: int = 20
    target_metric: str | None = None
    target_threshold: float | None = None
    min_improvement: float = 0.01
    patience: int = 3  # Stop after N iterations without improvement


@dataclass
class BudgetTracker:
    """Track budget consumption and enforce stopping rules.

    All stopping decisions are deterministic -- no LLM calls needed.
    """

    budget: IterationBudget
    start_time: float = field(default_factory=time.monotonic)
    iterations: int = 0
    runs: int = 0
    best_metric_value: float | None = None
    iterations_without_improvement: int = 0

    def record_iteration(
        self,
        metrics: dict[str, float] | None = None,
        num_runs: int = 1,
    ) -> None:
        """Record a completed iteration and update tracking."""
        self.iterations += 1
        self.runs += num_runs

        if metrics and self.budget.target_metric and self.budget.target_metric in metrics:
            current_value = metrics[self.budget.target_metric]
            if self.best_metric_value is None:
                self.best_metric_value = current_value
                self.iterations_without_improvement = 0
            elif current_value - self.best_metric_value >= self.budget.min_improvement:
                self.best_metric_value = current_value
                self.iterations_without_improvement = 0
            else:
                self.iterations_without_improvement += 1
        else:
            # No target metric to track improvement on
            self.iterations_without_improvement = 0

    def should_stop(self) -> tuple[bool, str]:
        """Check if any budget constraint is violated.

        Returns (should_stop, reason).
        """
        elapsed = time.monotonic() - self.start_time

        if self.iterations >= self.budget.max_iterations:
            return True, f"Max iterations reached ({self.budget.max_iterations})"

        if elapsed >= self.budget.max_wall_time_seconds:
            return True, f"Wall time budget exceeded ({self.budget.max_wall_time_seconds}s)"

        if self.runs >= self.budget.max_runs:
            return True, f"Max runs reached ({self.budget.max_runs})"

        if (
            self.budget.target_metric
            and self.budget.target_threshold is not None
            and self.best_metric_value is not None
            and self.best_metric_value >= self.budget.target_threshold
        ):
            return True, (
                f"Target threshold met: {self.budget.target_metric}"
                f"={self.best_metric_value:.4f} >= {self.budget.target_threshold}"
            )

        if self.iterations_without_improvement >= self.budget.patience:
            return True, (
                f"No improvement for {self.budget.patience} iterations "
                f"(best {self.budget.target_metric}={self.best_metric_value:.4f})"
            )

        return False, ""

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self.start_time

    @property
    def remaining_iterations(self) -> int:
        return max(0, self.budget.max_iterations - self.iterations)
