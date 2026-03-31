# Config

Application settings loaded from environment variables using Pydantic Settings.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google Gemini API key |
| `SCIENTIST_BIN_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `SCIENTIST_BIN_DEBUG` | `false` | Enable debug mode |
| `SCIENTIST_BIN_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
