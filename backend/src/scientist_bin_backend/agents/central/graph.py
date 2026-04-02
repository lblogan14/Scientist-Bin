"""StateGraph definition for the central orchestrator agent.

The central agent orchestrates the full 5-agent pipeline:
    analyze → route → analyst → plan (HITL) → framework → summary → END
"""

from __future__ import annotations

import importlib

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.central.nodes.analyzer import analyze
from scientist_bin_backend.agents.central.nodes.router import (
    FRAMEWORK_REGISTRY,
    SUPPORTED_FRAMEWORKS,
    route,
    select_subagent,
)
from scientist_bin_backend.agents.central.states import PipelineState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

# ---------------------------------------------------------------------------
# Delegate nodes — each calls the respective agent and maps results back
# ---------------------------------------------------------------------------


async def _analyst_delegate(state: PipelineState) -> dict:
    """Delegate to the analyst agent."""
    from scientist_bin_backend.agents.analyst.agent import AnalystAgent

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "data_analysis", "message": "Starting analyst agent"},
            ),
        )

    agent = AnalystAgent()
    result = await agent.run(
        objective=state["objective"],
        data_file_path=state.get("data_file_path"),
        experiment_id=experiment_id,
        task_analysis=state.get("task_analysis"),
        data_description=state.get("data_description"),
        selected_framework=state.get("selected_framework"),
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="analysis_completed",
                data={
                    "has_report": bool(result.get("analysis_report")),
                    "classification_confidence": result.get("classification_confidence"),
                },
            ),
        )

    return {
        "analysis_report": result.get("analysis_report"),
        "split_data_paths": result.get("split_data_paths"),
        "problem_type": result.get("problem_type"),
        "data_profile": result.get("data_profile"),
        "classification_confidence": result.get("classification_confidence"),
        "classification_reasoning": result.get("classification_reasoning"),
    }


async def _plan_delegate(state: PipelineState) -> dict:
    """Delegate to the plan agent."""
    from scientist_bin_backend.agents.plan.agent import PlanAgent

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "planning", "message": "Starting plan agent"},
            ),
        )

    agent = PlanAgent()
    result = await agent.run(
        objective=state["objective"],
        data_description=state.get("data_description", ""),
        data_file_path=state.get("data_file_path"),
        framework_preference=state.get("selected_framework"),
        experiment_id=experiment_id,
        auto_approve=state.get("plan_approved", False),
        task_analysis=state.get("task_analysis"),
        analysis_report=state.get("analysis_report"),
        data_profile=state.get("data_profile"),
        problem_type=state.get("problem_type"),
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="plan_completed",
                data={"plan_approved": result.get("plan_approved", False)},
            ),
        )

    return {
        "execution_plan": result.get("execution_plan"),
        "plan_approved": result.get("plan_approved", False),
        "plan_markdown": result.get("plan_markdown"),
    }


async def _framework_delegate(state: PipelineState) -> dict:
    """Delegate to the selected framework agent (generic)."""
    framework = (state.get("selected_framework") or "sklearn").lower()
    agent_path = FRAMEWORK_REGISTRY.get(framework)

    if not agent_path:
        return {"error": f"Unsupported framework: {framework}"}

    module_path, class_name = agent_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    agent_cls = getattr(module, class_name)

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "execution", "message": f"Starting {framework} agent"},
            ),
        )

    agent = agent_cls()
    result = await agent.run(
        objective=state["objective"],
        execution_plan=state.get("execution_plan"),
        analysis_report=state.get("analysis_report"),
        split_data_paths=state.get("split_data_paths"),
        problem_type=state.get("problem_type"),
        data_profile=state.get("data_profile"),
        experiment_id=experiment_id,
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="framework_completed",
                data={
                    "framework": framework,
                    "iterations": result.get("iterations", 0),
                },
            ),
        )

    return {"framework_results": result}


async def _summary_delegate(state: PipelineState) -> dict:
    """Delegate to the summary agent."""
    from scientist_bin_backend.agents.summary.agent import SummaryAgent

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "summarizing", "message": "Starting summary agent"},
            ),
        )

    framework_results = state.get("framework_results") or {}
    agent = SummaryAgent()
    result = await agent.run(
        objective=state["objective"],
        problem_type=state.get("problem_type"),
        execution_plan=state.get("execution_plan"),
        analysis_report=state.get("analysis_report"),
        data_profile=state.get("data_profile"),
        plan_markdown=state.get("plan_markdown"),
        split_data_paths=state.get("split_data_paths"),
        framework_results=framework_results,
        experiment_history=framework_results.get("experiment_history", []),
        test_metrics=framework_results.get("test_metrics"),
        test_diagnostics=framework_results.get("test_diagnostics"),
        generated_code=framework_results.get("generated_code"),
        test_evaluation_code=framework_results.get("test_evaluation_code"),
        experiment_id=experiment_id,
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="summary_completed", data={"best_model": result.get("best_model")}
            ),
        )

    return {
        "summary_report": result.get("summary_report"),
        "agent_response": {
            **framework_results,
            "summary_report": result.get("summary_report"),
            "best_model": result.get("best_model"),
            "best_hyperparameters": result.get("best_hyperparameters"),
            "best_metrics": result.get("best_metrics"),
            "selection_reasoning": result.get("selection_reasoning"),
            "report_sections": result.get("report_sections"),
            "plan": state.get("execution_plan"),
            "plan_markdown": state.get("plan_markdown"),
            "analysis_report": state.get("analysis_report"),
        },
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_central_graph(checkpointer=None):
    """Build and compile the central orchestrator graph.

    Pipeline: analyze → route → analyst → plan (HITL) → framework → summary → END
    """
    builder = StateGraph(PipelineState)

    builder.add_node("analyze", analyze)
    builder.add_node("route", route)
    builder.add_node("analyst", _analyst_delegate)
    builder.add_node("plan", _plan_delegate)
    builder.add_node("framework", _framework_delegate)
    builder.add_node("summary", _summary_delegate)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "route")
    builder.add_conditional_edges(
        "route",
        select_subagent,
        {fw: "analyst" for fw in SUPPORTED_FRAMEWORKS},
    )
    builder.add_edge("analyst", "plan")
    builder.add_edge("plan", "framework")
    builder.add_edge("framework", "summary")
    builder.add_edge("summary", END)

    return builder.compile(checkpointer=checkpointer)
