"""LLM utilities — LangChain Gemini for graph nodes, google-genai for search-grounded queries."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from scientist_bin_backend.config.settings import Settings, get_settings


def _build_agent_models(settings: Settings | None = None) -> dict[str, str]:
    """Build per-agent model registry from settings.

    Central graph and summary use the faster flash model;
    plan, analyst, and sklearn use the more capable pro model.
    Reads model names from settings so ``.env`` overrides take effect.
    """
    if settings is None:
        settings = get_settings()
    flash = settings.gemini_model_flash
    pro = settings.gemini_model_pro
    return {
        "central": flash,
        "plan": pro,
        "analyst": pro,
        "sklearn": pro,
        "summary": flash,
        "campaign": pro,
    }


class _LazyAgentModels(dict):
    """Lazy dict that populates from settings on first access.

    Avoids requiring GOOGLE_API_KEY at import time while keeping the
    ``AGENT_MODELS["sklearn"]`` access pattern working everywhere.
    """

    _loaded: bool = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.update(_build_agent_models())
            self._loaded = True

    def __getitem__(self, key: str) -> str:
        self._ensure_loaded()
        return super().__getitem__(key)

    def __contains__(self, key: object) -> bool:
        self._ensure_loaded()
        return super().__contains__(key)

    def get(self, key: str, default: str | None = None) -> str | None:  # type: ignore[override]
        self._ensure_loaded()
        return super().get(key, default)

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()

    def __len__(self):
        self._ensure_loaded()
        return super().__len__()


# Per-agent model registry. Lazily resolves from settings so .env overrides
# take effect, without requiring GOOGLE_API_KEY at import time.
AGENT_MODELS: dict[str, str] = _LazyAgentModels()


def extract_text_content(content: str | list) -> str:
    """Normalize AIMessage.content to a plain string.

    Newer Gemini models may return content as a list of dicts
    (``[{'type': 'text', 'text': '...', ...}]``) instead of a plain string.
    This helper handles both formats.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def get_chat_model(
    settings: Settings | None = None,
    model: str | None = None,
) -> ChatGoogleGenerativeAI:
    """Return a LangChain ChatGoogleGenerativeAI instance.

    Args:
        settings: Application settings.  Defaults to the cached singleton.
        model: Explicit model name.  When provided this overrides ``settings.gemini_model``.

    Note: With some Gemini models, ``AIMessage.content`` may be a list of dicts
    rather than a plain string. Use :func:`extract_text_content` to normalize
    the content when accessing it directly (not needed for structured output).
    """
    if settings is None:
        settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=settings.google_api_key,
    )


def get_agent_model(
    agent_name: str,
    settings: Settings | None = None,
) -> ChatGoogleGenerativeAI:
    """Return a chat model configured for a specific agent.

    Looks up the model name in the per-agent registry (built from settings)
    and falls back to the default ``settings.gemini_model`` if the agent name
    is unknown.
    """
    if settings is None:
        settings = get_settings()
    agent_models = _build_agent_models(settings)
    model = agent_models.get(agent_name, settings.gemini_model)
    return get_chat_model(settings=settings, model=model)


async def search_with_gemini(
    query: str,
    settings: Settings | None = None,
    model: str | None = None,
) -> str:
    """Perform a search-grounded query using the Google GenAI SDK.

    Uses ``google.genai.Client`` with Google Search tool for grounded results.
    This is separate from the LangChain path because LangChain's Gemini
    integration does not natively expose Google Search grounding.

    Args:
        query: The search query.
        settings: Application settings.
        model: Explicit model name.  Overrides ``settings.gemini_model``.
    """
    if settings is None:
        settings = get_settings()

    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    client = genai.Client(api_key=settings.google_api_key)
    response = await client.aio.models.generate_content(
        model=model or settings.gemini_model,
        contents=query,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
        ),
    )
    return response.text or ""
