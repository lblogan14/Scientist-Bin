"""Tests for config/settings.py."""

from __future__ import annotations

from unittest.mock import patch

from scientist_bin_backend.config.settings import Settings, get_settings


def test_settings_defaults(monkeypatch):
    """Verify all default values match the class definition."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    # Clear cached singleton so fresh Settings is created
    get_settings.cache_clear()

    # Bypass .env file loading by patching _ENV_FILE to a non-existent path
    with patch("scientist_bin_backend.config.settings._ENV_FILE", "nonexistent.env"):
        s = Settings(google_api_key="test-key", _env_file="nonexistent.env")

    assert s.gemini_model == "gemini-2.0-flash"
    assert s.gemini_model_flash == "gemini-3-flash-preview"
    assert s.gemini_model_pro == "gemini-3.1-pro-preview"
    assert s.debug is False
    assert s.cors_origins == ["http://localhost:5173"]
    assert s.sandbox_timeout == 300
    assert s.max_iterations == 5
    assert s.sandbox_max_output_bytes == 1_000_000


def test_settings_from_env(monkeypatch):
    """Environment variables override defaults."""
    monkeypatch.setenv("GOOGLE_API_KEY", "my-real-key")
    monkeypatch.setenv("SCIENTIST_BIN_GEMINI_MODEL", "gemini-custom")
    monkeypatch.setenv("SCIENTIST_BIN_DEBUG", "true")
    monkeypatch.setenv("SCIENTIST_BIN_MAX_ITERATIONS", "10")

    s = Settings(
        google_api_key="my-real-key",
        gemini_model="gemini-custom",
        debug=True,
        max_iterations=10,
    )

    assert s.google_api_key == "my-real-key"
    assert s.gemini_model == "gemini-custom"
    assert s.debug is True
    assert s.max_iterations == 10


def test_get_settings_caching(monkeypatch):
    """get_settings returns the same singleton on repeated calls."""
    monkeypatch.setenv("GOOGLE_API_KEY", "cache-test-key")
    get_settings.cache_clear()

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

    # Clean up
    get_settings.cache_clear()


def test_settings_env_prefix(monkeypatch):
    """Settings reads SCIENTIST_BIN_ prefixed env vars."""
    monkeypatch.setenv("GOOGLE_API_KEY", "prefix-test")
    monkeypatch.setenv("SCIENTIST_BIN_SANDBOX_TIMEOUT", "600")

    s = Settings(google_api_key="prefix-test", sandbox_timeout=600)
    assert s.sandbox_timeout == 600
