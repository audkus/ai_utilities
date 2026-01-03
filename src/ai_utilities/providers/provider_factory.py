"""Provider factory for creating AI providers based on settings."""

from typing import Optional, TYPE_CHECKING

from .base_provider import BaseProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from .provider_exceptions import ProviderConfigurationError, MissingOptionalDependencyError
from ..config_resolver import resolve_request_config, MissingApiKeyError, UnknownProviderError, MissingBaseUrlError

if TYPE_CHECKING:
    from ..client import AiSettings


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
    
    try:
        # Resolve configuration using the new resolver
        config = resolve_request_config(settings)

        # Create provider based on resolved provider
        if config.provider == "openai":
            # Lazy import to avoid dependency issues
            try:
                from .openai_provider import OpenAIProvider
            except ImportError as e:
                raise MissingOptionalDependencyError(
                    "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                ) from e
            return OpenAIProvider(settings)

        elif config.provider in ["groq", "together", "openrouter"]:
            # These are all OpenAI-compatible with different base URLs
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=int(config.timeout or 30),
                extra_headers=settings.extra_headers,
            )

        elif config.provider in ["ollama", "lmstudio", "text-generation-webui", "fastchat", "openai_compatible"]:
            # Local providers
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=int(config.timeout or 30),
                extra_headers=settings.extra_headers,
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
    except UnknownProviderError as e:
        raise ProviderConfigurationError(str(e), getattr(settings, "provider", "unknown"))
