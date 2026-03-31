# Utils

Shared utility modules used across the backend.

## Modules

- `llm.py` — `get_chat_model()` for LangChain Gemini calls, `search_with_gemini()` for Google Search-grounded queries, `extract_text_content()` to normalize `AIMessage.content` (newer Gemini models return a list of dicts instead of a plain string; use this whenever accessing `.content` directly from `ainvoke()`).
- `skill_loader.py` — SKILL.md loader following the [Anthropic Agent Skills specification](https://agentskills.io/specification). Provides `Skill` dataclass, `discover_skills()` for recursive discovery, `parse_skill()` for frontmatter parsing, `match_skill()` for problem-type matching, and `format_skill_listing()` for prompt injection.
