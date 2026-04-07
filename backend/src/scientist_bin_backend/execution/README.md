# Execution

Code execution infrastructure for sandboxed ML training.

## Modules

| File | Purpose |
|------|---------|
| `runner.py` | `CodeRunner` — executes Python in isolated subprocesses with timeout, stdout/stderr capture, and real-time metrics collection |
| `sandbox.py` | Environment sanitization (strips API keys), run directory management, `get_framework_python()` for per-framework venv resolution |
| `templates.py` | `MetricsReporter` harness injected into scripts, deterministic EDA template |
| `metrics_bridge.py` | File-based IPC: watches `metrics.jsonl` for real-time metric updates, parses `===RESULTS===` JSON from stdout |
| `budget.py` | `IterationBudget` + `BudgetTracker` — deterministic stopping rules (max iterations, wall time, patience, target thresholds) |
| `estimator.py` | Duration estimation from dataset characteristics, dynamic timeout computation, progressive training subset suggestions |
| `journal.py` | `ExperimentJournal` — append-only JSONL log for agent introspection and decision tracking |

## How Code Execution Works

1. Generated code is wrapped with a `MetricsReporter` harness (provides `report_metric()` function)
2. Written to an isolated run directory under `outputs/runs/{experiment_id}/{run_id}/`
3. Executed via `asyncio.create_subprocess_exec` with sanitized environment (no API keys). On Windows, falls back to `subprocess.run()` in a thread if the event loop does not support async subprocesses.
4. Stdout, stderr, and metrics captured in real-time
5. Results parsed from `===RESULTS===` JSON marker in stdout
6. Artifacts collected from the `artifacts/` subdirectory

## Framework Virtual Environments

Each ML framework (sklearn, FLAML, PyTorch, etc.) runs in its own isolated virtual environment under `backend/framework_venvs/<name>/.venv/`. The `get_framework_python(framework_name)` function in `sandbox.py` resolves the correct Python interpreter:

1. **Provisioned venv** — if `framework_venvs/<name>/.venv/` exists, use its Python
2. **Extras fallback** — if the marker package is importable in the current venv (extras installed via `uv sync --extra`), use `sys.executable`
3. **Error** — raise `RuntimeError` with instructions to provision or install extras

`FRAMEWORK_VENV_MAP` in `sandbox.py` maps agent framework names to venv directory names (e.g., `"sklearn"` → `"traditional"`, `"flaml"` → `"traditional"`).

The `METRICS_REPORTER_HARNESS` in `templates.py` conditionally imports pandas (wrapped in `try/except ImportError`) so it works in any framework venv regardless of whether pandas is available.
