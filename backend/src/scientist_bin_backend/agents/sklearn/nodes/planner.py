"""Planner node — researches and plans the sklearn approach."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.sklearn.prompts.templates import PLANNER_PROMPT
from scientist_bin_backend.agents.sklearn.schemas import SklearnPlan
from scientist_bin_backend.agents.sklearn.states import SklearnState
from scientist_bin_backend.utils.llm import get_chat_model, search_with_gemini


async def plan(state: SklearnState) -> dict:
    """Research best practices via Google Search, then produce a structured plan."""
    objective = state["objective"]
    data_description = state.get("data_description", "")

    # Search for relevant best practices
    search_query = f"scikit-learn best practices for: {objective} {data_description}"
    search_results = await search_with_gemini(search_query)

    # Generate structured plan
    llm = get_chat_model()
    structured_llm = llm.with_structured_output(SklearnPlan)
    prompt = PLANNER_PROMPT.format(
        objective=objective,
        data_description=data_description,
        search_context=search_results,
    )
    sklearn_plan: SklearnPlan = await structured_llm.ainvoke(
        [HumanMessage(content=prompt)]
    )

    plan_text = (
        f"Approach: {sklearn_plan.approach}\n"
        f"Algorithms: {', '.join(sklearn_plan.algorithms)}\n"
        f"Preprocessing: {', '.join(sklearn_plan.preprocessing_steps)}\n"
        f"Metrics: {', '.join(sklearn_plan.evaluation_metrics)}"
    )

    return {
        "plan": plan_text,
        "search_results": search_results,
        "messages": [HumanMessage(content=f"Plan created:\n{plan_text}")],
    }
