"""Planner node — researches and plans the sklearn approach.

Uses 1-2 LLM calls: optional Google Search + structured strategy plan.
Loads matching SKILL.md content to guide algorithm selection, preprocessing,
and evaluation strategy based on the problem type.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.sklearn.prompts.templates import PLANNER_PROMPT
from scientist_bin_backend.agents.sklearn.schemas import SklearnStrategyPlan
from scientist_bin_backend.utils.llm import get_chat_model, search_with_gemini
from scientist_bin_backend.utils.skill_loader import (
    discover_skills,
    format_skill_listing,
    match_skill,
)

logger = logging.getLogger(__name__)

# Resolve skills directory once at import time
_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


async def plan_strategy(state: dict) -> dict:
    """Research best practices via Google Search, then produce a structured plan.

    Skills integration:
    - Discovers available skills from the sklearn skills/ directory
    - Matches the best skill for the detected problem type
    - Injects the matched skill's full body into the planning prompt
    - Falls back to a compact listing of all skills if no match
    """
    objective = state["objective"]
    data_description = state.get("data_description", "")
    problem_type = state.get("problem_type", "classification")
    data_profile = state.get("data_profile")
    experiment_history = state.get("experiment_history", [])

    # --- Skill loading ---
    skills = discover_skills(_SKILLS_DIR)
    matched_skill = match_skill(skills, problem_type, objective)

    if matched_skill:
        skill_context = matched_skill.format_for_prompt(include_body=True)
        logger.info("Matched skill '%s' for problem type '%s'", matched_skill.name, problem_type)
    else:
        # No exact match — provide listing of available skills
        skill_context = (
            "Available skills (none matched problem type exactly):\n" + format_skill_listing(skills)
        )
        logger.info("No exact skill match for '%s', providing listing", problem_type)

    # --- Google Search for best practices ---
    search_query = f"scikit-learn best practices for {problem_type}: {objective} {data_description}"
    search_results = await search_with_gemini(search_query)

    # --- Format data profile for prompt ---
    data_profile_str = "No data profile available."
    if data_profile:
        data_profile_str = json.dumps(data_profile, indent=2, default=str)

    # --- Format experiment history ---
    history_str = "No previous experiments."
    if experiment_history:
        lines = []
        for record in experiment_history:
            algo = record.get("algorithm", "?")
            metrics = record.get("metrics", {})
            metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
            lines.append(f"  {algo}: {metrics_str}")
        history_str = "\n".join(lines)

    # --- Generate structured plan ---
    llm = get_chat_model()
    structured_llm = llm.with_structured_output(SklearnStrategyPlan)
    prompt = PLANNER_PROMPT.format(
        objective=objective,
        data_description=data_description,
        problem_type=problem_type,
        data_profile=data_profile_str,
        skill_context=skill_context,
        search_context=search_results,
        experiment_history=history_str,
    )
    plan: SklearnStrategyPlan = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # --- Extract structured fields for state ---
    candidate_algorithms = [c.algorithm_name for c in plan.candidate_algorithms]
    hyperparameter_spaces = {
        c.algorithm_name: c.hyperparameter_grid for c in plan.candidate_algorithms
    }
    preprocessing_plan = [s.step_name for s in plan.preprocessing_steps]
    feature_engineering_plan = [s.step_name for s in plan.feature_engineering_steps]

    plan_summary = (
        f"Approach: {plan.approach_summary}\n"
        f"Algorithms: {', '.join(candidate_algorithms)}\n"
        f"Preprocessing: {', '.join(preprocessing_plan)}\n"
        f"Feature engineering: {', '.join(feature_engineering_plan)}\n"
        f"CV strategy: {plan.cv_strategy}\n"
        f"Success criteria: {json.dumps(plan.success_criteria)}"
    )

    return {
        "strategy": plan.model_dump(),
        "candidate_algorithms": candidate_algorithms,
        "hyperparameter_spaces": hyperparameter_spaces,
        "preprocessing_plan": preprocessing_plan,
        "feature_engineering_plan": feature_engineering_plan,
        "cv_strategy": plan.cv_strategy,
        "success_criteria": plan.success_criteria,
        "search_results": search_results,
        "phase": "execution",
        "progress_events": [
            {
                "event_type": "phase_change",
                "data": {
                    "phase": "planning",
                    "algorithms": candidate_algorithms,
                    "summary": plan.approach_summary,
                    "matched_skill": matched_skill.name if matched_skill else None,
                },
            }
        ],
        "messages": [HumanMessage(content=f"Strategy planned:\n{plan_summary}")],
    }
