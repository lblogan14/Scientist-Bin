"""FindingsStore — ChromaDB-backed vector store for experiment findings.

Stores experiment results and extracted insights so that future experiments
can query past findings for cross-experiment learning.  ChromaDB is an
optional dependency; when it is not installed the store degrades gracefully
to a no-op.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FindingsStore:
    """Persistent vector store for experiment findings backed by ChromaDB.

    If ChromaDB is not installed, every public method becomes a safe no-op so
    that callers never need to guard imports themselves.
    """

    def __init__(self, persist_dir: Path | None = None) -> None:
        if persist_dir is None:
            persist_dir = (
                Path(__file__).resolve().parent.parent.parent.parent / "outputs" / "memory"
            )
        self._persist_dir = persist_dir
        self._collection = None
        self._available = False

        try:
            import chromadb  # noqa: F811
        except ImportError:
            logger.warning(
                "chromadb is not installed — FindingsStore will operate as a no-op. "
                "Install it with: pip install chromadb"
            )
            return

        try:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._collection = client.get_or_create_collection(name="experiment_findings")
            self._available = True
            logger.info("FindingsStore initialised at %s", self._persist_dir)
        except Exception:
            logger.exception("Failed to initialise ChromaDB — FindingsStore disabled")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_finding(
        self,
        experiment_id: str,
        objective: str,
        problem_type: str,
        algorithm: str,
        metrics: dict,
        insights: str = "",
    ) -> None:
        """Add an experiment finding to the vector store."""
        if not self._available:
            return

        metrics_str = ", ".join(
            f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items()
        )

        text = (
            f"Objective: {objective}\n"
            f"Problem: {problem_type}\n"
            f"Algorithm: {algorithm}\n"
            f"Metrics: {metrics_str}\n"
            f"Insights: {insights}"
        )

        primary_metric_value = next(
            (v for v in metrics.values() if isinstance(v, (int, float))),
            0.0,
        )

        metadata = {
            "experiment_id": experiment_id,
            "algorithm": algorithm,
            "problem_type": problem_type,
            "primary_metric_value": float(primary_metric_value),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        try:
            assert self._collection is not None  # guarded by _available  # noqa: S101
            self._collection.upsert(
                ids=[experiment_id],
                documents=[text],
                metadatas=[metadata],
            )
            logger.debug("Added finding for experiment %s", experiment_id)
        except Exception:
            logger.exception("Failed to add finding for experiment %s", experiment_id)

    def query_similar(self, query: str, n_results: int = 5) -> list[dict]:
        """Query the store for findings most similar to *query*.

        Returns a list of dicts, each with keys: id, text, metadata, distance.
        """
        if not self._available:
            return []

        try:
            assert self._collection is not None  # noqa: S101
            results = self._collection.query(query_texts=[query], n_results=n_results)
        except Exception:
            logger.exception("ChromaDB query failed")
            return []

        findings: list[dict] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            findings.append(
                {
                    "id": doc_id,
                    "text": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else None,
                }
            )

        return findings

    def get_findings_for_problem_type(self, problem_type: str, n_results: int = 10) -> list[dict]:
        """Return findings filtered by *problem_type* metadata."""
        if not self._available:
            return []

        try:
            assert self._collection is not None  # noqa: S101
            results = self._collection.query(
                query_texts=[problem_type],
                n_results=n_results,
                where={"problem_type": problem_type},
            )
        except Exception:
            logger.exception("ChromaDB query (problem_type=%s) failed", problem_type)
            return []

        findings: list[dict] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            findings.append(
                {
                    "id": doc_id,
                    "text": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else None,
                }
            )

        return findings

    def count(self) -> int:
        """Return the total number of stored findings."""
        if not self._available:
            return 0
        try:
            assert self._collection is not None  # noqa: S101
            return self._collection.count()
        except Exception:
            logger.exception("ChromaDB count failed")
            return 0
