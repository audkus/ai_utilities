"""Audio processing utilities for AI applications.

This module provides audio processing capabilities including:
- Audio file loading and validation
- Audio format conversion
- Audio transcription via AI providers
- Audio generation via AI providers
- Audio analysis and manipulation

The audio processing is designed to work seamlessly with the existing
AI utilities architecture and providers.
"""

from .audio_models import (
    AudioFormat,
    AudioFile,
    TranscriptionRequest,
    TranscriptionResult,
    AudioGenerationRequest,
    AudioGenerationResult,
)

from .audio_processor import AudioProcessor
from .audio_utils import (
    load_audio_file,
    save_audio_file,
    convert_audio_format,
    validate_audio_file,
    get_audio_info,
)

__all__ = [
    # Models
    "AudioFormat",
    "AudioFile", 
    "TranscriptionRequest",
    "TranscriptionResult",
    "AudioGenerationRequest",
    "AudioGenerationResult",
    # Main processor
    "AudioProcessor",
    # Utilities
    "load_audio_file",
    "save_audio_file",
    "convert_audio_format",
    "validate_audio_file",
    "get_audio_info",
]
