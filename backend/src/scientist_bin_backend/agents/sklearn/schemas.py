"""Pydantic models for the sklearn subagent's structured I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SklearnPlan(BaseModel):
    """Structured plan produced by the planner node."""

    approach: str = Field(..., description="High-level approach description")
    algorithms: list[str] = Field(default_factory=list, description="Algorithms to try")
    preprocessing_steps: list[str] = Field(
        default_factory=list, description="Data preprocessing steps"
    )
    evaluation_metrics: list[str] = Field(
        default_factory=list, description="Metrics to evaluate the model"
    )


class CodeGenerationResult(BaseModel):
    """Output of the code generation step."""

    code: str = Field(..., description="Complete, runnable Python/sklearn code")
    explanation: str = Field(default="", description="Brief explanation of the code")


class EvaluationResult(BaseModel):
    """Output of the code evaluation step."""

    success: bool = Field(..., description="Whether the code is correct and complete")
    metrics: dict | None = Field(default=None, description="Predicted/estimated metrics")
    errors: list[str] | None = Field(default=None, description="Issues found")
    suggestions: list[str] | None = Field(
        default=None, description="Improvement suggestions"
    )
