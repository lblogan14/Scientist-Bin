"""Utility functions for the sklearn subagent."""

from __future__ import annotations

import re


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM output, returning just the code."""
    # Remove ```python ... ``` or ``` ... ```
    pattern = r"```(?:python)?\s*\n?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
