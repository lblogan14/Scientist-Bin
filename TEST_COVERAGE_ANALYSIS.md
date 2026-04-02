# Test Coverage Analysis

## Current State

**Backend:** 322 passing tests across 16 test files covering ~92 source files  
**Frontend:** 24 passing tests across 4 test files covering ~109 source files

---

## Backend Coverage Breakdown

### Well-Tested Areas

| Module | Test File | What's Covered |
|--------|-----------|---------------|
| Agent schemas & states | `test_analyst.py`, `test_plan.py`, `test_summary.py`, `test_central.py`, `test_sklearn.py` | Pydantic models, state creation, schema validation, serialization |
| Base framework graph | `test_base_framework.py` | Graph routing logic, code validation, result parsing, conditional edges |
| Event bus | `test_bus.py` | Event publish/subscribe |
| Execution budget | `test_budget.py` | Token/cost budgeting |
| Execution estimator | `test_estimator.py` | Cost/time estimation |
| Execution journal | `test_journal.py` | Execution history tracking |
| Metrics bridge | `test_metrics_bridge.py` | Metrics file parsing, aggregation |
| Runner integration | `test_runner_integration.py` | End-to-end script execution, metrics, errors, timeouts |
| API endpoints | `test_api.py` | REST endpoints, CRUD, pagination, filtering, artifact download |
| Utils (LLM, naming, skills) | `test_llm.py`, `test_naming.py`, `test_skill_loader.py` | LLM client, slugify, experiment ID generation, skill parsing/matching |

### Gaps: No Tests At All

These source modules have **zero test coverage**:

#### 1. Execution: `sandbox.py` (HIGH PRIORITY)
- `create_run_directory()` - directory creation logic
- `prepare_script()` - script generation with harness injection
- `build_sandbox_env()` - environment sanitization (strips API keys/secrets)
- **Why it matters:** `build_sandbox_env` is security-critical -- it strips secrets from the subprocess environment. A regression here could leak API keys to generated code.

#### 2. Execution: `templates.py` (MEDIUM PRIORITY)
- `METRICS_REPORTER_HARNESS` content correctness
- `EDA_TEMPLATE` generation
- `COMPLETION_SENTINEL` usage
- **Why it matters:** Templates are injected into every executed script. Malformed templates silently break metric collection.

#### 3. Utils: `artifacts.py` (HIGH PRIORITY)
- `save_experiment_artifacts()` - saves models, results, journals, reports
- File copying, JSON serialization, error handling paths
- **Why it matters:** This handles all persistent artifact storage. Silent failures here mean lost experiment results.

#### 4. Config: `settings.py` (LOW PRIORITY)
- `Settings` pydantic model validation
- `get_settings()` caching behavior
- Environment variable loading with alias choices
- **Why it matters:** Low risk since pydantic-settings is well-tested, but validating custom alias behavior (`GOOGLE_API_KEY` vs `SCIENTIST_BIN_GOOGLE_API_KEY`) would catch config regressions.

#### 5. Agent Nodes - No Individual Node Tests (HIGH PRIORITY)
None of the agent **node functions** (the actual LLM-calling logic) are tested. The existing agent tests only cover schemas, states, and graph routing. The untested nodes include:

- **Analyst nodes:** `data_profiler.py`, `data_cleaner.py`, `data_splitter.py`, `report_writer.py`
- **Plan nodes:** `researcher.py`, `plan_writer.py`, `plan_reviewer.py`, `plan_saver.py`, `_context.py`
- **Summary nodes:** `context_collector.py`, `diagnostics_computer.py`, `report_generator.py`, `artifact_saver.py`, `reviewer.py`
- **Central nodes:** `analyzer.py`, `router.py`
- **Base nodes:** `code_validator.py` (routing tested, but not the full node), `code_executor.py`, `results_analyzer.py`, `test_evaluator.py`
- **Sklearn nodes:** `code_generator.py`, `error_researcher.py`

**Why it matters:** These are the core business logic of the application. While they call LLMs (requiring mocks), the input/output transformations, state mutations, and error handling paths should be tested.

#### 6. CLI: `cli.py` (LOW PRIORITY)
- Command-line interface via Typer
- **Why it matters:** Minor -- CLI is a thin wrapper, but testing it validates argument parsing.

#### 7. API: `experiments.py` (MEDIUM PRIORITY)
- Experiment-specific endpoints (separate from main `routes.py`)
- **Why it matters:** The main `test_api.py` covers `routes.py` well, but experiment-specific routes in this separate file may have untested paths.

### Gaps: Insufficient Test Depth

#### 8. Agent Graph Integration Tests (MEDIUM PRIORITY)
The existing agent tests validate schemas and conditional edges in isolation, but there are no tests that run a full agent graph end-to-end with mocked LLM responses. This would catch issues with:
- State passing between nodes
- Error propagation through the graph
- Graph termination conditions

#### 9. API WebSocket Endpoints (MEDIUM PRIORITY)
The `test_api.py` file tests REST endpoints but not WebSocket connections for real-time training monitoring (SSE/WebSocket events).

---

## Frontend Coverage Breakdown

### Well-Tested Areas

| Component | What's Covered |
|-----------|---------------|
| `ConfusionMatrixHeatmap` | Rendering, data display, edge cases |
| `MarkdownRenderer` | Markdown parsing, code blocks, GFM |
| `MetricCards` | Metric display, formatting, variants |
| `api.ts` types | Type guard functions, API type validation |

### Gaps (4 test files for 109 source files)

#### 1. Feature Pages (HIGH PRIORITY)
No tests for any feature page components:
- `DashboardPage` - main landing page with stats, forms, experiment list
- `ExperimentSetupPage` - experiment configuration flow
- `ModelSelectionPage` - model comparison and selection
- `ResultsPage` - results visualization with 10+ tab components
- `TrainingMonitorPage` - real-time training monitoring

**Why it matters:** These are the primary user-facing surfaces. Rendering tests would catch layout regressions and data binding issues.

#### 2. Custom Hooks (HIGH PRIORITY)
No tests for any data-fetching or state hooks:
- `use-experiments.ts`, `use-experiment.ts` - experiment CRUD
- `use-submit-train.ts` - training submission
- `use-training-status.ts` - polling/streaming status
- `use-experiment-events.ts` - SSE event stream
- `use-plan-review.ts` - plan review flow
- `use-models.ts`, `use-result.ts` - data fetching

**Why it matters:** Hooks contain business logic (caching, error handling, data transforms). Testing with `@testing-library/react-hooks` would validate these independently of UI.

#### 3. Chart Components (MEDIUM PRIORITY)
Only 1 of 18 chart components is tested (`ConfusionMatrixHeatmap`). Missing:
- `MetricLineChart`, `MetricBarChart`, `MetricPieChart`, `MetricRadarChart`
- `BoxPlotChart`, `FeatureImportanceChart`, `HorizontalBarChart`
- `GroupedBarChart`, `HyperparamHeatmap`, `OverfitGaugeChart`, `ParetoFrontierChart`
- `MetricScatterChart`, `ChartContainer`

**Why it matters:** Charts render complex data. Snapshot or smoke tests ensure they don't crash on edge-case data (empty arrays, NaN values, single data points).

#### 4. State Management: `app-store.ts` (MEDIUM PRIORITY)
The Zustand store has no tests for state transitions or selectors.

#### 5. API Client: `api-client.ts` (MEDIUM PRIORITY)
The `ky`-based API client configuration (base URL, error handling, interceptors) is untested.

#### 6. Form Components (MEDIUM PRIORITY)
- `ObjectiveForm` - experiment submission with validation
- `HyperparameterForm` - hyperparameter configuration
- `ExperimentFilterBar` - filtering controls

**Why it matters:** Form validation logic and submission flows are high-value test targets.

#### 7. Feedback Components (LOW PRIORITY)
- `ErrorBoundary` - React error boundary
- `QueryErrorReset` - TanStack Query error recovery

---

## Recommended Priority Order

### Tier 1 - High Impact, Moderate Effort
1. **`sandbox.py` tests** - Security-critical env sanitization; pure functions, easy to test
2. **`artifacts.py` tests** - Artifact persistence; use `tmp_path` fixture, no mocks needed
3. **Frontend hooks tests** - Business logic in hooks; use `renderHook` from testing-library
4. **Frontend feature page smoke tests** - Render each page with mock data, verify no crashes

### Tier 2 - High Impact, Higher Effort
5. **Agent node tests with mocked LLM** - Test state transformations in/out of each node
6. **Agent graph integration tests** - Run full graphs with mock LLM, verify end-to-end flow
7. **Frontend chart smoke tests** - Render each chart with representative + edge-case data

### Tier 3 - Lower Priority
8. **`templates.py` tests** - Validate harness content, sentinel markers
9. **`settings.py` tests** - Config loading edge cases
10. **API WebSocket tests** - Real-time endpoint testing
11. **Frontend form validation tests** - Zod schema + submission flows
12. **Frontend store tests** - Zustand state transitions
