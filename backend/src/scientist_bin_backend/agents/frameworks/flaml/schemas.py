"""Pydantic schemas for FLAML-specific structured outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FlamlStrategyPlan(BaseModel):
    """FLAML-specific execution plan parameters extracted from the plan agent."""

    time_budget: int = Field(default=120, description="Time budget in seconds for AutoML search")
    estimator_list: list[str] = Field(
        default_factory=list,
        description="Estimators to try (empty = FLAML default for the task)",
    )
    metric: str | None = Field(
        default=None, description="Optimization metric override (e.g. 'accuracy', 'rmse', 'mape')"
    )
    ts_period: int | None = Field(
        default=None, description="Forecast horizon for time series tasks"
    )
    eval_method: str = Field(
        default="auto", description="Evaluation method: 'auto', 'cv', or 'holdout'"
    )
    n_splits: int = Field(default=5, description="Number of CV folds")
