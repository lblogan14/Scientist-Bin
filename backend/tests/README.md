# Tests

pytest test suite for the Scientist-Bin backend.

## Structure

```
tests/
├── conftest.py                         — Shared fixtures (mock settings, test client)
├── e2e_helpers.py                      — Shared artifact assertions and cleanup for E2E tests
├── test_api.py                         — REST API endpoint tests (CRUD, filtering, pagination,
│                                         plan review, artifact downloads)
├── test_e2e_pipeline.py                — Sklearn E2E with real LLM (classification, regression,
│                                         clustering) — @pytest.mark.slow
├── test_e2e_flaml.py                   — FLAML E2E with real LLM (classification, regression,
│                                         ts_forecast) — @pytest.mark.slow
├── test_e2e_api_flaml.py               — API-driven FLAML E2E via _run_training — @pytest.mark.slow
├── agents/
│   ├── test_central.py                 — Central agent schemas, utilities, select_subagent routing
│   ├── test_plan.py                    — Plan agent schemas, context builder, markdown renderer, routing
│   ├── test_analyst.py                 — Analyst agent schemas, data profiler, splitter
│   ├── test_sklearn.py                 — Sklearn schemas, routing, utilities
│   ├── test_flaml.py                   — FLAML schemas, agent instantiation, registry
│   ├── test_base_framework.py          — Base framework agent infrastructure
│   ├── test_error_correction.py        — Error correction routing (_route_decision), error research node
│   └── test_summary.py                — Summary agent schemas, model ranking
├── events/
│   └── test_bus.py                     — EventBus pub/sub, pre_register/consume, SSE format
├── execution/
│   ├── test_budget.py                  — IterationBudget and BudgetTracker
│   ├── test_estimator.py              — Duration estimation, dynamic timeout
│   ├── test_flaml_codegen.py          — FLAML code execution via CodeRunner (no LLM, real training)
│   ├── test_framework_python.py       — get_framework_python() venv resolution and fallback
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
uv run pytest -v                           # Run all 490+ tests (fast, no API key needed)
uv run pytest -m slow --timeout=600        # E2E pipeline tests (requires GOOGLE_API_KEY)
uv run pytest tests/test_api.py            # API endpoint tests
uv run pytest tests/agents/test_central.py # Central agent + routing tests
uv run pytest tests/events/test_bus.py     # Event bus tests
uv run pytest tests/execution/test_flaml_codegen.py  # FLAML code execution (no LLM)
uv run pytest -k "iris"                    # Integration tests with iris data
```

## Test Tiers

| Tier | Speed | Gate | What |
|------|-------|------|------|
| **Fast** | <60s | None | Unit tests, schema tests, mocked API tests, codegen tests |
| **Slow** | 3-10min each | `GOOGLE_API_KEY` | Full pipeline E2E (real LLM + real training) |

Slow tests are marked `@pytest.mark.slow` and skipped automatically when `GOOGLE_API_KEY` is not set.

## Test Datasets

| Dataset | Path | Problem Type | Used By |
|---------|------|-------------|---------|
| Iris | `data/iris_data/Iris.csv` | Classification | sklearn E2E, FLAML E2E, codegen |
| Wine Quality | `data/wine_data/WineQT.csv` | Regression | sklearn E2E, FLAML E2E, codegen |
| Mall Customers | `data/mall_data/Mall_Customers.csv` | Clustering | sklearn E2E |
| Electric Production | `data/electric_data/Electric_Production.csv` | Time Series | FLAML E2E, codegen |
