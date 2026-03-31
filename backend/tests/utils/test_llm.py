"""Tests for LLM utility functions."""

from scientist_bin_backend.utils.llm import extract_text_content


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
