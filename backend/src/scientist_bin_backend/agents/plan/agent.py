"""High-level wrapper around the plan agent graph."""

from __future__ import annotations

from scientist_bin_backend.agents.plan.graph import build_plan_graph
from scientist_bin_backend.utils.naming import generate_experiment_id


class PlanAgent:
    """Runs the planning pipeline: rewrite -> research -> plan -> review.

    The review step uses ``interrupt()`` for human-in-the-loop approval.
    When ``auto_approve=True`` the interrupt is skipped and the plan is
    accepted immediately.
    """

    def __init__(self, checkpointer=None) -> None:
        self.graph = build_plan_graph(checkpointer=checkpointer)

    async def run(
        self,
        objective: str,
        data_description: str = "",
        data_file_path: str | None = None,
        framework_preference: str | None = None,
        experiment_id: str | None = None,
        auto_approve: bool = False,
        max_revisions: int = 3,
        task_analysis: dict | None = None,
        analysis_report: str | None = None,
        data_profile: dict | None = None,
        problem_type: str | None = None,
    ) -> dict:
        """Execute the full planning pipeline and return results.

        Args:
            objective: The user's ML objective in natural language.
            data_description: Free-text description of the dataset.
            data_file_path: Absolute path to the data file, if any.
            framework_preference: Preferred ML framework (e.g. "sklearn").
            experiment_id: Existing experiment ID, or auto-generated.
            auto_approve: When ``True``, skip human review and approve
                the plan automatically.
            max_revisions: Maximum number of plan revisions before
                auto-approving.
            task_analysis: Structured analysis from the central agent.
            analysis_report: Data analysis report from the analyst agent.
            data_profile: Data profile dict from the analyst agent.
            problem_type: ML problem type from the analyst agent.

        Returns:
            A dict with ``execution_plan``, ``plan_markdown``,
            ``plan_approved``, ``rewritten_query``, and ``search_results``.
        """
        experiment_id = experiment_id or generate_experiment_id(objective)

        initial_state = {
            "messages": [],
            "objective": objective,
            "data_description": data_description,
            "data_file_path": data_file_path,
            "framework_preference": framework_preference,
            "task_analysis": task_analysis,
            "analysis_report": analysis_report,
            "data_profile": data_profile,
            "problem_type": problem_type,
            "rewritten_query": None,
            "search_results": None,
            "execution_plan": None,
            "plan_markdown": None,
            "human_feedback": None,
            "plan_approved": auto_approve,
            "revision_count": 0,
            "max_revisions": max_revisions,
            "experiment_id": experiment_id,
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "execution_plan": result.get("execution_plan"),
            "plan_markdown": result.get("plan_markdown"),
            "plan_approved": result.get("plan_approved", False),
            "rewritten_query": result.get("rewritten_query"),
            "search_results": result.get("search_results"),
        }
