# Tests

pytest test suite for the Scientist-Bin backend.

## Structure

```
tests/
├── conftest.py                         — Shared fixtures (mock settings, test client)
├── test_api.py                         — REST API endpoint tests
├── agents/
│   ├── test_central.py                 — Central agent schemas and utilities
│   ├── test_plan.py                    — Plan agent schemas, query rewriter, plan writer
│   ├── test_analyst.py                 — Analyst agent schemas, data profiler, splitter
│   ├── test_sklearn.py                 — Sklearn schemas, routing, utilities
│   └── (test_summary.py)              — Summary agent schemas, model ranking (planned)
├── events/
│   └── test_bus.py                     — EventBus pub/sub, SSE format, new event types
├── execution/
│   ├── test_budget.py                  — IterationBudget and BudgetTracker
│   ├── test_estimator.py              — Duration estimation, dynamic timeout
│   ├── test_journal.py                — ExperimentJournal (append-only log)
│   ├── test_metrics_bridge.py         — ===RESULTS=== JSON parsing
│   └── test_runner_integration.py     — End-to-end CodeRunner with iris data
└── utils/
    ├── test_llm.py                    — extract_text_content(), get_agent_model(), AGENT_MODELS
    └── test_skill_loader.py           — SKILL.md parsing, discovery, matching
```

## Running

```bash
uv run pytest -v                           # Run all tests
uv run pytest tests/test_api.py            # Single module
uv run pytest tests/agents/test_plan.py    # Plan agent tests
uv run pytest tests/agents/test_analyst.py # Analyst agent tests
uv run pytest tests/utils/test_skill_loader.py  # Skill loader tests
uv run pytest -k "iris"                    # Integration tests with iris data
```
