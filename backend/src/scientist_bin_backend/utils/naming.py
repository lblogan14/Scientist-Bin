"""Experiment ID generation with human-readable naming.

Produces directory-safe names like: 2026-04-01_classify-iris-species_a1b2
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime


def generate_experiment_id(objective: str = "") -> str:
    """Generate a human-readable experiment ID.

    Format: ``YYYY-MM-DD_<slugified-objective>_<hex4>``

    Examples:
        >>> generate_experiment_id("Classify iris species")
        '2026-04-01_classify-iris-species_a1b2'
        >>> generate_experiment_id("")
        '2026-04-01_experiment_c3d4'

    The short hex suffix ensures uniqueness across same-day runs with
    identical objectives.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = _slugify(objective) if objective else "experiment"
    unique = uuid.uuid4().hex[:4]
    return f"{date_str}_{slug}_{unique}"


def _slugify(text: str, max_length: int = 40) -> str:
    """Convert text to a filesystem-safe slug.

    Lowercases, replaces non-alphanumeric runs with hyphens,
    strips leading/trailing hyphens, and truncates.
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    # Truncate at word boundary to avoid chopped words
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "experiment"
