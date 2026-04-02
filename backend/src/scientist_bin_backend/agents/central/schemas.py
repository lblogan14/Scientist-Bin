"""Pydantic models for the central agent's structured I/O."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    """Incoming training request from a user or the CLI."""

    objective: str = Field(..., description="What the user wants to achieve")
    data_description: str = Field(default="", description="Description of the dataset")
    data_file_path: str | None = Field(default=None, description="Path to the dataset file")
    framework_preference: str | None = Field(
        default=None,
        description="Optional framework preference (e.g. 'sklearn', 'pytorch')",
    )
    auto_approve_plan: bool = Field(
        default=False,
        description="Skip human-in-the-loop plan review",
    )


class DataCharacteristics(BaseModel):
    """Inferred data characteristics from the objective and description."""

    estimated_features: str | None = Field(
        default=None, description="Estimated feature count, e.g. '4', '50+', 'unknown'"
    )
    estimated_samples: str | None = Field(
        default=None, description="Estimated sample count, e.g. '150', '10k+', 'unknown'"
    )
    data_types: list[str] = Field(
        default_factory=list, description="Inferred data types, e.g. ['numeric', 'categorical']"
    )
    target_column_hint: str | None = Field(default=None, description="Guessed target column name")
    has_missing_values: bool | None = Field(default=None)
    has_class_imbalance: bool | None = Field(default=None)


class TaskAnalysis(BaseModel):
    """Structured output from the central analyzer node.

    Provides a machine-readable analysis of the user's request that is
    passed downstream to close the knowledge gap between agents.
    """

    task_type: Literal[
        "classification",
        "regression",
        "clustering",
        "dimensionality_reduction",
        "anomaly_detection",
    ] = Field(..., description="The ML problem type")
    task_subtype: str | None = Field(
        default=None,
        description="E.g. 'binary', 'multiclass', 'multi-label', 'ordinal'",
    )
    data_characteristics: DataCharacteristics = Field(
        default_factory=DataCharacteristics,
        description="Inferred data characteristics",
    )
    recommended_approach: str = Field(
        ..., description="High-level approach recommendation (2-3 sentences)"
    )
    complexity_estimate: Literal["low", "medium", "high"] = Field(
        ..., description="Estimated task complexity"
    )
    key_considerations: list[str] = Field(
        default_factory=list,
        description="Issues to watch: class imbalance, missing data, high cardinality, etc.",
    )
    suggested_frameworks: list[str] = Field(
        default_factory=list,
        description="Frameworks ranked by suitability, e.g. ['sklearn', 'pytorch']",
    )


class FrameworkSelection(BaseModel):
    """Structured output from the routing step."""

    framework: str = Field(..., description="Selected framework identifier")
    reasoning: str = Field(..., description="Why this framework was chosen")


class AgentResponse(BaseModel):
    """Final response produced by the agent pipeline."""

    framework: str
    plan: dict | None = None
    plan_markdown: str | None = None
    generated_code: str | None = None
    evaluation_results: dict | None = None
    experiment_history: list[dict] = []
    data_profile: dict | None = None
    problem_type: str | None = None
    iterations: int = 0
    analysis_report: str | None = None
    summary_report: str | None = None
    best_model: str | None = None
    best_hyperparameters: dict | None = None
    test_metrics: dict | None = None
    test_diagnostics: dict | None = None
    selection_reasoning: str | None = None
    report_sections: dict | None = None
    status: str = "completed"
