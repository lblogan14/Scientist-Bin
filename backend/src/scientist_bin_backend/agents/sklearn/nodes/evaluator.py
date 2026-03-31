"""Evaluator node — reviews generated code and decides whether to retry."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END

from scientist_bin_backend.agents.sklearn.prompts.templates import EVALUATOR_PROMPT
from scientist_bin_backend.agents.sklearn.schemas import EvaluationResult
from scientist_bin_backend.agents.sklearn.states import SklearnState
from scientist_bin_backend.utils.llm import get_chat_model


async def evaluate(state: SklearnState) -> dict:
    """Evaluate the generated code for correctness and completeness."""
    llm = get_chat_model()
    structured_llm = llm.with_structured_output(EvaluationResult)
    prompt = EVALUATOR_PROMPT.format(
        objective=state["objective"],
        code=state.get("generated_code", ""),
    )
    result: EvaluationResult = await structured_llm.ainvoke(
        [HumanMessage(content=prompt)]
    )

    status_msg = "Code passed evaluation." if result.success else "Code needs improvement."
    return {
        "evaluation_results": result.model_dump(),
        "retry_count": state.get("retry_count", 0) + 1,
        "messages": [HumanMessage(content=status_msg)],
    }


def should_retry(state: SklearnState) -> str:
    """Routing function: retry code generation or finish."""
    eval_results = state.get("evaluation_results")
    if eval_results and eval_results.get("success"):
        return END
    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return END
    return "generate_code"
