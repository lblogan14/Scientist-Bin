"""Code generator node — produces runnable FLAML AutoML code from the plan.

Uses 1 LLM call. The generated code must follow the structured output convention
(===RESULTS=== marker + JSON) and use the report_metric() function.

Unlike sklearn, FLAML handles model selection and hyperparameter tuning
automatically, so generated code is simpler — focused on configuring
``flaml.AutoML`` rather than building sklearn pipelines.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.base.utils import strip_code_fences
from scientist_bin_backend.agents.frameworks.flaml.prompts import (
    FLAML_CLASSIFICATION_PROMPT,
    FLAML_REGRESSION_PROMPT,
    FLAML_TS_FORECAST_PROMPT,
)
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.utils.llm import extract_text_content, get_agent_model
from scientist_bin_backend.utils.skill_loader import discover_skills, match_skill

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

# Maximum chars of reference content to inject
_MAX_REFERENCE_CHARS = 10000

# Default FLAML estimators by problem type
_DEFAULT_ESTIMATORS = {
    "classification": [
        "lgbm", "xgboost", "xgb_limitdepth", "rf", "extra_tree", "lrl1",
    ],
    "regression": ["lgbm", "rf", "xgboost", "extra_tree"],
    "ts_forecast": [
        "lgbm", "xgboost", "rf", "extra_tree", "prophet", "arima", "sarimax",
    ],
}

# Default metrics by problem type
_DEFAULT_METRICS = {
    "classification": "accuracy",
    "regression": "r2",
    "ts_forecast": "mape",
}


def _load_skill_reference(problem_type: str) -> str:
    """Load the skill reference content for a given problem type."""
    skills = discover_skills(_SKILLS_DIR)
    skill = match_skill(skills, problem_type)
    if not skill:
        return ""

    for supporting_file in skill.supporting_files:
        if supporting_file.name == "reference.md":
            try:
                content = supporting_file.read_text(encoding="utf-8")
                if len(content) > _MAX_REFERENCE_CHARS:
                    content = content[:_MAX_REFERENCE_CHARS] + "\n... (truncated)"
                return content
            except OSError:
                return ""
    return ""


async def generate_code(state: dict) -> dict:
    """Generate FLAML AutoML training code based on the plan and context."""
    # Build retry context if this is a refinement iteration
    retry_context = ""
    next_action = state.get("next_action")
    refinement_context = state.get("refinement_context")

    # Include validation error if the previous attempt failed validation
    validation_error = state.get("validation_error")
    if validation_error:
        retry_context += (
            "== CODE VALIDATION FAILED ==\n"
            f"{validation_error}\n"
            "Fix the issues above in the regenerated code.\n\n"
        )

    if next_action == "fix_error" and refinement_context:
        retry_context = f"== PREVIOUS ATTEMPT FAILED ==\n{refinement_context}\n"
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
            "Adjust the FLAML configuration based on these instructions.\n"
        )
    elif next_action == "try_new_algo" and refinement_context:
        retry_context = (
            "== NEW ALGORITHM REQUESTED ==\n"
            f"{refinement_context}\n"
            "Adjust the estimator_list or FLAML configuration as suggested.\n"
        )
    elif next_action == "feature_engineer" and refinement_context:
        retry_context = (
            "== FEATURE ENGINEERING REQUESTED ==\n"
            f"{refinement_context}\n"
            "Add the suggested feature transformations before passing data to FLAML.\n"
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

    problem_type = state.get("problem_type", "classification")

    # Extract FLAML-specific parameters from execution plan
    plan = execution_plan or {}
    time_budget = state.get("time_budget") or plan.get("time_budget", 120)
    estimator_list = (
        state.get("estimator_list")
        or plan.get("estimator_list")
        or _DEFAULT_ESTIMATORS.get(problem_type, _DEFAULT_ESTIMATORS["classification"])
    )
    metric = (
        state.get("flaml_metric")
        or plan.get("metric")
        or _DEFAULT_METRICS.get(problem_type, "accuracy")
    )

    # Load skill reference
    skill_reference = _load_skill_reference(problem_type)
    if skill_reference:
        retry_context = (
            f"== SKILL REFERENCE ({problem_type}) ==\n"
            "Use the following guidance when generating code:\n\n"
            f"{skill_reference}\n\n"
        ) + retry_context

    llm = get_agent_model("flaml")

    if problem_type == "ts_forecast":
        ts_period = state.get("ts_period") or plan.get("ts_period", 12)
        # Detect temporal and target columns from data profile
        temporal_column = None
        target_column = None
        if data_profile:
            temporal_cols = data_profile.get("temporal_columns", [])
            if temporal_cols:
                temporal_column = temporal_cols[0]
            target_column = data_profile.get("target_column")

        # Fallback: infer from column names if data profile didn't detect them
        if not temporal_column:
            col_names = (data_profile or {}).get("column_names", [])
            for candidate in ["DATE", "Date", "date", "datetime", "ds", "timestamp"]:
                if candidate in col_names:
                    temporal_column = candidate
                    break
            if not temporal_column and col_names:
                temporal_column = col_names[0]  # first column as last resort

        if not target_column:
            col_names = (data_profile or {}).get("column_names", [])
            # Target is likely the non-temporal numeric column
            for c in col_names:
                if c != temporal_column:
                    target_column = c
                    break
            if not target_column:
                target_column = "value"

        prompt = FLAML_TS_FORECAST_PROMPT.format(
            objective=state.get("objective", ""),
            data_profile=data_profile_str,
            strategy=strategy_str,
            train_file_path=train_path,
            val_file_path=val_path,
            test_file_path=test_path,
            analysis_context=analysis_context,
            retry_context=retry_context,
            time_budget=time_budget,
            metric=metric,
            estimator_list=json.dumps(estimator_list),
            ts_period=ts_period,
            temporal_column=temporal_column,
            target_column=target_column,
        )
    elif problem_type == "regression":
        prompt = FLAML_REGRESSION_PROMPT.format(
            objective=state.get("objective", ""),
            data_profile=data_profile_str,
            strategy=strategy_str,
            train_file_path=train_path,
            val_file_path=val_path,
            test_file_path=test_path,
            analysis_context=analysis_context,
            retry_context=retry_context,
            time_budget=time_budget,
            metric=metric,
            estimator_list=json.dumps(estimator_list),
        )
    else:
        prompt = FLAML_CLASSIFICATION_PROMPT.format(
            objective=state.get("objective", ""),
            data_profile=data_profile_str,
            strategy=strategy_str,
            train_file_path=train_path,
            val_file_path=val_path,
            test_file_path=test_path,
            analysis_context=analysis_context,
            retry_context=retry_context,
            time_budget=time_budget,
            metric=metric,
            estimator_list=json.dumps(estimator_list),
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
                    "framework": "flaml",
                },
            ),
        )

    return {
        "generated_code": code,
        "phase": "execution",
        "progress_events": [
            {
                "event_type": "agent_activity",
                "data": {
                    "action": "generate_code",
                    "iteration": state.get("current_iteration", 0),
                },
            }
        ],
        "messages": [HumanMessage(content="FLAML code generated. Proceeding to execution.")],
    }
