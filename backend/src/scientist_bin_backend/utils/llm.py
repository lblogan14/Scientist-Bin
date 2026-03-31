"""LLM utilities — LangChain Gemini for graph nodes, google-genai for search-grounded queries."""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from scientist_bin_backend.config.settings import Settings, get_settings


def get_chat_model(settings: Settings | None = None) -> ChatGoogleGenerativeAI:
    """Return a LangChain ChatGoogleGenerativeAI instance configured from settings."""
    if settings is None:
        settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
    )


async def search_with_gemini(query: str, settings: Settings | None = None) -> str:
    """Perform a search-grounded query using the Google GenAI SDK.

    Uses ``google.genai.Client`` with Google Search tool for grounded results.
    This is separate from the LangChain path because LangChain's Gemini
    integration does not natively expose Google Search grounding.
    """
    if settings is None:
        settings = get_settings()

    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    client = genai.Client(api_key=settings.google_api_key)
    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=query,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
        ),
    )
    return response.text or ""
