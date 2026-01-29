"""Unit tests for deterministic provider resolution."""

from __future__ import annotations

import logging

import pytest

from ai_utilities.client import AiSettings
from ai_utilities.provider_resolution import resolve_provider_config
from ai_utilities.providers.provider_exceptions import ProviderConfigurationError


def test_no_providers_configured_and_ai_provider_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """No providers configured + AI_PROVIDER missing -> error."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    # Clear all provider-specific vars
    for key in [
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "OPENROUTER_API_KEY",
        "OLLAMA_BASE_URL",
        "FASTCHAT_BASE_URL",
        "TEXT_GENERATION_WEBUI_BASE_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = AiSettings(_env_file=None)

    with pytest.raises(ProviderConfigurationError):
        resolve_provider_config(settings)


def test_single_provider_configured_selects_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exactly one provider configured -> selects it."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    settings = AiSettings(_env_file=None)

    resolved = resolve_provider_config(settings)
    assert resolved.provider == "groq"


def test_multiple_configured_default_order_and_logs(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """Multiple configured + no AI_PROVIDER -> picks default order and logs."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_AUTO_SELECT_ORDER", raising=False)

    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    settings = AiSettings(_env_file=None)

    caplog.set_level(logging.INFO)
    resolved = resolve_provider_config(settings)

    # Default order: openai, groq, openrouter...
    assert resolved.provider == "groq"
    assert any("Auto-selected provider" in rec.message for rec in caplog.records)


def test_multiple_configured_custom_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """AI_AUTO_SELECT_ORDER overrides selection order."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("AI_AUTO_SELECT_ORDER", "openrouter,groq")

    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    settings = AiSettings(_env_file=None)
    resolved = resolve_provider_config(settings)

    assert resolved.provider == "openrouter"


def test_explicit_provider_not_configured_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """AI_PROVIDER explicit but not configured -> raises."""
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    settings = AiSettings(_env_file=None)

    with pytest.raises(ProviderConfigurationError):
        resolve_provider_config(settings)


def test_hosted_model_precedence_provider_model_overrides_ai_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """<PROVIDER>_MODEL overrides AI_MODEL."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("AI_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    settings = AiSettings(_env_file=None)
    resolved = resolve_provider_config(settings)

    assert resolved.provider == "openai"
    assert resolved.model == "gpt-4o-mini"


def test_local_provider_requires_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Local provider requires <PROVIDER>_MODEL or AI_MODEL."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    settings = AiSettings(_env_file=None)

    with pytest.raises(ProviderConfigurationError):
        resolve_provider_config(settings)


def test_backward_compatibility_ai_provider_openai_ai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy: AI_PROVIDER=openai + AI_API_KEY works even if OPENAI_API_KEY absent."""
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "sk-legacy")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = AiSettings(_env_file=None)
    resolved = resolve_provider_config(settings)

    assert resolved.provider == "openai"
    assert resolved.api_key == "sk-legacy"
