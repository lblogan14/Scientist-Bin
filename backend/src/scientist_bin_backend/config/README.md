# Config

Application settings loaded from environment variables using Pydantic Settings.

The `.env` file is resolved relative to `backend/` (not the current working directory), so the CLI and server work correctly regardless of where they are invoked from.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google Gemini API key |
| `SCIENTIST_BIN_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `SCIENTIST_BIN_DEBUG` | `false` | Enable debug mode |
| `SCIENTIST_BIN_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `SCIENTIST_BIN_SANDBOX_TIMEOUT` | `300` | Seconds per code execution |
| `SCIENTIST_BIN_MAX_ITERATIONS` | `5` | Max generate-execute-analyze cycles |
| `SCIENTIST_BIN_SANDBOX_MAX_OUTPUT_BYTES` | `1000000` | Stdout cap per execution (1 MB) |
