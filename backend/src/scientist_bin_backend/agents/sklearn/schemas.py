"""Pydantic models for the sklearn subagent's structured I/O."""

from __future__ import annotations

from pydantic import Field

from scientist_bin_backend.agents.base.schemas import (
    AlgorithmCandidate,
    FeatureEngineeringStep,
    PreprocessingStep,
    StrategyPlan,
)


class SklearnStrategyPlan(StrategyPlan):
    """Sklearn-specific strategy plan with pipeline details."""

    pipeline_structure: str = Field(
        default="", description="Description of the sklearn Pipeline structure"
    )
    use_grid_search: bool = Field(
        default=True, description="Whether to use GridSearchCV or RandomizedSearchCV"
    )


# Re-export base schemas for convenience
__all__ = [
    "AlgorithmCandidate",
    "FeatureEngineeringStep",
    "PreprocessingStep",
    "SklearnStrategyPlan",
    "StrategyPlan",
]
