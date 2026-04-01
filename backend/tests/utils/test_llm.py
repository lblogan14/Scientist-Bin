"""Tests for LLM utility functions."""

from __future__ import annotations

from unittest.mock import patch

from scientist_bin_backend.utils.llm import (
    AGENT_MODELS,
    extract_text_content,
    get_agent_model,
    get_chat_model,
)

# ---------------------------------------------------------------------------
# extract_text_content tests
# ---------------------------------------------------------------------------


def test_extract_text_content_string():
    """Plain string content is returned as-is."""
    assert extract_text_content("Hello world") == "Hello world"


def test_extract_text_content_empty_string():
    assert extract_text_content("") == ""


def test_extract_text_content_list_single_block():
    """Single text block in list format (Gemini response)."""
    content = [{"type": "text", "text": "Hello.", "extras": {"signature": "abc"}}]
    assert extract_text_content(content) == "Hello."


def test_extract_text_content_list_multiple_blocks():
    """Multiple text blocks are concatenated."""
    content = [
        {"type": "text", "text": "Hello ", "extras": {}},
        {"type": "text", "text": "world.", "extras": {}},
    ]
    assert extract_text_content(content) == "Hello world."


def test_extract_text_content_list_with_non_text_block():
    """Non-text blocks are skipped."""
    content = [
        {"type": "text", "text": "Hello."},
        {"type": "other", "data": "ignored"},
    ]
    assert extract_text_content(content) == "Hello."


def test_extract_text_content_empty_list():
    assert extract_text_content([]) == ""


def test_extract_text_content_list_of_strings():
    """Some providers return list of plain strings."""
    assert extract_text_content(["Hello ", "world"]) == "Hello world"


# ---------------------------------------------------------------------------
# AGENT_MODELS registry tests
# ---------------------------------------------------------------------------


def test_agent_models_registry_has_expected_keys():
    """Verify all expected agent names are in the registry."""
    expected = {"central", "plan", "analyst", "sklearn", "summary"}
    assert set(AGENT_MODELS.keys()) == expected


def test_agent_models_registry_values_are_strings():
    for name, model in AGENT_MODELS.items():
        assert isinstance(model, str), f"AGENT_MODELS[{name!r}] should be a string"
        assert len(model) > 0, f"AGENT_MODELS[{name!r}] should not be empty"


# ---------------------------------------------------------------------------
# get_chat_model tests
# ---------------------------------------------------------------------------


def test_get_chat_model_default(mock_settings):
    """get_chat_model without explicit model uses settings.gemini_model."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_chat_model(settings=mock_settings)
        mock_cls.assert_called_once_with(
            model=mock_settings.gemini_model,
            google_api_key=mock_settings.google_api_key,
        )


def test_get_chat_model_explicit_model(mock_settings):
    """get_chat_model with explicit model overrides settings.gemini_model."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_chat_model(settings=mock_settings, model="gemini-3.1-pro-preview")
        mock_cls.assert_called_once_with(
            model="gemini-3.1-pro-preview",
            google_api_key=mock_settings.google_api_key,
        )


# ---------------------------------------------------------------------------
# get_agent_model tests
# ---------------------------------------------------------------------------


def test_get_agent_model_known_agent(mock_settings):
    """get_agent_model looks up the model from the AGENT_MODELS registry."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_agent_model("plan", settings=mock_settings)
        mock_cls.assert_called_once_with(
            model=AGENT_MODELS["plan"],
            google_api_key=mock_settings.google_api_key,
        )


def test_get_agent_model_unknown_agent_falls_back(mock_settings):
    """Unknown agent name falls back to settings.gemini_model."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_agent_model("unknown_agent", settings=mock_settings)
        mock_cls.assert_called_once_with(
            model=mock_settings.gemini_model,
            google_api_key=mock_settings.google_api_key,
        )


def test_get_agent_model_central_uses_flash(mock_settings):
    """Central agent uses the flash model."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_agent_model("central", settings=mock_settings)
        mock_cls.assert_called_once_with(
            model=AGENT_MODELS["central"],
            google_api_key=mock_settings.google_api_key,
        )
    # Verify it's actually the flash model
    assert "flash" in AGENT_MODELS["central"]


def test_get_agent_model_sklearn_uses_pro(mock_settings):
    """Sklearn agent uses the pro model."""
    with patch(
        "scientist_bin_backend.utils.llm.ChatGoogleGenerativeAI"
    ) as mock_cls:
        get_agent_model("sklearn", settings=mock_settings)
        mock_cls.assert_called_once_with(
            model=AGENT_MODELS["sklearn"],
            google_api_key=mock_settings.google_api_key,
        )
    # Verify it's actually the pro model
    assert "pro" in AGENT_MODELS["sklearn"]
