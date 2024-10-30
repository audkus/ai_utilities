"""
ai_utilities package initialization.

This package provides tools for AI integration, including interaction with AI models,
rate limiting, configuration management, and the ability to track AI response times.

Public Modules and Functions:
    - get_model_from_config
    - set_default_ai_config
    - set_default_model_configs
    - RateLimiter
    - ask_ai
    - is_ai_usage_enabled
    - AICallTimer

Example Usage:
    from ai_utilities import ask_ai, is_ai_usage_enabled, AICallTimer

    if is_ai_usage_enabled():
        with AICallTimer():
            response = ask_ai("Your prompt here")
            print(response)
"""

# Local application imports
from .ai_config_manager import (
    get_model_from_config,
    set_default_ai_config,
    set_default_model_configs,
)
from .rate_limiter import RateLimiter
from .ai_integration import ask_ai, is_ai_usage_enabled
from .ai_call_timer import AICallTimer

__all__ = [
    'get_model_from_config',
    'set_default_ai_config',
    'set_default_model_configs',
    'RateLimiter',
    'ask_ai',
    'is_ai_usage_enabled',
    'AICallTimer',
]
