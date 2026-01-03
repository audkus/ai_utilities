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
    settings = AiSettings(api_key="your-key", model="test-model-1")
    client = AiClient(settings)
    response = client.ask_json("List 5 AI trends")
"""

from .async_client import AsyncAiClient
from .client import AiClient, create_client
from .config_models import AiSettings
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
