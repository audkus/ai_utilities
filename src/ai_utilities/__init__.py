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

from .client import AiClient, AiSettings, create_client
from .async_client import AsyncAiClient
from .models import AskResult
from .usage_tracker import UsageTracker, ThreadSafeUsageTracker, UsageScope, UsageStats, create_usage_tracker
from .token_counter import TokenCounter
from .rate_limit_fetcher import RateLimitFetcher, RateLimitInfo

__all__ = [
    'AiClient',
    'AsyncAiClient',
    'AiSettings', 
    'create_client',
    'AskResult',
    'UsageTracker',
    'ThreadSafeUsageTracker',
    'UsageScope',
    'UsageStats',
    'create_usage_tracker',
    'TokenCounter',
    'RateLimitFetcher',
    'RateLimitInfo'
]

# Version
__version__ = "1.0.0"
