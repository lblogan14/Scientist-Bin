# Config

Application settings loaded from environment variables using Pydantic Settings.

The `.env` file is resolved relative to `backend/` (not the current working directory), so the CLI and server work correctly regardless of where they are invoked from.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google Gemini API key |
| `SCIENTIST_BIN_GEMINI_MODEL` | `gemini-2.0-flash` | Default Gemini model (fallback for unknown agents) |
| `SCIENTIST_BIN_GEMINI_MODEL_FLASH` | `gemini-3-flash-preview` | Fast model used by central and summary agents |
| `SCIENTIST_BIN_GEMINI_MODEL_PRO` | `gemini-3.1-pro-preview` | Capable model used by plan, analyst, and sklearn agents |
| `SCIENTIST_BIN_DEBUG` | `false` | Enable debug mode |
| `SCIENTIST_BIN_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `SCIENTIST_BIN_SANDBOX_TIMEOUT` | `300` | Seconds per code execution |
| `SCIENTIST_BIN_MAX_ITERATIONS` | `5` | Max generate-execute-analyze cycles |
| `SCIENTIST_BIN_SANDBOX_MAX_OUTPUT_BYTES` | `1000000` | Stdout cap per execution (1 MB) |

## Model Selection

The `gemini_model_flash` and `gemini_model_pro` settings provide configurable defaults for the two model tiers. However, per-agent model assignments are defined in `utils/llm.py` via the `AGENT_MODELS` dict:

| Agent | Model | Setting |
|-------|-------|---------|
| `central` | `gemini-3-flash-preview` | `gemini_model_flash` |
| `plan` | `gemini-3.1-pro-preview` | `gemini_model_pro` |
| `analyst` | `gemini-3.1-pro-preview` | `gemini_model_pro` |
| `sklearn` | `gemini-3.1-pro-preview` | `gemini_model_pro` |
| `summary` | `gemini-3-flash-preview` | `gemini_model_flash` |

## Module

- `settings.py` -- `Settings` class (Pydantic BaseSettings) with `SCIENTIST_BIN_` env prefix. `get_settings()` returns a cached singleton.
