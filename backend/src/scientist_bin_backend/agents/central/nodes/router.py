"""Router node — selects the appropriate framework subagent."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END

from scientist_bin_backend.agents.central.prompts.templates import ROUTER_PROMPT
from scientist_bin_backend.agents.central.schemas import FrameworkSelection
from scientist_bin_backend.agents.central.states import CentralState
from scientist_bin_backend.utils.llm import get_chat_model

SUPPORTED_FRAMEWORKS = {"sklearn"}


async def route(state: CentralState) -> dict:
    """Select the best framework and record the decision."""
    preference = state.get("framework_preference")

    # If user explicitly requested a supported framework, honour it
    if preference and preference.lower() in SUPPORTED_FRAMEWORKS:
        return {
            "selected_framework": preference.lower(),
            "messages": [
                HumanMessage(content=f"Using user-requested framework: {preference}")
            ],
        }

    # Otherwise, ask the LLM to decide
    analysis = ""
    if state.get("messages"):
        analysis = state["messages"][-1].content  # type: ignore[union-attr]

    llm = get_chat_model()
    structured_llm = llm.with_structured_output(FrameworkSelection)
    prompt = ROUTER_PROMPT.format(
        analysis=analysis,
        objective=state["objective"],
        framework_preference=preference or "none",
    )
    selection: FrameworkSelection = await structured_llm.ainvoke(
        [HumanMessage(content=prompt)]
    )

    msg = f"Selected {selection.framework}: {selection.reasoning}"
    return {
        "selected_framework": selection.framework,
        "messages": [HumanMessage(content=msg)],
    }


def select_subagent(state: CentralState) -> str:
    """Routing function for conditional edges — returns the subagent node name."""
    framework = (state.get("selected_framework") or "").lower()
    if framework in SUPPORTED_FRAMEWORKS:
        return framework
    return END
