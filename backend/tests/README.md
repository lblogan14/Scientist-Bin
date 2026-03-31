# Tests

pytest test suite for the Scientist-Bin backend.

## Structure

- `conftest.py` — Shared fixtures (mock settings, FastAPI test client).
- `test_api.py` — REST API endpoint tests.
- `agents/test_central.py` — Central agent schema and utility tests.
- `agents/test_sklearn.py` — Sklearn subagent schema, utility, and retry logic tests.

## Running

```bash
uv run pytest -v              # Run all tests
uv run pytest tests/test_api.py::test_health_check  # Single test
```
