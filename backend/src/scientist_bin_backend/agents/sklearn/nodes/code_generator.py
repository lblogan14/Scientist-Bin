"""Code generator node — produces runnable sklearn code from the plan."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.sklearn.prompts.templates import CODE_GENERATOR_PROMPT
from scientist_bin_backend.agents.sklearn.states import SklearnState
from scientist_bin_backend.agents.sklearn.utils import strip_code_fences
from scientist_bin_backend.utils.llm import get_chat_model


async def generate_code(state: SklearnState) -> dict:
    """Generate sklearn training code based on the plan."""
    retry_context = ""
    if state.get("evaluation_results") and not state["evaluation_results"].get("success"):
        errors = state["evaluation_results"].get("errors", [])
        suggestions = state["evaluation_results"].get("suggestions", [])
        retry_context = (
            "Previous attempt had issues:\n"
            f"Errors: {errors}\n"
            f"Suggestions: {suggestions}\n"
            "Please fix these issues in the new version."
        )

    llm = get_chat_model()
    prompt = CODE_GENERATOR_PROMPT.format(
        objective=state["objective"],
        data_description=state.get("data_description", ""),
        plan=state.get("plan", ""),
        retry_context=retry_context,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    code = strip_code_fences(response.content)

    return {
        "generated_code": code,
        "messages": [HumanMessage(content="Code generated successfully.")],
    }
