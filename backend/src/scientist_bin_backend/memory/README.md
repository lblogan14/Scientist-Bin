# Memory Module

Persistent memory systems for cross-experiment learning. Two components:

1. **FindingsStore** -- ChromaDB vector store for semantic search over experiment findings
2. **ERL Journal** -- Structured Explanation-Reflection-Learning entries appended to experiment journals

## FindingsStore

`findings_store.py` provides a ChromaDB-backed vector store for storing and querying experiment results. This enables the campaign orchestrator (and future agents) to retrieve relevant past findings when planning new experiments.

### What Gets Stored

Each finding is a text document composed of:

```
Objective: <original objective>
Problem: <problem_type>
Algorithm: <algorithm name>
Metrics: <key=value pairs>
Insights: <extracted insights text>
```

Metadata stored alongside:
- `experiment_id` -- unique experiment identifier
- `algorithm` -- algorithm name (e.g., "RandomForestClassifier")
- `problem_type` -- classification, regression, clustering
- `primary_metric_value` -- first numeric metric value (for ranking)
- `timestamp` -- ISO 8601 timestamp

### Public API

| Method | Description |
|--------|-------------|
| `add_finding(experiment_id, objective, problem_type, algorithm, metrics, insights)` | Upsert a finding into the vector store |
| `query_similar(query, n_results=5)` | Semantic search: find findings most similar to a query string |
| `get_findings_for_problem_type(problem_type, n_results=10)` | Filtered query: find findings matching a specific problem type |
| `count()` | Return total number of stored findings |

Each query method returns a list of dicts with keys: `id`, `text`, `metadata`, `distance`.

### Storage Location

By default, ChromaDB persists to `outputs/memory/` (relative to the backend root). A custom `persist_dir` can be passed to the constructor.

### Graceful Degradation

ChromaDB is an **optional dependency**. When it is not installed:
- The constructor logs a warning and sets `_available = False`
- All public methods become safe no-ops (return empty lists or 0)
- No `ImportError` is raised -- callers never need to guard imports

Install ChromaDB to enable the store:
```bash
pip install chromadb
```

## ERL Journal

`erl_journal.py` extends the existing JSONL experiment journal format with structured reasoning entries that capture agent decision rationale.

### ERLEntry Dataclass

Each entry has six fields:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO 8601 timestamp (auto-filled by `make_erl_entry()`) |
| `phase` | `str` | Pipeline phase (e.g., "code_generation", "analysis") |
| `decision` | `str` | What was decided |
| `explanation` | `str` | Why the decision was made |
| `reflection` | `str` | What could be improved or what was surprising |
| `learning` | `str` | Generalizable takeaway for future experiments |

### Functions

| Function | Description |
|----------|-------------|
| `write_erl_entry(journal_path, entry)` | Append an ERL entry as a JSON line to the journal file |
| `extract_learnings(journal_path)` | Read a journal and return all non-empty `learning` strings |
| `format_erl_context(entries)` | Format ERL entries into a text block for prompt injection |
| `make_erl_entry(phase, decision, explanation, reflection, learning)` | Factory that auto-fills the timestamp |

### Journal Format

ERL entries are written as JSON lines with an `"event": "erl_entry"` marker, making them compatible with the existing experiment journal format:

```json
{"event": "erl_entry", "timestamp": "2026-04-04T...", "phase": "code_generation", "decision": "Switch to GradientBoosting", "explanation": "RandomForest overfitting", "reflection": "Should have tried regularization first", "learning": "Tree-based ensembles need early stopping on small datasets"}
```

The `extract_learnings()` function reads the journal and collects all non-empty `learning` fields, which can then be fed back into future experiment prompts for cross-experiment improvement.

## Key Files

| File | Purpose |
|------|---------|
| `findings_store.py` | `FindingsStore` class -- ChromaDB vector store with graceful degradation |
| `erl_journal.py` | `ERLEntry`, `write_erl_entry()`, `extract_learnings()`, `format_erl_context()`, `make_erl_entry()` |
