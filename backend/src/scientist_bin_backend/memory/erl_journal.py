"""Enhanced ERL (Explanation, Reflection, Learning) journaling.

Extends the existing JSONL experiment journal format with structured
reasoning entries that capture the agent's decision rationale, reflections,
and extracted learnings for cross-experiment improvement.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ERLEntry:
    """A single Explanation-Reflection-Learning journal entry."""

    timestamp: str
    phase: str
    decision: str
    explanation: str
    reflection: str
    learning: str


def write_erl_entry(journal_path: Path, entry: ERLEntry) -> None:
    """Append an ERL entry as a JSON line to *journal_path*."""
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event": "erl_entry",
        **asdict(entry),
    }
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def extract_learnings(journal_path: Path) -> list[str]:
    """Read *journal_path* and return all non-empty learning strings."""
    if not journal_path.exists():
        return []

    learnings: list[str] = []
    with open(journal_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            learning = entry.get("learning", "")
            if learning:
                learnings.append(learning)

    return learnings


def format_erl_context(entries: list[ERLEntry]) -> str:
    """Format a list of ERL entries into a text block suitable for prompt injection."""
    if not entries:
        return "No prior ERL entries available."

    lines: list[str] = []
    for entry in entries:
        lines.append(f"--- [{entry.timestamp}] {entry.phase} ---")
        lines.append(f"Decision: {entry.decision}")
        lines.append(f"Explanation: {entry.explanation}")
        lines.append(f"Reflection: {entry.reflection}")
        if entry.learning:
            lines.append(f"Learning: {entry.learning}")
        lines.append("")

    return "\n".join(lines).rstrip()


def make_erl_entry(
    phase: str,
    decision: str,
    explanation: str,
    reflection: str,
    learning: str = "",
) -> ERLEntry:
    """Convenience factory that auto-fills the timestamp."""
    return ERLEntry(
        timestamp=datetime.now(UTC).isoformat(),
        phase=phase,
        decision=decision,
        explanation=explanation,
        reflection=reflection,
        learning=learning,
    )
