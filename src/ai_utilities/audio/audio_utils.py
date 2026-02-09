"""Audio processing utilities.

This module provides basic audio file operations including loading,
saving, format conversion, and validation. Uses Python standard library
and optional dependencies for audio processing.
"""

import mimetypes
from pathlib import Path
from typing import Union, Dict, Any

try:
    import wave
    WAVE_AVAILABLE = True
except ImportError:
    WAVE_AVAILABLE = False

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import pydub
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from .audio_models import AudioFile, AudioFormat, AudioAnalysisResult
from ..exceptions import AudioProcessingError


def validate_audio_file(file_path: Union[str, Path]) -> bool:
    """Validate that a file is a supported audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        True if the file is a valid audio file, False otherwise
    """
    path = Path(file_path)
    
    # Check file exists
    if not path.exists():
        return False
    
    # Check file extension
    valid_extensions = {fmt.value for fmt in AudioFormat}
    if path.suffix.lower().lstrip('.') not in valid_extensions:
        return False
    
    # Check MIME type if available
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type and not mime_type.startswith('audio/'):
        return False
    
    return True


def get_audio_format(file_path: Union[str, Path]) -> AudioFormat:
    """Detect the audio format of a file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        AudioFormat enum value
        
    Raises:
        AudioProcessingError: If format cannot be determined
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip('.')
    
    try:
        return AudioFormat(extension)
    except ValueError:
        # Try to detect from MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type:
            format_map = {
                'audio/wav': AudioFormat.WAV,
                'audio/mpeg': AudioFormat.MP3,
                'audio/flac': AudioFormat.FLAC,
                'audio/ogg': AudioFormat.OGG,
                'audio/mp4': AudioFormat.M4A,
                'audio/webm': AudioFormat.WEBM,
            }
            if mime_type in format_map:
                return format_map[mime_type]
        
        raise AudioProcessingError(f"Unsupported audio format: {extension}")


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size


def load_audio_file(file_path: Union[str, Path]) -> AudioFile:
    """Load an audio file and extract basic metadata.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        AudioFile object with metadata
        
    Raises:
        AudioProcessingError: If file cannot be loaded
    """
    path = Path(file_path)
    
    if not validate_audio_file(path):
        raise AudioProcessingError(f"Invalid or unsupported audio file: {path}")
    
    # Basic file info
    format = get_audio_format(path)
    file_size = get_file_size(path)
    
    # Extract metadata using available libraries
    metadata = {}
    duration = None
    sample_rate = None
    channels = None
    
    # Try to extract metadata using mutagen if available
    if MUTAGEN_AVAILABLE:
        try:
            audio_file = mutagen.File(str(path))
            if audio_file is not None:
                if audio_file.info:
                    duration = audio_file.info.length
                    sample_rate = getattr(audio_file.info, 'sample_rate', None)
                    channels = getattr(audio_file.info, 'channels', None)
                
                # Extract tags
                for key, value in audio_file.items():
                    if isinstance(value, list) and len(value) == 1:
                        metadata[key] = str(value[0])
                    else:
                        metadata[key] = str(value)
        except (ImportError, AttributeError, OSError, Exception):
            # Continue with basic info if mutagen fails or format not supported
            pass
    
    # Try WAV-specific extraction
    if format == AudioFormat.WAV and WAVE_AVAILABLE:
        try:
            with wave.open(str(path), 'rb') as wav_file:
                if duration is None:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    duration = frames / sample_rate if sample_rate > 0 else None
                channels = wav_file.getnchannels()
                if sample_rate is None:
                    sample_rate = wav_file.getframerate()
        except (OSError, ValueError, Exception):
            # Continue with what we have if WAV file is corrupted or unreadable
            pass
    
    return AudioFile(
        file_path=path,
        format=format,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        file_size_bytes=file_size,
        metadata=metadata
    )


def analyze_audio_file(file_path: Union[str, Path]) -> AudioAnalysisResult:
    """Perform detailed analysis of an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        AudioAnalysisResult with detailed information
        
    Raises:
        AudioProcessingError: If analysis fails
    """
    audio_file = load_audio_file(file_path)
    
    # Extract detailed format information
    format_details = {}
    bit_depth = None
    
    if audio_file.format == AudioFormat.WAV and WAVE_AVAILABLE:
        try:
            with wave.open(str(audio_file.file_path), 'rb') as wav_file:
                format_details['sample_width'] = wav_file.getsampwidth()
                format_details['frame_count'] = wav_file.getnframes()
                format_details['compression_type'] = wav_file.getcomptype()
                format_details['compression_name'] = wav_file.getcompname()
                bit_depth = wav_file.getsampwidth() * 8
        except Exception as e:
            raise AudioProcessingError(f"Failed to analyze WAV file: {e}")
    
    elif PYDUB_AVAILABLE:
        try:
            audio_segment = pydub.AudioSegment.from_file(str(audio_file.file_path))
            format_details['frame_count'] = len(audio_segment)
            format_details['frame_rate'] = audio_segment.frame_rate
            format_details['sample_width'] = audio_segment.sample_width
            bit_depth = audio_segment.sample_width * 8
        except (ImportError, Exception):
            # pydub might not support this format or failed to read it
            pass
    
    # Ensure we have the basic information
    duration = audio_file.duration_seconds
    if duration is None:
        raise AudioProcessingError("Could not determine audio duration")
    
    sample_rate = audio_file.sample_rate or 44100  # Default assumption
    channels = audio_file.channels or 1  # Default to mono
    
    return AudioAnalysisResult(
        audio_file=audio_file,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        format_details=format_details,
        metadata=audio_file.metadata
    )


def convert_audio_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_format: AudioFormat,
    quality: str = "medium"
) -> Path:
    """Convert audio file to a different format.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        target_format: Target audio format
        quality: Quality setting ("low", "medium", "high")
        
    Returns:
        Path to the converted file
        
    Raises:
        AudioProcessingError: If conversion fails
    """
    if not PYDUB_AVAILABLE:
        raise AudioProcessingError(
            "Audio format conversion requires pydub. "
            "Install with: pip install pydub"
        )
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not validate_audio_file(input_file):
        raise AudioProcessingError(f"Invalid input audio file: {input_file}")
    
    try:
        # Load audio file
        audio = pydub.AudioSegment.from_file(str(input_file))
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set export parameters based on format and quality
        export_params = {"format": target_format.value}
        
        if target_format == AudioFormat.MP3:
            quality_map = {"low": 64, "medium": 128, "high": 192}
            export_params["bitrate"] = f"{quality_map[quality]}k"
        elif target_format == AudioFormat.WAV:
            export_params["parameters"] = ["-acodec", "pcm_s16le"]
        elif target_format == AudioFormat.FLAC:
            export_params["parameters"] = ["-compression_level", "5"]
        elif target_format == AudioFormat.OGG:
            quality_map = {"low": 1, "medium": 5, "high": 9}
            export_params["parameters"] = ["-q:a", str(quality_map[quality])]
        
        # Export to target format
        audio.export(str(output_file), **export_params)
        
        return output_file
        
    except Exception as e:
        raise AudioProcessingError(f"Failed to convert audio: {e}")


def save_audio_file(audio_data: bytes, file_path: Union[str, Path]) -> Path:
    """Save audio data to a file.
    
    Args:
        audio_data: Raw audio data bytes
        file_path: Path where to save the file
        
    Returns:
        Path to the saved file
        
    Raises:
        AudioProcessingError: If save fails
    """
    path = Path(file_path)
    
    try:
        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write audio data
        with open(path, "wb") as f:
            f.write(audio_data)
        
        return path
        
    except Exception as e:
        raise AudioProcessingError(f"Failed to save audio file: {e}")


def get_audio_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get basic information about an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary with audio information
    """
    try:
        audio_file = load_audio_file(file_path)
        
        return {
            "file_path": str(audio_file.file_path),
            "format": audio_file.format.value,
            "file_size_bytes": audio_file.file_size_bytes,
            "file_size_mb": round(audio_file.file_size_mb, 2),
            "duration_seconds": audio_file.duration_seconds,
            "sample_rate": audio_file.sample_rate,
            "channels": audio_file.channels,
            "is_large_file": audio_file.is_large_file,
            "metadata": audio_file.metadata,
        }
    except Exception as e:
        return {
            "file_path": str(file_path),
            "error": str(e)
        }


def create_audio_file_info(file_path: Union[str, Path]) -> AudioFile:
    """Create AudioFile object with basic validation.
    
    This is a convenience function that combines validation and loading.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        AudioFile object
        
    Raises:
        AudioProcessingError: If file is invalid
    """
    return load_audio_file(file_path)
