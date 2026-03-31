"""Pydantic models for the central agent's structured I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    """Incoming training request from a user or the CLI."""

    objective: str = Field(..., description="What the user wants to achieve")
    data_description: str = Field(default="", description="Description of the dataset")
    framework_preference: str | None = Field(
        default=None,
        description="Optional framework preference (e.g. 'sklearn', 'pytorch')",
    )


class FrameworkSelection(BaseModel):
    """Structured output from the routing step."""

    framework: str = Field(..., description="Selected framework identifier")
    reasoning: str = Field(..., description="Why this framework was chosen")


class AgentResponse(BaseModel):
    """Final response produced by the agent pipeline."""

    framework: str
    plan: str | None = None
    generated_code: str | None = None
    evaluation_results: dict | None = None
    status: str = "completed"
