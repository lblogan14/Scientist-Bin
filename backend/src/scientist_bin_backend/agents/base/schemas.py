"""Shared Pydantic schemas for structured LLM outputs across all framework subagents."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Phase 0: Problem Classification
# ---------------------------------------------------------------------------


class ProblemClassification(BaseModel):
    """Structured output from the classify_problem node."""

    problem_type: Literal[
        "classification",
        "regression",
        "clustering",
        "dimensionality_reduction",
        "anomaly_detection",
    ]
    reasoning: str = Field(..., description="Why this problem type was chosen")
    target_column_guess: str | None = Field(
        default=None, description="Best guess for the target column name"
    )
    suggested_metrics: list[str] = Field(
        default_factory=list, description="Appropriate evaluation metrics"
    )


# ---------------------------------------------------------------------------
# Phase 2: Strategy Planning
# ---------------------------------------------------------------------------


class AlgorithmCandidate(BaseModel):
    """A candidate algorithm with its hyperparameter search space."""

    algorithm_name: str = Field(..., description="Full sklearn class name or common name")
    rationale: str = Field(..., description="Why this algorithm is a good fit")
    hyperparameter_grid: dict[str, list] = Field(
        default_factory=dict, description="Param name -> values to search"
    )
    priority: int = Field(default=1, description="1 = try first (simplest), higher = more complex")


class PreprocessingStep(BaseModel):
    """A data preprocessing step."""

    step_name: str
    description: str
    applies_to: list[str] = Field(
        default_factory=list,
        description="Column names, or 'numeric'/'categorical' for groups",
    )


class FeatureEngineeringStep(BaseModel):
    """A feature engineering operation."""

    step_name: str
    description: str
    new_features: list[str] = Field(
        default_factory=list, description="Names of new features to create"
    )


class StrategyPlan(BaseModel):
    """Structured output from the plan_strategy node."""

    approach_summary: str = Field(..., description="High-level approach description")
    candidate_algorithms: list[AlgorithmCandidate] = Field(
        ..., description="Algorithms to try, ordered by priority (simplest first)"
    )
    preprocessing_steps: list[PreprocessingStep] = Field(
        default_factory=list, description="Data preprocessing pipeline steps"
    )
    feature_engineering_steps: list[FeatureEngineeringStep] = Field(
        default_factory=list, description="Feature engineering operations"
    )
    cv_strategy: str = Field(default="5-fold stratified", description="Cross-validation strategy")
    success_criteria: dict[str, float] = Field(
        default_factory=dict, description="metric_name -> threshold to consider success"
    )


# ---------------------------------------------------------------------------
# Phase 4: Results Analysis
# ---------------------------------------------------------------------------


class IterationDecision(BaseModel):
    """LLM decision after analyzing experiment results."""

    action: Literal[
        "accept",
        "refine_params",
        "try_new_algo",
        "fix_error",
        "feature_engineer",
        "abort",
    ]
    reasoning: str = Field(..., description="Why this action was chosen")
    refinement_instructions: str | None = Field(
        default=None, description="Specific guidance for the next iteration"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in this decision"
    )


# ---------------------------------------------------------------------------
# Finalization
# ---------------------------------------------------------------------------


class FinalReport(BaseModel):
    """Structured final output of the ML pipeline."""

    best_model: str = Field(..., description="Name of the best-performing model")
    best_metrics: dict[str, float] = Field(
        default_factory=dict, description="Metrics of the best model"
    )
    total_iterations: int = Field(default=1)
    interpretation: str = Field(..., description="Human-readable interpretation of results")
    recommendations: list[str] = Field(
        default_factory=list, description="Suggestions for further improvement"
    )
