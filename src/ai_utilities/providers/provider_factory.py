"""Provider factory for creating AI providers based on settings."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, List

from .base_provider import BaseProvider
from .provider_exceptions import ProviderConfigurationError, MissingOptionalDependencyError
from ..config_resolver import resolve_request_config, MissingApiKeyError, UnknownProviderError, MissingBaseUrlError, MissingModelError

if TYPE_CHECKING:
    from ..client import AiSettings


def _coerce_timeout_seconds(value: object, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return default


def list_supported_providers() -> List[str]:
    """List all supported provider identifiers.
    
    Returns:
        List of supported provider names in alphabetical order.
        This function has no side effects and doesn't require any imports
        beyond the standard library.
        
    Note:
        This is the authoritative source of truth for supported providers.
        Do not duplicate this list elsewhere - always import this function.
    """
    # This list must match the valid_providers set in config_resolver.py
    return [
        "fastchat",
        "lmstudio", 
        "ollama",
        "openai",
        "openai_compatible",
        "openrouter",
        "text-generation-webui",
        "together",
        "groq",
    ]


def create_provider(settings: "AiSettings", provider: Optional[BaseProvider] = None) -> BaseProvider:
    """Create an AI provider based on settings.
    
    Args:
        settings: AI settings containing provider configuration
        provider: Optional explicit provider to use (overrides settings)
        
    Returns:
        Configured AI provider instance
    
    Raises:
        ProviderConfigurationError: If provider configuration is invalid
    """
    # If explicit provider is provided, use it
    if provider is not None:
        return provider
    
    # Check if settings is None
    if settings is None:
        raise ProviderConfigurationError("Settings cannot be None", "unknown")
    
    try:
        config = resolve_request_config(settings)

        # Ensure the provider instance sees resolved values (api_key/base_url/model)
        # without mutating the original settings object.
        update_data = {
            "provider": config.provider,
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": getattr(config, "model", None),
            "timeout": _coerce_timeout_seconds(getattr(config, "timeout", None), 30),
        }
        provider_settings = settings.model_copy(update=update_data)

        # Create provider based on resolved provider
        if config.provider == "openai":
            # Lazy import to avoid dependency issues
            try:
                from .openai_provider import OpenAIProvider
            except ImportError as e:
                raise MissingOptionalDependencyError(
                    "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                ) from e
            return OpenAIProvider(provider_settings)

        elif config.provider in ["groq", "together", "openrouter"]:
            # These are all OpenAI-compatible with different base URLs
            from .openai_compatible_provider import OpenAICompatibleProvider
            extra_headers = getattr(settings, 'extra_headers', None) if hasattr(settings, 'extra_headers') else None
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=_coerce_timeout_seconds(getattr(settings, "timeout", None), 30),
                extra_headers=extra_headers,
                model=getattr(config, 'model', None),
            )

        elif config.provider in ["ollama", "lmstudio", "text-generation-webui", "fastchat", "openai_compatible"]:
            # Local providers
            from .openai_compatible_provider import OpenAICompatibleProvider
            extra_headers = getattr(settings, 'extra_headers', None) if hasattr(settings, 'extra_headers') else None
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=_coerce_timeout_seconds(getattr(config, "timeout", None), 30),
                extra_headers=extra_headers,
                model=getattr(config, 'model', None),
            )

        else:
            raise ProviderConfigurationError(
                f"Unknown provider: {config.provider}",
                config.provider
            )

    except MissingBaseUrlError as e:
        raise ProviderConfigurationError(str(e), getattr(settings, "provider", "unknown"))
    except MissingApiKeyError as e:
        provider_name = getattr(settings, "provider", "unknown") or "unknown"
        if provider_name == "openai":
            raise ProviderConfigurationError("API key is required", "openai")
        else:
            raise ProviderConfigurationError(str(e), provider_name)
    except MissingModelError as e:
        raise ProviderConfigurationError(str(e), getattr(settings, "provider", "unknown"))
    except UnknownProviderError as e:
        raise ProviderConfigurationError(str(e), getattr(settings, "provider", "unknown"))
