"""
ai_utilities - Clean v1 library for AI integrations.

This package provides tools for AI integration with explicit configuration
and no import-time side effects, including audio processing capabilities.

Main Classes:
    AiSettings: Configuration settings for AI client
    AiClient: Main AI client for making requests
    AudioProcessor: Audio transcription and generation

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
    settings = AiSettings(api_key="your-key", model="test-model-1")
    client = AiClient(settings)
    response = client.ask_json("List 5 AI trends")
"""

from .async_client import AsyncAiClient
from .client import AiClient, AiSettings, create_client
from .file_models import UploadedFile
from .json_parsing import JsonParseError, parse_json_from_text
from .models import AskResult
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
    UsageTracker,
    create_usage_tracker,
)
from .audio import (
    AudioProcessor,
    AudioFormat,
    AudioFile,
    TranscriptionRequest,
    TranscriptionResult,
    AudioGenerationRequest,
    AudioGenerationResult,
    load_audio_file,
    save_audio_file,
    validate_audio_file,
    get_audio_info,
)

__all__ = [
    'AiClient',
    'AsyncAiClient',
    'AiSettings', 
    'create_client',
    'AskResult',
    'UploadedFile',
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
    'ProviderConfigurationError',
    'FileTransferError',
    # Audio processing
    'AudioProcessor',
    'AudioFormat',
    'AudioFile',
    'TranscriptionRequest',
    'TranscriptionResult',
    'AudioGenerationRequest',
    'AudioGenerationResult',
    'load_audio_file',
    'save_audio_file',
    'validate_audio_file',
    'get_audio_info',
]

# Version - automatically retrieved from package metadata
try:
    from importlib.metadata import version
    __version__ = version("ai-utilities")
except ImportError:
    # Fallback for older Python versions or when package is not installed
    __version__ = "0.5.0"  # Should match pyproject.toml version
