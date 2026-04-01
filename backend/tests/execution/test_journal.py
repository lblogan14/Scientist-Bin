"""Tests for the experiment journal."""

import tempfile
from pathlib import Path

from scientist_bin_backend.execution.journal import ExperimentJournal


def test_journal_log_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        journal = ExperimentJournal(Path(tmpdir) / "journal.jsonl")
        journal.log("test_event", phase="testing", iteration=1, data={"foo": "bar"})
        journal.log("test_event_2", phase="testing", iteration=2, reasoning="worked")

        entries = journal.read_all()
        assert len(entries) == 2
        assert entries[0]["event"] == "test_event"
        assert entries[0]["data"]["foo"] == "bar"
        assert entries[1]["reasoning"] == "worked"


def test_journal_summarize():
    with tempfile.TemporaryDirectory() as tmpdir:
        journal = ExperimentJournal(Path(tmpdir) / "journal.jsonl")
        journal.log(
            "experiment_result",
            phase="analysis",
            iteration=1,
            data={"metrics": {"accuracy": 0.95}},
        )
        summary = journal.summarize()
        assert "experiment_result" in summary
        assert "accuracy=0.9500" in summary


def test_journal_extract_heuristics():
    with tempfile.TemporaryDirectory() as tmpdir:
        journal = ExperimentJournal(Path(tmpdir) / "journal.jsonl")
        journal.log("reflection", reasoning="Tree models work best for this data")
        journal.log("heuristic_learned", reasoning="Don't scale for tree-based models")
        journal.log("other_event", reasoning="not a heuristic")

        heuristics = journal.extract_heuristics()
        assert len(heuristics) == 2
        assert "Tree models" in heuristics[0]


def test_journal_empty_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        journal = ExperimentJournal(Path(tmpdir) / "journal.jsonl")
        entries = journal.read_all()
        assert entries == []
        assert journal.summarize() == "No journal entries yet."
