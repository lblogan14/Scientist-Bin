"""State schema for the scikit-learn subagent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class SklearnState(TypedDict):
    """Typed state passed through the sklearn subagent graph."""

    messages: Annotated[list, add_messages]
    objective: str
    data_description: str
    plan: str | None
    search_results: str | None
    generated_code: str | None
    evaluation_results: dict | None
    retry_count: int
    max_retries: int
    error: str | None
