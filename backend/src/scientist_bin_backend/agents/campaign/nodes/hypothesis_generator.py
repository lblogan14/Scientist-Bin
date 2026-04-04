"""Hypothesis generation node — produces ranked hypotheses for the next campaign iteration."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.campaign.prompts import HYPOTHESIS_GENERATION_PROMPT
from scientist_bin_backend.agents.campaign.schemas import HypothesisList
from scientist_bin_backend.utils.llm import get_agent_model

logger = logging.getLogger(__name__)


async def generate_hypotheses(state: dict) -> dict:
    """Generate a ranked list of hypotheses based on the objective and past findings.

    Uses an LLM with structured output to produce :class:`HypothesisList`,
    then serialises the hypotheses into the state for downstream consumption.

    Returns:
        Partial state update with ``hypotheses`` (list[dict]).
    """
    llm = get_agent_model("campaign")
    structured_llm = llm.with_structured_output(HypothesisList)

    completed = state.get("completed_experiments", [])
    findings = state.get("findings_summary", "No experiments completed yet.")

    # Build a concise summary of completed experiments for the prompt
    experiments_summary = (
        "None yet."
        if not completed
        else json.dumps(
            [
                {
                    "iteration": exp.get("iteration"),
                    "algorithm": exp.get("algorithm"),
                    "metrics": exp.get("metrics"),
                    "notes": exp.get("notes", ""),
                }
                for exp in completed
            ],
            indent=2,
        )
    )

    prompt = HYPOTHESIS_GENERATION_PROMPT.format(
        objective=state["objective"],
        data_profile=state.get("data_description", "Not available."),
        findings_summary=findings,
        completed_experiments=experiments_summary,
    )

    result: HypothesisList = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    hypotheses = [h.model_dump() for h in result.hypotheses]
    logger.info(
        "Generated %d hypotheses for iteration %d",
        len(hypotheses),
        state.get("current_iteration", 0),
    )

    return {
        "hypotheses": hypotheses,
        "messages": [
            HumanMessage(
                content=(
                    f"Generated {len(hypotheses)} hypotheses. "
                    f"Top: {hypotheses[0]['description'] if hypotheses else 'none'}"
                )
            )
        ],
    }
