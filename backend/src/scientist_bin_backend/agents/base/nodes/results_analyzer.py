"""Results analysis, iteration routing, and finalization nodes.

Enhanced with:
- Experiment journaling (append-only log for introspection)
- Structured reflection (ERL pattern)
- IMPROVE pattern (modify one component at a time)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage

from scientist_bin_backend.agents.base.prompts import (
    FINAL_REPORT_PROMPT,
    REFLECTION_PROMPT,
    RESULTS_ANALYZER_PROMPT,
)
from scientist_bin_backend.agents.base.schemas import FinalReport, IterationDecision
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent
from scientist_bin_backend.execution.journal import get_journal_for_experiment
from scientist_bin_backend.execution.metrics_bridge import parse_results_json
from scientist_bin_backend.utils.llm import extract_text_content, get_chat_model


async def analyze_results(state: dict) -> dict:
    """Analyze execution results and decide next action.

    If execution failed: deterministic error classification (0 LLM calls).
    If execution succeeded: LLM decides next iteration action (1 LLM call),
    then performs structured reflection (1 LLM call).

    Follows the IMPROVE pattern: suggests modifying one pipeline component
    at a time for interpretable, stable improvements.
    """
    execution_success = state.get("execution_success", False)
    execution_output = state.get("execution_output", "")
    execution_error = state.get("execution_error", "")
    current_iteration = state.get("current_iteration", 0) + 1
    max_iterations = state.get("max_iterations", 5)
    experiment_history = list(state.get("experiment_history", []))
    experiment_id = state.get("experiment_id", "default")

    # Get experiment journal for logging
    journal = get_journal_for_experiment(experiment_id)

    # Parse results from execution output
    results_json = parse_results_json(execution_output)

    # Build new experiment records from this iteration
    new_records = []
    if results_json and "results" in results_json:
        for entry in results_json["results"]:
            record = {
                "iteration": current_iteration,
                "algorithm": entry.get("algorithm", "unknown"),
                "hyperparameters": entry.get("best_params", {}),
                "metrics": entry.get("metrics", {}),
                "training_time_seconds": entry.get("training_time", 0),
                "timestamp": datetime.now(UTC).isoformat(),
                # Enriched diagnostic fields (optional — present when
                # the generated code extracts them)
                "cv_fold_scores": entry.get("cv_fold_scores"),
                "cv_results_top_n": entry.get("cv_results_top_n"),
                "feature_importances": entry.get("feature_importances"),
                "confusion_matrix": entry.get("confusion_matrix"),
                "residual_stats": entry.get("residual_stats"),
            }
            new_records.append(record)

    # Log results to journal
    if new_records:
        for rec in new_records:
            journal.log(
                "experiment_result",
                phase="analysis",
                iteration=current_iteration,
                data={"algorithm": rec["algorithm"], "metrics": rec["metrics"]},
            )
    elif not execution_success:
        journal.log(
            "execution_failed",
            phase="analysis",
            iteration=current_iteration,
            data={"error": execution_error[:500]},
        )

    # Update best experiment
    best_experiment = state.get("best_experiment")
    success_criteria = state.get("success_criteria", {})
    primary_metric = next(iter(success_criteria), None) if success_criteria else None

    for record in new_records:
        if primary_metric and primary_metric in record.get("metrics", {}):
            current_best_value = (
                best_experiment.get("metrics", {}).get(primary_metric, -float("inf"))
                if best_experiment
                else -float("inf")
            )
            if record["metrics"][primary_metric] > current_best_value:
                best_experiment = record

    # Decide next action
    reflection = None
    if not execution_success:
        # Deterministic: execution failed, try to fix
        next_action = "fix_error"
        refinement_context = (
            f"The code failed to execute. Error:\n{execution_error}\n\n"
            "Please fix the error and regenerate the code."
        )
        decision_msg = f"Execution failed. Will attempt to fix. Error: {execution_error[:200]}"
        journal.log(
            "decision",
            phase="analysis",
            iteration=current_iteration,
            reasoning="Execution failed, attempting fix",
            data={"action": "fix_error"},
        )
    elif current_iteration >= max_iterations:
        # Deterministic: budget exhausted
        next_action = "accept" if best_experiment else "abort"
        refinement_context = None
        decision_msg = f"Max iterations ({max_iterations}) reached. Finalizing."
        journal.log(
            "decision",
            phase="analysis",
            iteration=current_iteration,
            reasoning=f"Budget exhausted after {max_iterations} iterations",
            data={"action": next_action},
        )
    else:
        # LLM decides next action (IMPROVE: suggest one component change)
        execution_summary = _build_execution_summary(results_json, execution_output)
        history_summary = _build_history_summary(experiment_history + new_records)

        # Include journal heuristics for context
        journal_context = journal.summarize(max_entries=10)

        llm = get_chat_model()
        structured_llm = llm.with_structured_output(IterationDecision)
        prompt = RESULTS_ANALYZER_PROMPT.format(
            objective=state.get("objective", ""),
            problem_type=state.get("problem_type", "unknown"),
            current_iteration=current_iteration,
            max_iterations=max_iterations,
            execution_summary=execution_summary,
            experiment_history=history_summary,
            success_criteria=(
                json.dumps(success_criteria) if success_criteria else "None specified"
            ),
            journal_context=journal_context,
        )
        decision: IterationDecision = await structured_llm.ainvoke([HumanMessage(content=prompt)])
        next_action = decision.action
        refinement_context = decision.refinement_instructions
        decision_msg = (
            f"Decision: {decision.action} "
            f"(confidence: {decision.confidence:.2f}). {decision.reasoning}"
        )

        # Log decision to journal
        journal.log(
            "decision",
            phase="analysis",
            iteration=current_iteration,
            reasoning=decision.reasoning,
            data={
                "action": decision.action,
                "confidence": decision.confidence,
                "instructions": decision.refinement_instructions,
            },
        )

        # Structured reflection (ERL): generate a heuristic from this iteration
        if next_action not in ("accept", "abort") and new_records:
            try:
                reflection = await _reflect_on_iteration(llm, state, new_records, decision)
                if reflection:
                    journal.log(
                        "reflection",
                        phase="analysis",
                        iteration=current_iteration,
                        reasoning=reflection,
                    )
            except Exception:
                reflection = None

    # Emit event
    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="agent_activity",
            data={
                "action": "analyze_results",
                "decision": next_action,
                "iteration": current_iteration,
            },
        ),
    )

    return {
        "experiment_history": new_records,  # Uses operator.add reducer
        "best_experiment": best_experiment,
        "current_iteration": current_iteration,
        "next_action": next_action,
        "refinement_context": refinement_context,
        "reflection": reflection,
        "phase": "done" if next_action in ("accept", "abort") else "execution",
        "progress_events": [
            {
                "event_type": "agent_activity",
                "data": {"action": next_action, "iteration": current_iteration},
            }
        ],
        "messages": [HumanMessage(content=decision_msg)],
    }


async def finalize(state: dict) -> dict:
    """Produce the final report. Uses 1 LLM call.

    Also writes final journal entries and extracts heuristics for future experiments.
    """
    best_experiment = state.get("best_experiment")
    experiment_history = state.get("experiment_history", [])
    data_profile = state.get("data_profile")
    experiment_id = state.get("experiment_id", "default")

    best_algorithm = best_experiment.get("algorithm", "unknown") if best_experiment else "none"
    best_metrics = best_experiment.get("metrics", {}) if best_experiment else {}

    data_profile_summary = ""
    if data_profile:
        data_profile_summary = data_profile.get("statistics_summary", "")

    history_summary = _build_history_summary(experiment_history)

    llm = get_chat_model()
    structured_llm = llm.with_structured_output(FinalReport)
    prompt = FINAL_REPORT_PROMPT.format(
        objective=state.get("objective", ""),
        problem_type=state.get("problem_type", "unknown"),
        best_algorithm=best_algorithm,
        best_metrics=json.dumps(best_metrics),
        experiment_history=history_summary,
        data_profile_summary=data_profile_summary,
    )
    report: FinalReport = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Write final journal entry
    journal = get_journal_for_experiment(experiment_id)
    journal.log(
        "experiment_complete",
        phase="done",
        iteration=state.get("current_iteration", 0),
        reasoning=report.interpretation,
        data={
            "best_model": report.best_model,
            "best_metrics": report.best_metrics,
            "recommendations": report.recommendations,
        },
    )

    # Emit completion
    await event_bus.emit(
        experiment_id,
        ExperimentEvent(
            event_type="experiment_done",
            data={
                "best_model": report.best_model,
                "best_metrics": report.best_metrics,
                "total_iterations": report.total_iterations,
            },
        ),
    )

    return {
        "phase": "done",
        "progress_events": [
            {
                "event_type": "experiment_done",
                "data": {"best_model": report.best_model},
            }
        ],
        "messages": [
            HumanMessage(
                content=f"## Final Report\n\n"
                f"**Best model:** {report.best_model}\n"
                f"**Metrics:** {json.dumps(report.best_metrics)}\n"
                f"**Iterations:** {report.total_iterations}\n\n"
                f"{report.interpretation}\n\n"
                f"**Recommendations:**\n" + "\n".join(f"- {r}" for r in report.recommendations)
            )
        ],
    }


# ---------------------------------------------------------------------------
# Reflection (ERL pattern)
# ---------------------------------------------------------------------------


async def _reflect_on_iteration(
    llm, state: dict, new_records: list[dict], decision: IterationDecision
) -> str | None:
    """Generate a heuristic/insight from this iteration's results.

    This is the Experiential Reflective Learning (ERL) pattern:
    after each iteration, the agent reflects on what happened and
    extracts a transferable lesson.
    """
    prompt = REFLECTION_PROMPT.format(
        objective=state.get("objective", ""),
        iteration=state.get("current_iteration", 0) + 1,
        results=json.dumps(
            [{"algorithm": r["algorithm"], "metrics": r["metrics"]} for r in new_records]
        ),
        decision=decision.action,
        reasoning=decision.reasoning,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    content = extract_text_content(response.content).strip()
    return content if content else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_execution_summary(results_json: dict | None, stdout: str) -> str:
    """Build a compact summary of execution results for the LLM prompt."""
    if not results_json:
        return f"Raw output (first 1000 chars):\n{stdout[:1000]}"

    lines = []
    for entry in results_json.get("results", []):
        algo = entry.get("algorithm", "?")
        metrics = entry.get("metrics", {})
        metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
        lines.append(f"  {algo}: {metrics_str}")

    best = results_json.get("best_model", "?")
    errors = results_json.get("errors", [])

    summary = "Model results:\n" + "\n".join(lines)
    summary += f"\nBest model: {best}"
    if errors:
        summary += f"\nErrors: {errors}"
    return summary


def _build_history_summary(experiment_history: list[dict]) -> str:
    """Build a compact summary of all experiment iterations."""
    if not experiment_history:
        return "No previous experiments."

    lines = []
    for record in experiment_history:
        algo = record.get("algorithm", "?")
        iteration = record.get("iteration", "?")
        metrics = record.get("metrics", {})
        metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
        lines.append(f"  Iteration {iteration} - {algo}: {metrics_str}")

    return "\n".join(lines)
