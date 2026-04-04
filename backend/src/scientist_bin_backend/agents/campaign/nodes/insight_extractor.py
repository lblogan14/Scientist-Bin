"""Insight extraction node — distils generalizable learnings after each experiment."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.campaign.prompts import INSIGHT_EXTRACTION_PROMPT
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model

logger = logging.getLogger(__name__)


async def extract_insights(state: dict) -> dict:
    """Extract learnings from the latest experiment and update the findings memory.

    Uses an LLM to analyse the most recent experiment result in context of
    the existing findings memory, producing an updated summary.

    Returns:
        Partial state update with ``findings_summary`` (str).
    """
    llm = get_agent_model("campaign")

    completed = state.get("completed_experiments", [])
    if not completed:
        logger.warning("No completed experiments — skipping insight extraction")
        return {}

    latest = completed[-1]
    existing_findings = state.get("findings_summary", "No findings yet.")

    prompt = INSIGHT_EXTRACTION_PROMPT.format(
        objective=state["objective"],
        latest_result=json.dumps(latest, indent=2, default=str),
        findings_summary=existing_findings,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    updated_findings = extract_text_content(response.content)

    logger.info(
        "Updated findings memory after iteration %d (%d chars)",
        state.get("current_iteration", 0),
        len(updated_findings),
    )

    # Persist to FindingsStore for cross-campaign learning (optional)
    try:
        from scientist_bin_backend.memory.findings_store import FindingsStore

        experiment_id = latest.get("experiment_id", "")
        algorithm = latest.get("algorithm", "unknown")
        metrics = latest.get("metrics", {})
        if experiment_id:
            store = FindingsStore()
            store.add_finding(
                experiment_id=experiment_id,
                objective=state["objective"],
                problem_type=latest.get("problem_type", "unknown"),
                algorithm=algorithm,
                metrics=metrics,
                insights=updated_findings,
            )
    except Exception:
        logger.debug("FindingsStore not available — skipping persist", exc_info=True)

    return {
        "findings_summary": updated_findings,
        "messages": [
            HumanMessage(
                content=(
                    f"Extracted insights from iteration "
                    f"{state.get('current_iteration', 0)}. "
                    f"Findings memory updated ({len(updated_findings)} chars)."
                )
            )
        ],
    }
