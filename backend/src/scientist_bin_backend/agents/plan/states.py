"""State schema for the plan agent."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class PlanState(TypedDict, total=False):
    """Typed state for the plan agent graph.

    Tracks the full lifecycle: query rewriting, web research,
    execution plan generation, and human-in-the-loop plan approval.
    """

    # -- Message history (LangGraph convention) --
    messages: Annotated[list, add_messages]

    # -- Input --
    objective: str
    data_description: str
    data_file_path: str | None
    framework_preference: str | None

    # -- Upstream context (from central analyzer and analyst agent) --
    task_analysis: dict | None
    analysis_report: str | None
    data_profile: dict | None
    problem_type: str | None

    # -- Query rewriting --
    rewritten_query: str | None

    # -- Research --
    search_results: str | None

    # -- Plan generation --
    execution_plan: dict | None
    plan_markdown: str | None

    # -- Human-in-the-loop --
    human_feedback: str | None
    plan_approved: bool
    revision_count: int
    max_revisions: int

    # -- Control --
    experiment_id: str | None
    error: str | None
