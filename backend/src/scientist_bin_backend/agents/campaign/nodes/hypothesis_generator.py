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
    When available, queries the ``FindingsStore`` for similar past findings
    to enrich the prompt context.

    Returns:
        Partial state update with ``hypotheses`` (list[dict]).
    """
    llm = get_agent_model("campaign")
    structured_llm = llm.with_structured_output(HypothesisList)

    completed = state.get("completed_experiments", [])
    findings = state.get("findings_summary", "No experiments completed yet.")

    # Query FindingsStore for cross-campaign learnings (optional)
    store_context = ""
    try:
        from scientist_bin_backend.memory.findings_store import FindingsStore

        store = FindingsStore()
        similar = store.query_similar(state["objective"])
        if similar:
            store_lines = []
            for f in similar:
                store_lines.append(f"- {f.get('text', '')} (distance: {f.get('distance', '?')})")
            store_context = "\n\n## Cross-Campaign Findings (from memory)\n" + "\n".join(
                store_lines
            )
    except Exception:
        logger.debug("FindingsStore not available — skipping", exc_info=True)

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

    # Append store context to findings if available
    enriched_findings = findings
    if store_context:
        enriched_findings = findings + store_context

    prompt = HYPOTHESIS_GENERATION_PROMPT.format(
        objective=state["objective"],
        data_profile=state.get("data_description", "Not available."),
        findings_summary=enriched_findings,
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
