"""
Configuration resolver for multi-provider support.

Handles resolution of provider, API key, and base URL with proper precedence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class UnknownProviderError(Exception):
    """Raised when an unknown provider is specified."""
    pass


class MissingApiKeyError(Exception):
    """Raised when no API key is available for a cloud provider."""
    pass


class MissingBaseUrlError(Exception):
    """Raised when a base_url is required but missing."""
    pass


@dataclass
class ResolvedConfig:
    """Resolved configuration for a request."""
    provider: str
    api_key: str
    base_url: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[float] = None
    
    # Provider-specific settings
    provider_kwargs: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.provider_kwargs is None:
            self.provider_kwargs = {}


def resolve_provider(
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    env_provider: Optional[str] = None
) -> str:
    """Resolve provider using precedence rules.
    
    Args:
        provider: Per-request provider override
        base_url: Base URL to infer provider from
        env_provider: Environment AI_PROVIDER
        
    Returns:
        Provider name (lowercase)
        
    Raises:
        UnknownProviderError: If provider cannot be determined
    """
    valid_providers = {
        "openai",
        "groq",
        "together", 
        "openrouter",
        "ollama",
        "lmstudio",
        "text-generation-webui",
        "fastchat",
        "openai_compatible",
        # Additional providers from documentation
        "anyscale",
        "fireworks", 
        "replicate",
        "vllm",
        "oobabooga",
        "localai",
        "azure",
        "google-vertex",
        "aws-bedrock", 
        "ibm-watsonx",
    }

    def _validate(name: str) -> str:
        normalized = name.lower()
        if normalized not in valid_providers:
            raise UnknownProviderError(f"Unknown provider: {normalized}")
        return normalized

    # 1) Per-request provider wins
    if provider:
        return _validate(provider)
    
    # 2) Settings/provider provider
    # (This will be handled by caller passing settings.provider)
    
    # 3) Environment AI_PROVIDER
    if env_provider:
        return _validate(env_provider)
    
    # 4) Infer from base_url
    if base_url:
        return _infer_provider_from_url(base_url)
    
    # 5) Infer from provider-specific base URLs in environment
    env_provider = _infer_provider_from_env_base_urls()
    if env_provider:
        return _validate(env_provider)
    
    # 6) Default to OpenAI
    return "openai"


def _infer_provider_from_url(base_url: str) -> str:
    """Infer provider from base URL pattern.
    
    Args:
        base_url: The base URL to analyze
        
    Returns:
        Provider name
        
    Raises:
        UnknownProviderError: If provider cannot be inferred
    """
    parsed = urlparse(base_url)
    hostname = parsed.hostname or ""
    port = parsed.port
    
    # Local providers
    if hostname == "localhost" or hostname == "127.0.0.1":
        if port == 11434:
            return "ollama"
        elif port == 1234:
            return "lmstudio"
        elif port == 5000:
            return "text-generation-webui"
        elif port == 8000:
            return "fastchat"
    
    # Check hostname patterns
    if "api.openai.com" in hostname:
        return "openai"
    elif "api.groq.com" in hostname:
        return "groq"
    elif "api.together.xyz" in hostname:
        return "together"
    elif "openrouter.ai" in hostname:
        return "openrouter"
    
    # Default to openai-compatible for custom endpoints
    return "openai_compatible"


def _infer_provider_from_env_base_urls() -> Optional[str]:
    """Infer provider from provider-specific base URL environment variables.
    
    Returns:
        Provider name if found, None otherwise
    """
    import os
    
    # Check for provider-specific base URLs in order of preference
    provider_base_url_mapping = {
        "TEXT_GENERATION_WEBUI_BASE_URL": "text-generation-webui",
        "FASTCHAT_BASE_URL": "fastchat", 
        "OLLAMA_BASE_URL": "ollama",
        "LMSTUDIO_BASE_URL": "lmstudio",
    }
    
    for env_var, provider in provider_base_url_mapping.items():
        if os.getenv(env_var):
            return provider
    
    return None


def _get_provider_specific_base_url(provider: str) -> Optional[str]:
    """Get provider-specific base URL from environment variables.
    
    Args:
        provider: Provider name
        
    Returns:
        Provider-specific base URL or None if not found
    """
    import os
    
    # Mapping of providers to their specific environment variables
    provider_base_url_mapping = {
        "text_generation_webui": "TEXT_GENERATION_WEBUI_BASE_URL",
        "fastchat": "FASTCHAT_BASE_URL",
        "ollama": "OLLAMA_BASE_URL", 
        "lmstudio": "LMSTUDIO_BASE_URL",
        "text-generation-webui": "TEXT_GENERATION_WEBUI_BASE_URL",  # Alternative naming
    }
    
    env_var = provider_base_url_mapping.get(provider.lower())
    if env_var:
        return os.getenv(env_var)
    
    return None


def resolve_api_key(
    provider: str,
    api_key: Optional[str] = None,
    settings_api_key: Optional[str] = None,
    settings: Optional[Any] = None,
    env_vars: Optional[Dict[str, str]] = None
) -> str:
    """Resolve API key using precedence rules.
    
    Args:
        provider: Resolved provider name
        api_key: Per-request API key override
        settings_api_key: Settings API_KEY (from AI_API_KEY)
        settings: AiSettings instance with vendor-specific keys
        env_vars: Environment variables dict
        
    Returns:
        Resolved API key
        
    Raises:
        MissingApiKeyError: If no API key is available for cloud providers
    """
    if env_vars is None:
        env_vars = {}
    
    # 1) Per-request API key wins
    if api_key:
        return api_key
    
    # 2) Settings API_KEY (AI_API_KEY override)
    if settings_api_key:
        return settings_api_key
    
    # 3) Vendor-specific key from settings
    if settings:
        vendor_key = _get_vendor_key_from_settings(provider, settings)
        if vendor_key:
            return vendor_key
    
    # 4) Vendor-specific key from environment
    vendor_key = _get_vendor_key_for_provider(provider, env_vars)
    if vendor_key:
        return vendor_key
    
    # 5) For local providers, allow fallback tokens
    if provider == "openai_compatible":
        return "dummy-key"
    if provider in ["ollama", "lmstudio", "text-generation-webui", "fastchat"]:
        fallbacks = {
            "ollama": "ollama",
            "lmstudio": "lm-studio", 
            "text-generation-webui": "webui",
            "fastchat": "fastchat"
        }
        return fallbacks.get(provider, "not-required")
    
    # 6) Cloud providers must have API keys
    if provider == "openai":
        raise MissingApiKeyError("API key is required")
    raise MissingApiKeyError(f"No API key found for provider '{provider}'. "
                           f"Set {provider.upper()}_API_KEY environment variable.")


def _get_vendor_key_from_settings(provider: str, settings) -> Optional[str]:
    """Get vendor-specific API key from AiSettings.
    
    Args:
        provider: Provider name
        settings: AiSettings instance
        
    Returns:
        API key or None if not found
    """
    key_mapping = {
        "openai": "openai_api_key",
        "groq": "groq_api_key", 
        "together": "together_api_key",
        "openrouter": "openrouter_api_key",
        "ollama": "ollama_api_key",
        "lmstudio": "lmstudio_api_key",
    }
    
    attr_name = key_mapping.get(provider)
    if attr_name and hasattr(settings, attr_name):
        return getattr(settings, attr_name)
    
    return None


def _get_vendor_key_for_provider(provider: str, env_vars: Dict[str, str]) -> Optional[str]:
    """Get vendor-specific API key for provider.
    
    Args:
        provider: Provider name
        env_vars: Environment variables
        
    Returns:
        API key or None if not found
    """
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY", 
        "together": "TOGETHER_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai_compatible": "AI_API_KEY",  # Fallback for custom endpoints
        # Additional providers from documentation
        "anyscale": "ANYSCALE_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
        "azure": "AZURE_OPENAI_API_KEY",
        "google-vertex": "GOOGLE_APPLICATION_CREDENTIALS",
        "aws-bedrock": "AWS_ACCESS_KEY_ID",  # Simplified - would need full AWS auth
        "ibm-watsonx": "IBM_CLOUD_API_KEY",
    }
    
    env_key = key_mapping.get(provider)
    if env_key:
        return env_vars.get(env_key)
    
    return None


def resolve_base_url(
    provider: str,
    base_url: Optional[str] = None,
    settings_base_url: Optional[str] = None
) -> str:
    """Resolve base URL using precedence rules.
    
    Args:
        provider: Resolved provider name
        base_url: Per-request base URL override
        settings_base_url: Settings BASE_URL (from AI_BASE_URL)
        
    Returns:
        Resolved base URL
    """
    # 1) Per-request base URL wins
    if base_url:
        return base_url
    
    # 2) Settings base URL (AI_BASE_URL)
    if settings_base_url:
        return settings_base_url
    
    # 3) Provider-specific base URLs from environment
    provider_base_url = _get_provider_specific_base_url(provider)
    if provider_base_url:
        return provider_base_url
    
    # 4) Provider default base URL
    if provider == "openai_compatible":
        raise MissingBaseUrlError("base_url is required")

    defaults = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": "http://localhost:11434/v1",
        "lmstudio": "http://localhost:1234/v1",
        "text-generation-webui": "http://localhost:5000/v1",
        "fastchat": "http://localhost:8000/v1",
        # Additional providers from documentation
        "anyscale": "https://api.endpoints.anyscale.com/v1",
        "fireworks": "https://api.fireworks.ai/inference/v1",
        "replicate": "https://api.replicate.com/v1",
        "vllm": "http://localhost:8000/v1",
        "oobabooga": "http://localhost:7860/v1", 
        "localai": "http://localhost:8080/v1",
        "azure": "https://your-resource.openai.azure.com",
        "google-vertex": "https://us-central1-aiplatform.googleapis.com/v1",
        "aws-bedrock": "https://bedrock-runtime.us-east-1.amazonaws.com",
        "ibm-watsonx": "https://us-south.ml.cloud.ibm.com",
    }
    
    return defaults.get(provider, "https://api.openai.com/v1")


def resolve_request_config(
    settings,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> ResolvedConfig:
    """Resolve complete request configuration.
    
    Args:
        settings: AiSettings instance
        provider: Per-request provider override
        api_key: Per-request API key override
        base_url: Per-request base URL override
        model: Per-request model override
        temperature: Per-request temperature override
        max_tokens: Per-request max_tokens override
        timeout: Per-request timeout override
        **kwargs: Additional provider-specific parameters
        
    Returns:
        ResolvedConfig with all settings resolved
        
    Raises:
        UnknownProviderError: If provider cannot be determined
        MissingApiKeyError: If no API key is available for cloud providers
    """
    import os
    
    # Get environment variables
    env_vars = dict(os.environ)
    
    # Resolve provider
    resolved_provider = resolve_provider(
        provider=provider,
        base_url=base_url or settings.base_url,
        env_provider=getattr(settings, 'provider', None) or env_vars.get('AI_PROVIDER')
    )
    
    # Resolve API key
    resolved_api_key = resolve_api_key(
        provider=resolved_provider,
        api_key=api_key,
        settings_api_key=settings.api_key,
        settings=settings,
        env_vars=env_vars
    )
    
    # Resolve base URL
    try:
        resolved_base_url = resolve_base_url(
            provider=resolved_provider,
            base_url=base_url,
            settings_base_url=settings.base_url
        )
    except MissingBaseUrlError as e:
        raise MissingBaseUrlError(str(e))  # Re-raise so provider_factory can catch it 
        
    # Resolve other parameters (per-request wins, then settings)
    resolved_model = model or settings.model
    resolved_temperature = temperature or settings.temperature
    resolved_max_tokens = max_tokens or getattr(settings, 'max_tokens', None)
    resolved_timeout = timeout or settings.request_timeout_s or settings.timeout
    
    # Provider-specific kwargs
    provider_kwargs = kwargs.copy()
    
    return ResolvedConfig(
        provider=resolved_provider,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        model=resolved_model,
        temperature=resolved_temperature,
        max_tokens=resolved_max_tokens,
        timeout=resolved_timeout,
        provider_kwargs=provider_kwargs
    )
