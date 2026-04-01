"""Analyzer node — examines the training request and produces an analysis."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.central.prompts.templates import ANALYZER_PROMPT
from scientist_bin_backend.agents.central.states import CentralState
from scientist_bin_backend.utils.llm import get_agent_model


async def analyze(state: CentralState) -> dict:
    """Analyze the user's training request."""
    llm = get_agent_model("central")
    prompt = ANALYZER_PROMPT.format(
        objective=state["objective"],
        data_description=state.get("data_description", ""),
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"messages": [response]}
