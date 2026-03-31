"""Experiment journal — append-only log for agent introspection and decision tracking.

The journal captures reasoning, decisions, metrics, and observations across iterations.
It serves as external memory for the agent, enabling structured reflection on past
experiments and better decision-making in future iterations.

Based on Eric J. Ma's agentic data science patterns and the ERL (Experiential
Reflective Learning) approach.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class ExperimentJournal:
    """Append-only experiment journal written to a JSONL file."""

    def __init__(self, journal_path: Path) -> None:
        self.journal_path = journal_path
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event: str,
        *,
        phase: str = "",
        iteration: int | None = None,
        data: dict | None = None,
        reasoning: str = "",
    ) -> None:
        """Append a journal entry."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            "phase": phase,
            "iteration": iteration,
            "reasoning": reasoning,
            "data": data or {},
        }
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read_all(self) -> list[dict]:
        """Read all journal entries."""
        if not self.journal_path.exists():
            return []
        entries = []
        with open(self.journal_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def summarize(self, max_entries: int = 20) -> str:
        """Produce a compact summary of recent journal entries for LLM context."""
        entries = self.read_all()
        if not entries:
            return "No journal entries yet."

        recent = entries[-max_entries:]
        lines = []
        for e in recent:
            ts = e.get("timestamp", "?")[:19]
            event = e.get("event", "?")
            phase = e.get("phase", "")
            iteration = e.get("iteration")
            reasoning = e.get("reasoning", "")
            data = e.get("data", {})

            line = f"[{ts}] {event}"
            if phase:
                line += f" (phase={phase})"
            if iteration is not None:
                line += f" (iter={iteration})"
            if reasoning:
                line += f" — {reasoning}"
            # Include key metrics if present
            if "metrics" in data:
                metrics_str = ", ".join(
                    f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                    for k, v in data["metrics"].items()
                )
                line += f" [{metrics_str}]"
            lines.append(line)

        return "\n".join(lines)

    def extract_heuristics(self) -> list[str]:
        """Extract learned heuristics from the journal for future experiments.

        Returns a list of actionable insights based on experiment history.
        """
        entries = self.read_all()
        heuristics = []

        for e in entries:
            if e.get("event") == "heuristic_learned":
                heuristics.append(e.get("reasoning", ""))
            elif e.get("event") == "reflection" and e.get("reasoning"):
                heuristics.append(e.get("reasoning", ""))

        return heuristics


def get_journal_for_experiment(
    experiment_id: str, base_dir: Path | None = None
) -> ExperimentJournal:
    """Get or create a journal for a given experiment."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent / "outputs"
    journal_path = base_dir / "runs" / experiment_id / "journal.jsonl"
    return ExperimentJournal(journal_path)
