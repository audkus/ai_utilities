"""
ai_utilities - Clean v1 library for AI integrations.

This package provides tools for AI integration with explicit configuration
and no import-time side effects.

Main Classes:
    AiSettings: Configuration settings for AI client
    AiClient: Main AI client for making requests

Example Usage:
    from ai_utilities import AiClient, AiSettings
    
    # Using environment variables
    client = AiClient()
    response = client.ask("What is the capital of France?")
    
    # Using explicit settings
    settings = AiSettings(api_key="your-key", model="test-model-1")
    client = AiClient(settings)
    response = client.ask_json("List 5 AI trends")
"""

from .async_client import AsyncAiClient
from .client import AiClient, AiSettings, create_client
from .models import AskResult
from .json_parsing import JsonParseError, parse_json_from_text
from .rate_limit_fetcher import RateLimitFetcher, RateLimitInfo
from .token_counter import TokenCounter
from .usage_tracker import (
    ThreadSafeUsageTracker,
    UsageScope,
    UsageStats,
    UsageTracker,
    create_usage_tracker,
)
from .providers import (
    BaseProvider,
    OpenAIProvider,
    OpenAICompatibleProvider,
    create_provider,
    ProviderCapabilities,
    ProviderCapabilityError,
    ProviderConfigurationError,
)

__all__ = [
    'AiClient',
    'AsyncAiClient',
    'AiSettings', 
    'create_client',
    'AskResult',
    'JsonParseError',
    'parse_json_from_text',
    'UsageTracker',
    'ThreadSafeUsageTracker',
    'UsageScope',
    'UsageStats',
    'create_usage_tracker',
    'TokenCounter',
    'RateLimitFetcher',
    'RateLimitInfo',
    'BaseProvider',
    'OpenAIProvider',
    'OpenAICompatibleProvider',
    'create_provider',
    'ProviderCapabilities',
    'ProviderCapabilityError',
    'ProviderConfigurationError'
]

# Version - automatically retrieved from package metadata
try:
    from importlib.metadata import version
    __version__ = version("ai-utilities")
except ImportError:
    # Fallback for older Python versions or when package is not installed
    __version__ = "0.4.0"  # Should match pyproject.toml version
