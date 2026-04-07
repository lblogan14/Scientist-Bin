"""Router node — selects the appropriate framework subagent."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.central.prompts import ROUTER_PROMPT
from scientist_bin_backend.agents.central.schemas import FrameworkSelection
from scientist_bin_backend.agents.central.states import CentralState
from scientist_bin_backend.utils.llm import get_agent_model

# Framework registry: maps framework name -> fully-qualified agent class path.
# Adding a new framework requires one entry here + implementing the agent.
FRAMEWORK_REGISTRY: dict[str, str] = {
    "sklearn": "scientist_bin_backend.agents.frameworks.sklearn.agent.SklearnAgent",
    "flaml": "scientist_bin_backend.agents.frameworks.flaml.agent.FlamlAgent",
    # "pytorch": "scientist_bin_backend.agents.frameworks.pytorch.agent.PytorchAgent",
}

SUPPORTED_FRAMEWORKS = set(FRAMEWORK_REGISTRY.keys())


async def route(state: CentralState) -> dict:
    """Select the best framework and record the decision.

    Uses a deterministic path first (user preference or task_analysis
    suggestion), falling back to an LLM call for ambiguous cases.
    """
    preference = state.get("framework_preference")

    # 1. If user explicitly requested a supported framework, honour it
    if preference and preference.lower() in SUPPORTED_FRAMEWORKS:
        return {
            "selected_framework": preference.lower(),
            "messages": [HumanMessage(content=f"Using user-requested framework: {preference}")],
        }

    # 2. Deterministic: pick first supported framework from task_analysis
    task_analysis = state.get("task_analysis") or {}
    suggested = task_analysis.get("suggested_frameworks", [])
    for fw in suggested:
        if fw.lower() in SUPPORTED_FRAMEWORKS:
            return {
                "selected_framework": fw.lower(),
                "messages": [HumanMessage(content=f"Selected {fw} based on task analysis")],
            }

    # 3. Fallback: ask the LLM to decide
    llm = get_agent_model("central")
    structured_llm = llm.with_structured_output(FrameworkSelection)

    analysis_text = json.dumps(task_analysis, indent=2) if task_analysis else ""
    prompt = ROUTER_PROMPT.format(
        analysis=analysis_text,
        objective=state["objective"],
        framework_preference=preference or "none",
    )
    selection: FrameworkSelection = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    msg = f"Selected {selection.framework}: {selection.reasoning}"
    return {
        "selected_framework": selection.framework,
        "messages": [HumanMessage(content=msg)],
    }


def select_subagent(state: CentralState) -> str:
    """Routing function for conditional edges — returns the next node name."""
    framework = (state.get("selected_framework") or "").lower()
    if framework in SUPPORTED_FRAMEWORKS:
        return framework
    # Fallback to first supported framework rather than silently ending the pipeline
    return next(iter(SUPPORTED_FRAMEWORKS))
