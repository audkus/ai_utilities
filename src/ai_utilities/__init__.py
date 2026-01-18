"""
ai_utilities - Clean v1 library for AI integrations.

This package provides tools for AI integration with explicit configuration
and no import-time side effects, including audio processing capabilities.

🚀 STABLE PUBLIC API (v1.x):
    Core classes and functions that are guaranteed to remain stable:
    - AiClient, AsyncAiClient, AiSettings, create_client
    - AskResult, UploadedFile
    - JsonParseError, parse_json_from_text
    - AudioProcessor, load_audio_file, save_audio_file, validate_audio_file, get_audio_info

📦 COMPATIBILITY EXPORTS:
    Available for backwards compatibility but may change in future releases:
    - Usage tracking: UsageTracker*, create_usage_tracker
    - Rate limiting: RateLimitFetcher, RateLimitInfo
    - Token counting: TokenCounter
    - Providers: BaseProvider, OpenAIProvider, create_provider, etc.
    - Audio models: AudioFormat, TranscriptionRequest, etc.

    (*) Consider using ai_utilities.usage, ai_utilities.rate_limit, etc. in future.

Example Usage:
    from ai_utilities import AiClient, AiSettings
    
    # Using environment variables
    client = AiClient()
    response = client.ask("What is the capital of France?")
    
    # Audio transcription
    result = client.transcribe_audio("recording.wav")
    print(result["text"])
    
    # Audio generation
    audio_data = client.generate_audio("Hello, world!", voice="nova")
    
    # Using explicit settings
    settings = AiSettings(api_key="your-key", model="gpt-4")
    client = AiClient(settings)
    response = client.ask_json("List 5 AI trends")
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import TYPE_CHECKING, Any

# Lazy submodule support for patching in tests
_LAZY_SUBMODULES: dict[str, str] = {
    # submodule attribute -> real module path
    "_test_reset": "ai_utilities._test_reset",
    "ai_config_manager": "ai_utilities.ai_config_manager", 
    "api_key_resolver": "ai_utilities.api_key_resolver",
    "async_client": "ai_utilities.async_client",
    "audio": "ai_utilities.audio",
    "cache": "ai_utilities.cache",
    "cli": "ai_utilities.cli",
    "client": "ai_utilities.client",
    "config_models": "ai_utilities.config_models",
    "config_resolver": "ai_utilities.config_resolver",
    "context": "ai_utilities.context",
    "di": "ai_utilities.di",
    "env_detection": "ai_utilities.env_detection",
    "env_overrides": "ai_utilities.env_overrides",
    "env_utils": "ai_utilities.env_utils",
    "error_codes": "ai_utilities.error_codes",
    "exceptions": "ai_utilities.exceptions",
    "file_models": "ai_utilities.file_models",
    "json_parsing": "ai_utilities.json_parsing",
    "knowledge": "ai_utilities.knowledge",
    "metrics": "ai_utilities.metrics",
    "models": "ai_utilities.models",
    "openai_client": "ai_utilities.openai_client",
    "openai_model": "ai_utilities.openai_model",
    "progress_indicator": "ai_utilities.progress_indicator",
    "providers": "ai_utilities.providers",
    "rate_limit_fetcher": "ai_utilities.rate_limit_fetcher",
    "rate_limiter": "ai_utilities.rate_limiter",
    "response_processor": "ai_utilities.response_processor",
    "setup": "ai_utilities.setup",
    "ssl_check": "ai_utilities.ssl_check",
    "token_counter": "ai_utilities.token_counter",
    "usage_tracker": "ai_utilities.usage_tracker",
}

# Core imports - these are lightweight and essential
from .async_client import AsyncAiClient
from .client import AiClient, create_client
from .config_models import AiSettings
from .file_models import UploadedFile
from .json_parsing import JsonParseError, parse_json_from_text
from .models import AskResult

# Type checking imports - only available during type checking, not at runtime
if TYPE_CHECKING:
    from .audio import (
        AudioProcessor,
        load_audio_file,
        save_audio_file,
        validate_audio_file,
        get_audio_info,
        AudioFormat,
        AudioFile,
        TranscriptionRequest,
        TranscriptionResult,
        AudioGenerationRequest,
        AudioGenerationResult,
    )
    from .usage_tracker import UsageTracker, create_usage_tracker
    from .openai_client import OpenAIClient
    from .providers import (
        BaseProvider,
        FileTransferError,
        OpenAICompatibleProvider,
        OpenAIProvider,
        ProviderCapabilities,
        ProviderCapabilityError,
        ProviderConfigurationError,
        create_provider,
    )
    from .rate_limit_fetcher import RateLimitFetcher, RateLimitInfo
    from .token_counter import TokenCounter
    from .usage_tracker import (
        ThreadSafeUsageTracker,
        UsageScope,
        UsageStats,
    )


def __getattr__(name: str) -> Any:
    """Lazy import heavy modules to avoid import-time side effects."""
    
    # Handle lazy submodules first (for test patching)
    if name in _LAZY_SUBMODULES:
        module: ModuleType = importlib.import_module(_LAZY_SUBMODULES[name])
        globals()[name] = module  # Cache for future access
        return module
    
    # Audio processing
    if name in {
        'AudioProcessor', 'load_audio_file', 'save_audio_file', 
        'validate_audio_file', 'get_audio_info', 'AudioFormat',
        'AudioFile', 'TranscriptionRequest', 'TranscriptionResult',
        'AudioGenerationRequest', 'AudioGenerationResult'
    }:
        from .audio import (
            AudioProcessor,
            load_audio_file,
            save_audio_file,
            validate_audio_file,
            get_audio_info,
            AudioFormat,
            AudioFile,
            TranscriptionRequest,
            TranscriptionResult,
            AudioGenerationRequest,
            AudioGenerationResult,
        )
        return locals()[name]
    
    # Usage tracking
    elif name in {'UsageTracker', 'create_usage_tracker'}:
        from .usage_tracker import UsageTracker, create_usage_tracker
        return locals()[name]
    
    # OpenAI client (for testing)
    elif name == 'OpenAIClient':
        from .openai_client import OpenAIClient
        return OpenAIClient
    
    # Providers
    elif name in {
        'BaseProvider', 'FileTransferError', 'OpenAICompatibleProvider',
        'OpenAIProvider', 'ProviderCapabilities', 'ProviderCapabilityError',
        'ProviderConfigurationError', 'create_provider'
    }:
        from .providers import (
            BaseProvider,
            FileTransferError,
            OpenAICompatibleProvider,
            OpenAIProvider,
            ProviderCapabilities,
            ProviderCapabilityError,
            ProviderConfigurationError,
            create_provider,
        )
        return locals()[name]
    
    # Rate limiting
    elif name in {'RateLimitFetcher', 'RateLimitInfo'}:
        from .rate_limit_fetcher import RateLimitFetcher, RateLimitInfo
        return locals()[name]
    
    # Token counting
    elif name == 'TokenCounter':
        from .token_counter import TokenCounter
        return TokenCounter
    
    # Usage tracker internals
    elif name in {'ThreadSafeUsageTracker', 'UsageScope', 'UsageStats'}:
        from .usage_tracker import (
            ThreadSafeUsageTracker,
            UsageScope,
            UsageStats,
        )
        return locals()[name]
    
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Stable public API exports - these are guaranteed to remain stable in v1.x
__all__ = [
    # Core client classes
    'AiClient',
    'AsyncAiClient', 
    'AiSettings',
    'create_client',
    'AskResult',
    
    # File handling
    'UploadedFile',
    'JsonParseError', 
    'parse_json_from_text',
    
    # Usage tracking
    'UsageTracker',
    'create_usage_tracker',
    
    # OpenAI client (internal, for testing)
    'OpenAIClient',
    
    # Audio processing (stable but may be moved to submodule in future)
    'AudioProcessor',
    'load_audio_file',
    'save_audio_file',
    'validate_audio_file',
    'get_audio_info',
    
    # Compatibility exports (available but not guaranteed stable)
    'ThreadSafeUsageTracker', 
    'UsageScope',
    'UsageStats',
    'RateLimitFetcher',
    'RateLimitInfo',
    'TokenCounter',
    'BaseProvider',
    'OpenAIProvider',
    'OpenAICompatibleProvider', 
    'create_provider',
    'ProviderCapabilities',
    'ProviderCapabilityError',
    'ProviderConfigurationError',
    'FileTransferError',
    'AudioFormat',
    'AudioFile',
    'TranscriptionRequest',
    'TranscriptionResult',
    'AudioGenerationRequest',
    'AudioGenerationResult',
]

# Version - automatically retrieved from package metadata
try:
    from importlib.metadata import version
    __version__ = version("ai-utilities")
except ImportError:
    # Fallback for older Python versions or when package is not installed
    __version__ = "1.0.0b2"  # Should match pyproject.toml version

# SSL Backend Compatibility Check
# This checks for LibreSSL compatibility issues and provides clear user feedback
from .ssl_check import require_ssl_backend
require_ssl_backend()
