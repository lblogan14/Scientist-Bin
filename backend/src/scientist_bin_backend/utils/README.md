# Utils

Shared utility modules used across the backend.

## Modules

### `llm.py`

LLM utilities for LangChain Gemini and Google Search grounding.

| Function / Object | Description |
|-------------------|-------------|
| `AGENT_MODELS` | Dict mapping agent names to Gemini model identifiers. Central and summary use `gemini-3-flash-preview`; plan, analyst, and sklearn use `gemini-3.1-pro-preview`. |
| `get_agent_model(agent_name)` | Returns a `ChatGoogleGenerativeAI` instance configured for the named agent. Falls back to `settings.gemini_model` for unknown agent names. |
| `get_chat_model(settings, model)` | Returns a `ChatGoogleGenerativeAI` instance with an explicit model override. |
| `extract_text_content(content)` | Normalizes `AIMessage.content` to a plain string. Newer Gemini models return content as a list of dicts instead of a plain string; use this whenever accessing `.content` directly from `ainvoke()` (not needed for `with_structured_output()` calls). |
| `search_with_gemini(query)` | Performs a search-grounded query using the `google-genai` SDK with Google Search tool. Used by the plan agent (research) and sklearn agent (error research). |

### `skill_loader.py`

SKILL.md loader following the [Anthropic Agent Skills specification](https://agentskills.io/specification).

| Function | Description |
|----------|-------------|
| `discover_skills()` | Recursively discovers SKILL.md files from a given `skills/` directory |
| `parse_skill()` | Parses YAML frontmatter from a SKILL.md file into a `Skill` dataclass |
| `match_skill()` | Matches a problem type to the best available skill |
| `format_skill_listing()` | Formats skill content for prompt injection |

### `artifacts.py`

Shared artifact saving logic used by both the CLI and the API route after training completes.

| Function | Description |
|----------|-------------|
| `save_experiment_artifacts(experiment_id, result_dict)` | Copies artifacts from run directories to top-level `outputs/` directories. Returns a dict mapping artifact type to saved file path. |

Saved artifacts:
- `outputs/results/<id>.json` -- full result JSON
- `outputs/models/<id>.joblib` -- best trained model
- `outputs/logs/<id>.jsonl` -- experiment decision journal
- `outputs/results/<id>_analysis.md` -- analysis report from the analyst agent
- `outputs/results/<id>_summary.md` -- summary report from the summary agent
- `outputs/results/<id>_plan.json` -- execution plan from the plan agent
