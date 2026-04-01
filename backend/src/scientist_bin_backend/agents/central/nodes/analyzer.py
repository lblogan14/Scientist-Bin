"""Analyzer node — examines the training request and produces structured analysis."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.central.prompts import ANALYZER_PROMPT
from scientist_bin_backend.agents.central.schemas import TaskAnalysis
from scientist_bin_backend.agents.central.states import CentralState
from scientist_bin_backend.utils.llm import get_agent_model


async def analyze(state: CentralState) -> dict:
    """Analyze the user's training request and produce a structured TaskAnalysis.

    Returns both the structured analysis dict and a summary message for logging.
    """
    llm = get_agent_model("central")
    structured_llm = llm.with_structured_output(TaskAnalysis)

    prompt = ANALYZER_PROMPT.format(
        objective=state["objective"],
        data_description=state.get("data_description", ""),
    )

    analysis: TaskAnalysis = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    summary_msg = (
        f"Task analysis: {analysis.task_type}"
        f" ({analysis.task_subtype or 'general'})"
        f" | Complexity: {analysis.complexity_estimate}"
        f" | Suggested: {', '.join(analysis.suggested_frameworks)}"
    )

    return {
        "task_analysis": analysis.model_dump(),
        "messages": [HumanMessage(content=summary_msg)],
    }
