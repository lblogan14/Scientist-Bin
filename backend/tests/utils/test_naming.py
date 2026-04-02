"""Tests for the experiment naming utility."""

from __future__ import annotations

import re

from scientist_bin_backend.utils.naming import _slugify, generate_experiment_id

# ---------------------------------------------------------------------------
# _slugify tests
# ---------------------------------------------------------------------------


def test_slugify_simple():
    assert _slugify("Classify iris species") == "classify-iris-species"


def test_slugify_special_characters():
    assert _slugify("Predict house prices (NYC)!") == "predict-house-prices-nyc"


def test_slugify_multiple_spaces():
    assert _slugify("  too   many   spaces  ") == "too-many-spaces"


def test_slugify_empty():
    assert _slugify("") == "experiment"


def test_slugify_only_special_chars():
    assert _slugify("!!!@@@###") == "experiment"


def test_slugify_truncation():
    long_text = "this is a very long objective that should be truncated at a word boundary"
    result = _slugify(long_text, max_length=40)
    assert len(result) <= 40
    assert not result.endswith("-")


def test_slugify_truncation_at_word_boundary():
    """Truncation should not chop words in the middle."""
    result = _slugify("classify iris species from measurements", max_length=20)
    assert len(result) <= 20
    # Should truncate at a hyphen boundary, not mid-word
    assert not result.endswith("-")


def test_slugify_numbers_preserved():
    assert _slugify("model v2 experiment 3") == "model-v2-experiment-3"


def test_slugify_no_leading_trailing_hyphens():
    result = _slugify("---hello---world---")
    assert not result.startswith("-")
    assert not result.endswith("-")
    assert result == "hello-world"


# ---------------------------------------------------------------------------
# generate_experiment_id tests
# ---------------------------------------------------------------------------


def test_generate_experiment_id_format():
    """ID should match YYYY-MM-DD_slug_hex4 pattern."""
    result = generate_experiment_id("Classify iris species")
    pattern = r"^\d{4}-\d{2}-\d{2}_classify-iris-species_[0-9a-f]{4}$"
    assert re.match(pattern, result), f"'{result}' doesn't match expected pattern"


def test_generate_experiment_id_empty_objective():
    """Empty objective produces 'experiment' slug."""
    result = generate_experiment_id("")
    pattern = r"^\d{4}-\d{2}-\d{2}_experiment_[0-9a-f]{4}$"
    assert re.match(pattern, result), f"'{result}' doesn't match expected pattern"


def test_generate_experiment_id_no_args():
    """Default empty objective produces 'experiment' slug."""
    result = generate_experiment_id()
    assert "_experiment_" in result


def test_generate_experiment_id_uniqueness():
    """Two calls with the same objective produce different IDs."""
    id1 = generate_experiment_id("Classify iris")
    id2 = generate_experiment_id("Classify iris")
    assert id1 != id2


def test_generate_experiment_id_filesystem_safe():
    """Generated ID should be safe for filesystem paths."""
    result = generate_experiment_id("Predict prices for NYC apartments!")
    # Should only contain: alphanumeric, hyphens, underscores
    assert re.match(r"^[\w-]+$", result), f"'{result}' contains unsafe characters"


def test_generate_experiment_id_long_objective():
    """Long objectives are truncated but still produce valid IDs."""
    long_obj = "Build a comprehensive machine learning model to predict customer churn"
    result = generate_experiment_id(long_obj)
    # Date (10) + _ (1) + slug (<=40) + _ (1) + hex (4) = max ~56 chars
    assert len(result) <= 60
    assert result.startswith("20")  # Starts with year


def test_generate_experiment_id_has_date():
    """ID contains today's date."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    result = generate_experiment_id("test")
    assert result.startswith(today)
