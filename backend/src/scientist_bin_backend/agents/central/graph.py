"""StateGraph definition for the central orchestrator agent.

The central agent orchestrates the full 5-agent pipeline:
    analyze → route → plan → analyst → sklearn → summary → END
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from scientist_bin_backend.agents.central.nodes.analyzer import analyze
from scientist_bin_backend.agents.central.nodes.router import route, select_subagent
from scientist_bin_backend.agents.central.states import CentralState
from scientist_bin_backend.events.bus import event_bus
from scientist_bin_backend.events.types import ExperimentEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Delegate nodes — each calls the respective agent and maps results back
# ---------------------------------------------------------------------------


async def _plan_delegate(state: CentralState) -> dict:
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


async def _analyst_delegate(state: CentralState) -> dict:
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
        execution_plan=state.get("execution_plan"),
        experiment_id=experiment_id,
    )

    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="analysis_completed",
                data={"has_report": bool(result.get("analysis_report"))},
            ),
        )

    return {
        "analysis_report": result.get("analysis_report"),
        "split_data_paths": result.get("split_data_paths"),
        "problem_type": result.get("problem_type"),
        "data_profile": result.get("data_profile"),
    }


async def _sklearn_delegate(state: CentralState) -> dict:
    """Delegate to the sklearn subagent."""
    from scientist_bin_backend.agents.sklearn.agent import SklearnAgent

    experiment_id = state.get("experiment_id")
    if experiment_id:
        await event_bus.emit(
            experiment_id,
            ExperimentEvent(
                event_type="phase_change",
                data={"phase": "execution", "message": "Starting sklearn agent"},
            ),
        )

    agent = SklearnAgent()
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
                event_type="sklearn_completed", data={"iterations": result.get("iterations", 0)}
            ),
        )

    return {"sklearn_results": result}


async def _summary_delegate(state: CentralState) -> dict:
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

    sklearn_results = state.get("sklearn_results") or {}
    agent = SummaryAgent()
    result = await agent.run(
        objective=state["objective"],
        problem_type=state.get("problem_type"),
        execution_plan=state.get("execution_plan"),
        analysis_report=state.get("analysis_report"),
        sklearn_results=sklearn_results,
        experiment_history=sklearn_results.get("experiment_history", []),
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
            **sklearn_results,
            "summary_report": result.get("summary_report"),
            "best_model": result.get("best_model"),
            "best_hyperparameters": result.get("best_hyperparameters"),
            "best_metrics": result.get("best_metrics"),
            "plan": state.get("execution_plan"),
            "plan_markdown": state.get("plan_markdown"),
            "analysis_report": state.get("analysis_report"),
        },
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_central_graph(checkpointer=None):
    """Build and compile the central orchestrator graph."""
    builder = StateGraph(CentralState)

    builder.add_node("analyze", analyze)
    builder.add_node("route", route)
    builder.add_node("plan", _plan_delegate)
    builder.add_node("analyst", _analyst_delegate)
    builder.add_node("sklearn", _sklearn_delegate)
    builder.add_node("summary", _summary_delegate)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "route")
    builder.add_conditional_edges("route", select_subagent, {"sklearn": "plan", END: END})
    builder.add_edge("plan", "analyst")
    builder.add_edge("analyst", "sklearn")
    builder.add_edge("sklearn", "summary")
    builder.add_edge("summary", END)

    return builder.compile(checkpointer=checkpointer)
