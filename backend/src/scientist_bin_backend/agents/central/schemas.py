"""Pydantic models for the central agent's structured I/O."""

from __future__ import annotations

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
    status: str = "completed"
