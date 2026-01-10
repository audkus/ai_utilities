"""Audio processing data models.

This module contains Pydantic models for audio processing operations,
including file metadata, transcription requests, and generation parameters.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from pydantic import BaseModel, Field, field_validator


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    WEBM = "webm"


class AudioFile(BaseModel):
    """Represents an audio file with metadata."""
    
    file_path: Path = Field(..., description="Path to the audio file")
    format: AudioFormat = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    file_size_bytes: int = Field(..., description="File size in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        """Validate that the file path exists and has a valid extension."""
        if not v.exists():
            raise ValueError(f"Audio file does not exist: {v}")
        return v
    
    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size(cls, v):
        """Validate that file size is positive."""
        if v <= 0:
            raise ValueError("File size must be positive")
        return v
    
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)
    
    @property
    def is_large_file(self) -> bool:
        """Check if file is larger than 25MB (common API limit)."""
        return self.file_size_mb > 25


class TranscriptionRequest(BaseModel):
    """Request for audio transcription."""
    
    audio_file: AudioFile = Field(..., description="Audio file to transcribe")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'es')")
    model: str = Field("whisper-1", description="Transcription model to use")
    prompt: Optional[str] = Field(None, description="Optional prompt to guide transcription")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature")
    response_format: str = Field("json", description="Response format")
    timestamp_granularities: List[str] = Field(default_factory=list, description="Timestamp granularities")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is within valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("response_format")
    @classmethod
    def validate_response_format(cls, v):
        """Validate response format."""
        valid_formats = ["json", "text", "srt", "verbose_json", "vtt"]
        if v not in valid_formats:
            raise ValueError(f"Response format must be one of: {valid_formats}")
        return v


class TranscriptionSegment(BaseModel):
    """A single segment of transcribed audio."""
    
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    
    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate that end time is after start time."""
        if info.data and "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("End time must be after start time")
        return v


class TranscriptionResult(BaseModel):
    """Result of audio transcription."""
    
    text: str = Field(..., description="Full transcribed text")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    segments: Optional[List[TranscriptionSegment]] = Field(None, description="Timestamped segments")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall confidence")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to process")
    model_used: str = Field(..., description="Model used for transcription")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def word_count(self) -> int:
        """Count of words in the transcription."""
        return len(self.text.split())
    
    @property
    def character_count(self) -> int:
        """Count of characters in the transcription."""
        return len(self.text)


class AudioGenerationRequest(BaseModel):
    """Request for audio generation."""
    
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field("alloy", description="Voice to use for generation")
    model: str = Field("tts-1", description="Text-to-speech model")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="Speech speed factor")
    response_format: AudioFormat = Field(AudioFormat.MP3, description="Output audio format")
    
    @field_validator("speed")
    @classmethod
    def validate_speed(cls, v):
        """Validate speech speed is within valid range."""
        if not 0.25 <= v <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        return v
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate text is not empty and within length limits."""
        if not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) > 4096:  # Common API limit
            raise ValueError("Text is too long (max 4096 characters)")
        return v.strip()


class AudioGenerationResult(BaseModel):
    """Result of audio generation."""
    
    audio_data: bytes = Field(..., description="Generated audio data")
    format: AudioFormat = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Generated audio duration")
    text: str = Field(..., description="Original text that was generated")
    voice: str = Field(..., description="Voice used for generation")
    model_used: str = Field(..., description="Model used for generation")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to generate")
    file_size_bytes: int = Field(..., description="Size of generated audio")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)
    
    def save_to_file(self, file_path: Union[str, Path]) -> Path:
        """Save audio data to a file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            f.write(self.audio_data)
        
        return path


class AudioAnalysisResult(BaseModel):
    """Result of audio analysis."""
    
    audio_file: AudioFile = Field(..., description="Analyzed audio file")
    duration_seconds: float = Field(..., description="Exact duration")
    sample_rate: int = Field(..., description="Sample rate")
    channels: int = Field(..., description="Number of channels")
    bit_depth: Optional[int] = Field(None, description="Bit depth")
    format_details: Dict[str, Any] = Field(default_factory=dict, description="Format-specific details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    
    @property
    def is_stereo(self) -> bool:
        """Check if audio is stereo."""
        return self.channels == 2
    
    @property
    def is_mono(self) -> bool:
        """Check if audio is mono."""
        return self.channels == 1
