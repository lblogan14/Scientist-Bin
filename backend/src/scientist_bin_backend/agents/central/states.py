"""State schema for the central orchestrator agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class CentralState(TypedDict):
    """Typed state passed through the central agent graph."""

    messages: Annotated[list, add_messages]
    objective: str
    data_description: str
    framework_preference: str | None
    selected_framework: str | None
    agent_response: dict | None
    error: str | None
