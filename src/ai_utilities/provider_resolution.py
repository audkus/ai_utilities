"""Provider resolution and configuration.

This module contains the single-responsibility logic for selecting an AI provider
from settings + environment variables, including deterministic auto-selection.

Precedence rules (high to low):
1) Provider-specific variables (e.g. OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL)
2) Generic AI_* variables (AI_API_KEY, AI_MODEL, AI_BASE_URL) as fallback when provider matches

Provider selection rules:
- If AI_PROVIDER is set to an explicit provider:
  - If provider is configured, use it.
  - If not configured, raise ProviderConfigurationError.
- If AI_PROVIDER is missing or set to "auto":
  - Determine configured providers.
  - If none configured: raise ProviderConfigurationError.
  - If one configured: use it.
  - If multiple configured: select deterministically by order and log at INFO.

Configured provider definition:
- Hosted provider: <PROVIDER>_API_KEY is set (non-empty)
- Local provider: <PROVIDER>_BASE_URL is set (non-empty)
"""

from __future__ import annotations

import logging
import os
from typing import Iterable, Optional, Tuple

from pydantic import BaseModel, Field

from .providers.provider_exceptions import ProviderConfigurationError

logger = logging.getLogger(__name__)


ProviderName = str


VALID_PROVIDERS: frozenset[str] = frozenset(
    {
        "openai",
        "groq",
        "together",
        "openrouter",
        "ollama",
        "lmstudio",
        "fastchat",
        "text-generation-webui",
        "openai_compatible",
        "auto",
    }
)


DEFAULT_AUTO_SELECT_ORDER: tuple[str, ...] = (
    "openai",
    "groq",
    "openrouter",
    "together",
    "ollama",
    "lmstudio",
    "fastchat",
    "text-generation-webui",
)


class ResolvedProviderConfig(BaseModel):
    """Resolved provider configuration.

    Args:
        provider: Provider identifier.
        api_key: API key/token to use.
        base_url: Provider base URL.
        model: Model name.
        is_local: Whether this provider is considered local.
        selection_reason: Human readable reason for the chosen provider.
    """

    provider: ProviderName
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    is_local: bool
    selection_reason: str = Field(default="")


def configure_library_logging(ai_log_level: Optional[str]) -> None:
    """Configure the ai_utilities logger level.

    This intentionally avoids calling logging.basicConfig() to prevent unexpected
    global logging side effects.

    Args:
        ai_log_level: Log level string (e.g. "INFO").

    Returns:
        None.
    """

    if not ai_log_level:
        return

    level_name = str(ai_log_level).strip().upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = logging.INFO

    lib_logger = logging.getLogger("ai_utilities")
    lib_logger.setLevel(level)
    if not lib_logger.handlers:
        lib_logger.addHandler(logging.NullHandler())


def resolve_provider_config(settings) -> ResolvedProviderConfig:
    """Resolve the effective provider configuration.

    Args:
        settings: AiSettings instance.

    Returns:
        ResolvedProviderConfig.

    Raises:
        ProviderConfigurationError: If configuration is missing or inconsistent.
    """

    ai_log_level = getattr(settings, "ai_log_level", None) or os.getenv("AI_LOG_LEVEL")
    configure_library_logging(ai_log_level)

    return _resolve_provider_config_internal(settings=settings)


def _resolve_provider_config_internal(
    *,
    settings,
    provider_override: Optional[str] = None,
    api_key_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> ResolvedProviderConfig:
    requested_provider = _normalize(provider_override)
    if requested_provider is None:
        requested_provider = _normalize(getattr(settings, "provider", None))
    if requested_provider is None:
        requested_provider = _normalize(os.getenv("AI_PROVIDER"))

    if requested_provider is not None and requested_provider not in VALID_PROVIDERS:
        raise ProviderConfigurationError(
            f"Unknown provider: {requested_provider}",
            requested_provider,
        )

    if requested_provider is None or requested_provider == "auto":
        configured = _detect_configured_providers(settings)
        if not configured:
            raise ProviderConfigurationError(
                "No providers are configured. Set e.g. OPENAI_API_KEY (hosted) or OLLAMA_BASE_URL (local).",
                "auto",
            )

        if len(configured) == 1:
            selected_provider = configured[0]
            reason = "single configured provider"
        else:
            order, order_source = _resolve_auto_select_order(settings)
            selected_provider = _pick_first_in_order(configured, order)
            if selected_provider is None:
                raise ProviderConfigurationError(
                    f"Multiple providers are configured ({', '.join(configured)}), but none match AI_AUTO_SELECT_ORDER.",
                    "auto",
                )
            reason = "multiple configured providers"
            logger.info(
                "Auto-selected provider: %s. Configured providers=%s. Order=%s. Order source=%s.",
                selected_provider,
                configured,
                list(order),
                order_source,
            )

        requested_provider = selected_provider
    else:
        configured = _detect_configured_providers(settings)
        # Special case: openai_compatible should be allowed through so that
        # missing base_url can raise a precise error ("Base URL is required")
        # instead of a generic "not configured".
        if requested_provider == "openai_compatible":
            reason = "explicit provider"
        elif requested_provider not in configured:
            # Backward compatibility: allow legacy AI_API_KEY to count as configuration
            # for explicitly selected hosted providers.
            legacy_ai_api_key = getattr(settings, "api_key", None) or os.getenv("AI_API_KEY")
            hosted = {"openai", "groq", "together", "openrouter"}
            if requested_provider in hosted and _non_empty(str(legacy_ai_api_key) if legacy_ai_api_key else None):
                configured.append(requested_provider)
            else:
                raise ProviderConfigurationError(
                    f"Provider '{requested_provider}' is not configured.",
                    requested_provider,
                )
        else:
            reason = "explicit provider"

    provider = requested_provider
    reason = "explicit provider"  # Default reason

    is_local = provider in {"ollama", "lmstudio", "fastchat", "text-generation-webui"}

    api_key = _resolve_api_key(
        settings=settings,
        provider=provider,
        api_key_override=api_key_override,
    )
    base_url = _resolve_base_url(
        settings=settings,
        provider=provider,
        base_url_override=base_url_override,
    )
    model = _resolve_model(
        settings=settings,
        provider=provider,
        is_local=is_local,
        model_override=model_override,
    )

    return ResolvedProviderConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        is_local=is_local,
        selection_reason=reason,
    )


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s.lower() if s else None


def _resolve_auto_select_order(settings) -> Tuple[Iterable[str], str]:
    order_raw = getattr(settings, "ai_auto_select_order", None) or os.getenv("AI_AUTO_SELECT_ORDER")
    if not order_raw:
        return DEFAULT_AUTO_SELECT_ORDER, "default"

    parts = [_normalize(p) for p in str(order_raw).split(",")]
    normalized = [p for p in parts if p]
    return (normalized or DEFAULT_AUTO_SELECT_ORDER), "env"


def _pick_first_in_order(configured: list[str], order: Iterable[str]) -> Optional[str]:
    configured_set = set(configured)
    for candidate in order:
        if candidate in configured_set:
            return candidate
    return None


def _detect_configured_providers(settings) -> list[str]:
    configured: list[str] = []

    hosted_api_key_env = {
        "openai": _non_empty(getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")),
        "groq": _non_empty(getattr(settings, "groq_api_key", None) or os.getenv("GROQ_API_KEY")),
        "together": _non_empty(getattr(settings, "together_api_key", None) or os.getenv("TOGETHER_API_KEY")),
        "openrouter": _non_empty(getattr(settings, "openrouter_api_key", None) or os.getenv("OPENROUTER_API_KEY")),
    }

    local_base_url_env = {
        "ollama": _non_empty(getattr(settings, "ollama_base_url", None) or os.getenv("OLLAMA_BASE_URL")),
        "lmstudio": _non_empty(getattr(settings, "lmstudio_base_url", None) or os.getenv("LMSTUDIO_BASE_URL")),
        "fastchat": _non_empty(getattr(settings, "fastchat_base_url", None) or os.getenv("FASTCHAT_BASE_URL")),
        "text-generation-webui": _non_empty(
            getattr(settings, "text_generation_webui_base_url", None)
            or os.getenv("TEXT_GENERATION_WEBUI_BASE_URL")
        ),
    }

    openai_compatible_configured = _non_empty(getattr(settings, "base_url", None) or os.getenv("AI_BASE_URL"))

    for provider, present in hosted_api_key_env.items():
        if present:
            configured.append(provider)

    # Legacy compatibility: a lone AI_API_KEY historically implied OpenAI.
    # This keeps auto-selection deterministic while preserving older setups.
    if "openai" not in configured:
        legacy_ai_api_key = getattr(settings, "api_key", None) or os.getenv("AI_API_KEY")
        if _non_empty(str(legacy_ai_api_key) if legacy_ai_api_key else None):
            configured.append("openai")

    for provider, present in local_base_url_env.items():
        if present:
            configured.append(provider)

    if openai_compatible_configured:
        configured.append("openai_compatible")

    return configured


def _non_empty(value: Optional[str]) -> bool:
    return bool(value and str(value).strip())


def _resolve_api_key(*, settings, provider: str, api_key_override: Optional[str]) -> Optional[str]:
    if api_key_override and str(api_key_override).strip():
        return str(api_key_override).strip()

    # Provider-specific keys win
    provider_specific = {
        "openai": getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY"),
        "groq": getattr(settings, "groq_api_key", None) or os.getenv("GROQ_API_KEY"),
        "together": getattr(settings, "together_api_key", None) or os.getenv("TOGETHER_API_KEY"),
        "openrouter": getattr(settings, "openrouter_api_key", None) or os.getenv("OPENROUTER_API_KEY"),
    }.get(provider)

    if provider_specific and str(provider_specific).strip():
        return str(provider_specific).strip()

    # Generic fallback for legacy users/tests
    generic = getattr(settings, "api_key", None) or os.getenv("AI_API_KEY")
    if generic and str(generic).strip():
        return str(generic).strip()

    # Local providers: keep backward-compatible fallback tokens.
    local_fallbacks = {
        "ollama": "ollama",
        "lmstudio": "lm-studio",
        "text-generation-webui": "webui",
        "fastchat": "fastchat",
    }
    if provider in local_fallbacks:
        return local_fallbacks[provider]

    if provider == "openai_compatible":
        # Allow missing API key so callers/tests can surface a missing-key error
        # after base_url is considered configured.
        return None

    raise ProviderConfigurationError(
        "API key is required. Set provider-specific <PROVIDER>_API_KEY or AI_API_KEY.",
        provider,
    )


def _resolve_base_url(*, settings, provider: str, base_url_override: Optional[str]) -> Optional[str]:
    if base_url_override and str(base_url_override).strip():
        return str(base_url_override).strip()

    provider_specific = {
        "openai": getattr(settings, "openai_base_url", None) or os.getenv("OPENAI_BASE_URL"),
        "groq": getattr(settings, "groq_base_url", None) or os.getenv("GROQ_BASE_URL"),
        "together": getattr(settings, "together_base_url", None) or os.getenv("TOGETHER_BASE_URL"),
        "openrouter": getattr(settings, "openrouter_base_url", None) or os.getenv("OPENROUTER_BASE_URL"),
        "ollama": getattr(settings, "ollama_base_url", None) or os.getenv("OLLAMA_BASE_URL"),
        "lmstudio": getattr(settings, "lmstudio_base_url", None) or os.getenv("LMSTUDIO_BASE_URL"),
        "fastchat": getattr(settings, "fastchat_base_url", None) or os.getenv("FASTCHAT_BASE_URL"),
        "text-generation-webui": getattr(settings, "text_generation_webui_base_url", None)
        or os.getenv("TEXT_GENERATION_WEBUI_BASE_URL"),
    }.get(provider)

    if provider_specific and str(provider_specific).strip():
        return str(provider_specific).strip()

    generic = getattr(settings, "base_url", None) or os.getenv("AI_BASE_URL")
    if generic and str(generic).strip():
        return str(generic).strip()

    defaults = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": "http://localhost:11434/v1",
        "lmstudio": "http://localhost:1234/v1",
        "fastchat": "http://localhost:8000/v1",
        "text-generation-webui": "http://localhost:5000/v1",
    }

    default = defaults.get(provider)
    if default:
        return default

    if provider == "openai_compatible":
        return None

    raise ProviderConfigurationError("Base URL is required.", provider)


def _resolve_model(
    *,
    settings,
    provider: str,
    is_local: bool,
    model_override: Optional[str],
) -> str:
    if model_override and str(model_override).strip():
        return str(model_override).strip()

    provider_specific = {
        "openai": getattr(settings, "openai_model", None) or os.getenv("OPENAI_MODEL"),
        "groq": getattr(settings, "groq_model", None) or os.getenv("GROQ_MODEL"),
        "together": getattr(settings, "together_model", None) or os.getenv("TOGETHER_MODEL"),
        "openrouter": getattr(settings, "openrouter_model", None) or os.getenv("OPENROUTER_MODEL"),
        "ollama": getattr(settings, "ollama_model", None) or os.getenv("OLLAMA_MODEL"),
        "lmstudio": getattr(settings, "lmstudio_model", None) or os.getenv("LMSTUDIO_MODEL"),
        "fastchat": getattr(settings, "fastchat_model", None) or os.getenv("FASTCHAT_MODEL"),
        "text-generation-webui": getattr(settings, "text_generation_webui_model", None)
        or os.getenv("TEXT_GENERATION_WEBUI_MODEL"),
    }.get(provider)

    if provider_specific and str(provider_specific).strip():
        return str(provider_specific).strip()

    generic = getattr(settings, "model", None) or os.getenv("AI_MODEL")
    if generic and str(generic).strip():
        return str(generic).strip()

    if is_local:
        raise ProviderConfigurationError(
            "Model is required for local providers. Set <PROVIDER>_MODEL or AI_MODEL.",
            provider,
        )

    if provider == "openai_compatible":
        raise ProviderConfigurationError(
            "Model is required. Set AI_MODEL.",
            provider,
        )

    # Hosted provider defaults
    hosted_defaults = {
        "openai": "gpt-3.5-turbo",
        "groq": "llama3-70b-8192",
        "together": "meta-llama/Llama-3-8b-chat-hf",
        "openrouter": "meta-llama/llama-3-8b-instruct:free",
    }
    default = hosted_defaults.get(provider)
    if default:
        return default

    raise ProviderConfigurationError("Model is required.", provider)
