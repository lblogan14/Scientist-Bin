"""LLM utilities — LangChain Gemini for graph nodes, google-genai for search-grounded queries."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from scientist_bin_backend.config.settings import Settings, get_settings

# Per-agent model registry.  Central graph and summary use the faster flash
# model; plan, analyst, and sklearn use the more capable pro model.
AGENT_MODELS: dict[str, str] = {
    "central": "gemini-3-flash-preview",
    "plan": "gemini-3.1-pro-preview",
    "analyst": "gemini-3.1-pro-preview",
    "sklearn": "gemini-3.1-pro-preview",
    "summary": "gemini-3-flash-preview",
}


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

    Looks up the model name in :data:`AGENT_MODELS` and falls back to the
    default ``settings.gemini_model`` if the agent name is unknown.
    """
    if settings is None:
        settings = get_settings()
    model = AGENT_MODELS.get(agent_name, settings.gemini_model)
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
