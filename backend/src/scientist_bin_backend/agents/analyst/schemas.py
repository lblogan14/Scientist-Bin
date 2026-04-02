"""Pydantic schemas for the analyst agent structured outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CleaningAction(BaseModel):
    """A single data cleaning action taken on the dataset."""

    action: str = Field(
        ..., description="Type of cleaning action (e.g. 'impute', 'drop', 'encode')"
    )
    column: str | None = Field(
        default=None, description="Column the action applies to, or None for row-level"
    )
    description: str = Field(..., description="Human-readable description of the action")


class SplitStatistics(BaseModel):
    """Statistics about the train/val/test split."""

    train_samples: int = Field(..., description="Number of training samples")
    val_samples: int = Field(..., description="Number of validation samples")
    test_samples: int = Field(..., description="Number of test samples")
    train_ratio: float = Field(..., description="Training set ratio")
    val_ratio: float = Field(..., description="Validation set ratio")
    test_ratio: float = Field(..., description="Test set ratio")


class AnalysisReport(BaseModel):
    """Structured analysis report produced by the analyst agent."""

    dataset_summary: str = Field(..., description="High-level summary of the dataset")
    shape: list[int] = Field(..., description="Dataset shape [rows, cols]")
    columns: list[str] = Field(default_factory=list, description="Column names")
    data_quality_issues: list[str] = Field(
        default_factory=list, description="Data quality issues found"
    )
    cleaning_actions: list[CleaningAction] = Field(
        default_factory=list, description="Cleaning actions performed"
    )
    split_statistics: SplitStatistics | None = Field(
        default=None, description="Train/val/test split statistics"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for modeling"
    )


class ValidatedClassification(BaseModel):
    """Result of validating/refining the upstream classification against actual data.

    Used when the central orchestrator's TaskAnalysis is available. The analyst
    validates the upstream hypothesis using real data evidence and either confirms,
    refines, or overrides the classification.
    """

    problem_type: Literal[
        "classification",
        "regression",
        "clustering",
        "dimensionality_reduction",
        "anomaly_detection",
    ] = Field(..., description="The validated ML problem type")
    confidence: Literal["confirmed", "refined", "overridden"] = Field(
        ...,
        description=(
            "'confirmed': upstream is correct. "
            "'refined': approximately right but adjusted (e.g. binary vs multiclass). "
            "'overridden': upstream is wrong based on data evidence."
        ),
    )
    reasoning: str = Field(
        ..., description="Evidence from the actual data supporting this classification"
    )
    target_column_guess: str | None = Field(
        default=None, description="Best guess for the target column name"
    )
    suggested_metrics: list[str] = Field(
        default_factory=list, description="Appropriate evaluation metrics"
    )
    upstream_disagreement: str | None = Field(
        default=None,
        description="If refined or overridden, what the upstream got wrong and why",
    )
