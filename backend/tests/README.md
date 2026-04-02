# Tests

pytest test suite for the Scientist-Bin backend.

## Structure

```
tests/
├── conftest.py                         — Shared fixtures (mock settings, test client)
├── test_api.py                         — REST API endpoint tests (CRUD, filtering, pagination,
│                                         plan review, artifact downloads)
├── agents/
│   ├── test_central.py                 — Central agent schemas, utilities, select_subagent routing
│   ├── test_plan.py                    — Plan agent schemas, context builder, markdown renderer, routing
│   ├── test_analyst.py                 — Analyst agent schemas, data profiler, splitter
│   ├── test_sklearn.py                 — Sklearn schemas, routing, utilities
│   ├── test_base_framework.py          — Base framework agent infrastructure
│   └── test_summary.py                — Summary agent schemas, model ranking
├── events/
│   └── test_bus.py                     — EventBus pub/sub, pre_register/consume, SSE format
├── execution/
│   ├── test_budget.py                  — IterationBudget and BudgetTracker
│   ├── test_estimator.py              — Duration estimation, dynamic timeout
│   ├── test_journal.py                — ExperimentJournal (append-only log)
│   ├── test_metrics_bridge.py         — ===RESULTS=== JSON parsing
│   └── test_runner_integration.py     — End-to-end CodeRunner with iris data
└── utils/
    ├── test_llm.py                    — extract_text_content(), get_agent_model(), AGENT_MODELS
    ├── test_naming.py                 — Experiment ID generation and slugification
    └── test_skill_loader.py           — SKILL.md parsing, discovery, matching
```

## Running

```bash
uv run pytest -v                           # Run all tests
uv run pytest tests/test_api.py            # API endpoint tests
uv run pytest tests/agents/test_central.py # Central agent + routing tests
uv run pytest tests/events/test_bus.py     # Event bus tests
uv run pytest -k "iris"                    # Integration tests with iris data
```
