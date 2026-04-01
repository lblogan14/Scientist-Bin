"""Code generator node — produces runnable sklearn code from the plan.

Uses 1 LLM call. The generated code must follow the structured output convention
(===RESULTS=== marker + JSON) and use the report_metric() function.

The sklearn agent now receives pre-split data paths (train/val/test) from the
analyst agent, so generated code loads data from those paths directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.sklearn.prompts.templates import CODE_GENERATOR_PROMPT
from scientist_bin_backend.agents.sklearn.utils import strip_code_fences
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model


async def generate_code(state: dict) -> dict:
    """Generate sklearn training code based on the plan and context."""
    # Build retry context if this is a refinement iteration
    retry_context = ""
    next_action = state.get("next_action")
    refinement_context = state.get("refinement_context")

    if next_action == "fix_error" and refinement_context:
        retry_context = f"== PREVIOUS ATTEMPT FAILED ==\n{refinement_context}\n"
        # Include web search results for error resolution
        search_results = state.get("search_results")
        if search_results:
            retry_context += (
                "\n== WEB SEARCH RESULTS (solutions found online) ==\n"
                f"{search_results}\n"
                "Use the above information to fix the error.\n"
            )
    elif next_action == "refine_params" and refinement_context:
        retry_context = (
            "== REFINEMENT REQUESTED ==\n"
            f"{refinement_context}\n"
            "Adjust the hyperparameter search based on these instructions.\n"
        )
    elif next_action == "try_new_algo" and refinement_context:
        retry_context = (
            "== NEW ALGORITHM REQUESTED ==\n"
            f"{refinement_context}\n"
            "Try different algorithms as suggested.\n"
        )
    elif next_action == "feature_engineer" and refinement_context:
        retry_context = (
            "== FEATURE ENGINEERING REQUESTED ==\n"
            f"{refinement_context}\n"
            "Add the suggested feature transformations.\n"
        )

    # Build experiment history context
    experiment_history = state.get("experiment_history", [])
    if experiment_history:
        history_lines = ["== Previous experiment results (avoid repeating same configurations) =="]
        for record in experiment_history:
            algo = record.get("algorithm", "?")
            metrics = record.get("metrics", {})
            params = record.get("hyperparameters", {})
            metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
            history_lines.append(f"  {algo} ({json.dumps(params)}): {metrics_str}")
        retry_context += "\n".join(history_lines) + "\n"

    # Format data profile
    data_profile = state.get("data_profile")
    data_profile_str = "No data profile available."
    if data_profile:
        data_profile_str = json.dumps(data_profile, indent=2, default=str)

    # Format strategy / execution plan
    execution_plan = state.get("execution_plan")
    strategy = state.get("strategy") or execution_plan
    strategy_str = "No strategy available."
    if strategy:
        strategy_str = json.dumps(strategy, indent=2, default=str)

    # Resolve split data paths
    split_data_paths = state.get("split_data_paths", {})
    train_path = str(Path(split_data_paths.get("train", "train.csv")).resolve())
    val_path = str(Path(split_data_paths.get("val", "val.csv")).resolve())
    test_path = str(Path(split_data_paths.get("test", "test.csv")).resolve())

    # Include analysis report if available
    analysis_context = ""
    analysis_report = state.get("analysis_report")
    if analysis_report:
        analysis_context = f"\n== DATA ANALYSIS REPORT ==\n{analysis_report[:2000]}\n"

    llm = get_agent_model("sklearn")
    prompt = CODE_GENERATOR_PROMPT.format(
        objective=state.get("objective", ""),
        problem_type=state.get("problem_type", "classification"),
        data_profile=data_profile_str,
        strategy=strategy_str,
        train_file_path=train_path,
        val_file_path=val_path,
        test_file_path=test_path,
        analysis_context=analysis_context,
        retry_context=retry_context,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    code = strip_code_fences(extract_text_content(response.content))

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="agent_activity",
                data={
                    "action": "generate_code",
                    "iteration": state.get("current_iteration", 0),
                },
            ),
        )

    return {
        "generated_code": code,
        "phase": "execution",
        "progress_events": [
            {
                "event_type": "agent_activity",
                "data": {"action": "generate_code", "iteration": state.get("current_iteration", 0)},
            }
        ],
        "messages": [HumanMessage(content="Code generated. Proceeding to execution.")],
    }
