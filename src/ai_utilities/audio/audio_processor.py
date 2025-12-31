"""Main audio processor for transcription and generation.

This module provides the main AudioProcessor class that integrates
with AI providers to offer audio transcription and generation capabilities.
"""

import time
from typing import Optional, Dict, Any, Union
from pathlib import Path

from ..client import AiClient
from .audio_models import (
    AudioFile,
    TranscriptionRequest,
    TranscriptionResult,
    AudioGenerationRequest,
    AudioGenerationResult,
    AudioFormat,
)
from .audio_utils import (
    load_audio_file,
    save_audio_file,
    validate_audio_file,
    AudioProcessingError,
)


class AudioProcessor:
    """Main class for audio processing operations.
    
    Provides high-level interface for audio transcription and generation
    using AI providers. Integrates with the existing AiClient infrastructure.
    """
    
    def __init__(self, client: Optional[AiClient] = None):
        """Initialize the audio processor.
        
        Args:
            client: Optional AiClient instance. If None, creates a new one.
        """
        self.client = client or AiClient()
    
    def transcribe_audio(
        self,
        audio_file: Union[str, Path, AudioFile],
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json",
        timestamp_granularities: Optional[list] = None
    ) -> TranscriptionResult:
        """Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file or AudioFile object
            language: Optional language code (e.g., 'en', 'es')
            model: Transcription model to use
            prompt: Optional prompt to guide transcription
            temperature: Sampling temperature (0.0 to 1.0)
            response_format: Response format ('json', 'text', 'srt', 'verbose_json', 'vtt')
            timestamp_granularities: List of timestamp granularities
            
        Returns:
            TranscriptionResult with transcribed text and metadata
            
        Raises:
            AudioProcessingError: If transcription fails
        """
        start_time = time.time()
        
        # Load and validate audio file
        if isinstance(audio_file, (str, Path)):
            audio_file_obj = load_audio_file(audio_file)
        else:
            audio_file_obj = audio_file
        
        # Check file size limits
        if audio_file_obj.is_large_file:
            raise AudioProcessingError(
                f"Audio file is too large ({audio_file_obj.file_size_mb:.1f}MB). "
                "Maximum file size is 25MB for most providers."
            )
        
        # Create transcription request
        request = TranscriptionRequest(
            audio_file=audio_file_obj,
            language=language,
            model=model,
            prompt=prompt,
            temperature=temperature,
            response_format=response_format,
            timestamp_granularities=timestamp_granularities or []
        )
        
        try:
            # Call the AI provider for transcription
            result = self._transcribe_with_provider(request)
            
            # Add processing time
            processing_time = time.time() - start_time
            result.processing_time_seconds = processing_time
            
            return result
            
        except Exception as e:
            raise AudioProcessingError(f"Transcription failed: {e}")
    
    def _transcribe_with_provider(self, request: TranscriptionRequest) -> TranscriptionResult:
        """Transcribe audio using the AI provider.
        
        Args:
            request: Transcription request
            
        Returns:
            TranscriptionResult
            
        Raises:
            AudioProcessingError: If provider transcription fails
        """
        try:
            # Read audio file as bytes
            with open(request.audio_file.file_path, "rb") as f:
                audio_data = f.read()
            
            # Use the provider's OpenAI client directly
            if hasattr(self.client.provider, 'client'):
                openai_client = self.client.provider.client
                
                # Prepare files for upload
                files = {
                    "file": ("audio.wav", audio_data, "audio/wav")
                }
                
                # Prepare data
                data = {
                    "model": request.model,
                    "temperature": request.temperature,
                    "response_format": request.response_format,
                }
                
                # Add optional parameters
                if request.language:
                    data["language"] = request.language
                if request.prompt:
                    data["prompt"] = request.prompt
                if request.timestamp_granularities:
                    for granularity in request.timestamp_granularities:
                        data.append(("timestamp_granularities[]", granularity))
                
                # Make the request using OpenAI client
                response = openai_client.audio.transcriptions.create(
                    file=(request.audio_file.file_path.name, audio_data, "audio/wav"),
                    model=request.model,
                    temperature=request.temperature,
                    response_format=request.response_format,
                    language=request.language,
                    prompt=request.prompt
                )
                
                # Parse the response
                if hasattr(response, 'text'):
                    # Simple text response
                    return TranscriptionResult(
                        text=response.text,
                        model_used=request.model,
                        metadata={"provider_response": str(response)}
                    )
                else:
                    # Verbose JSON response
                    return self._parse_transcription_response(response.model_dump(), request)
            else:
                raise AudioProcessingError("Provider does not support audio transcription")
                
        except Exception as e:
            raise AudioProcessingError(f"Provider transcription failed: {e}")
    
    def _parse_transcription_response(
        self, 
        response_data: Dict[str, Any], 
        request: TranscriptionRequest
    ) -> TranscriptionResult:
        """Parse transcription response from provider.
        
        Args:
            response_data: Raw response from provider
            request: Original transcription request
            
        Returns:
            Parsed TranscriptionResult
        """
        text = response_data.get("text", "")
        
        # Extract segments if available (verbose_json format)
        segments = None
        if "segments" in response_data:
            from .audio_models import TranscriptionSegment
            segments = []
            for segment_data in response_data["segments"]:
                segment = TranscriptionSegment(
                    start_time=segment_data.get("start", 0.0),
                    end_time=segment_data.get("end", 0.0),
                    text=segment_data.get("text", ""),
                    confidence=segment_data.get("confidence")
                )
                segments.append(segment)
        
        return TranscriptionResult(
            text=text,
            language=response_data.get("language"),
            duration_seconds=request.audio_file.duration_seconds,
            segments=segments,
            confidence=response_data.get("confidence"),
            model_used=request.model,
            metadata={
                "provider_response": response_data,
                "original_file": str(request.audio_file.file_path),
                "file_format": request.audio_file.format.value
            }
        )
    
    def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0,
        response_format: AudioFormat = AudioFormat.MP3
    ) -> AudioGenerationResult:
        """Generate audio from text using text-to-speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            model: Text-to-speech model
            speed: Speech speed factor (0.25 to 4.0)
            response_format: Output audio format
            
        Returns:
            AudioGenerationResult with generated audio
            
        Raises:
            AudioProcessingError: If generation fails
        """
        start_time = time.time()
        
        # Create generation request
        request = AudioGenerationRequest(
            text=text,
            voice=voice,
            model=model,
            speed=speed,
            response_format=response_format
        )
        
        try:
            # Call the AI provider for generation
            result = self._generate_with_provider(request)
            
            # Add processing time
            processing_time = time.time() - start_time
            result.processing_time_seconds = processing_time
            
            return result
            
        except Exception as e:
            raise AudioProcessingError(f"Audio generation failed: {e}")
    
    def _generate_with_provider(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Generate audio using the AI provider.
        
        Args:
            request: Audio generation request
            
        Returns:
            AudioGenerationResult
            
        Raises:
            AudioProcessingError: If provider generation fails
        """
        try:
            # Use the provider's OpenAI client directly
            if hasattr(self.client.provider, 'client'):
                openai_client = self.client.provider.client
                
                # Make the request using OpenAI client
                response = openai_client.audio.speech.create(
                    model=request.model,
                    input=request.text,
                    voice=request.voice,
                    speed=request.speed,
                    response_format=request.response_format.value
                )
                
                # Get audio data
                audio_data = response.content
                
                return AudioGenerationResult(
                    audio_data=audio_data,
                    format=request.response_format,
                    text=request.text,
                    voice=request.voice,
                    model_used=request.model,
                    file_size_bytes=len(audio_data),
                    metadata={
                        "provider_response_headers": dict(response.response.headers) if hasattr(response, 'response') else {},
                        "request_params": {
                            "model": request.model,
                            "input": request.text,
                            "voice": request.voice,
                            "speed": request.speed,
                            "response_format": request.response_format.value
                        }
                    }
                )
            else:
                raise AudioProcessingError("Provider does not support audio generation")
            
        except Exception as e:
            raise AudioProcessingError(f"Provider audio generation failed: {e}")
    
    def transcribe_and_generate(
        self,
        audio_file: Union[str, Path, AudioFile],
        target_voice: str = "alloy",
        translation_prompt: Optional[str] = None
    ) -> tuple[TranscriptionResult, AudioGenerationResult]:
        """Transcribe audio and then regenerate with different voice.
        
        This is a convenience method that combines transcription and generation,
        useful for voice cloning or translation scenarios.
        
        Args:
            audio_file: Audio file to transcribe
            target_voice: Voice for regenerated audio
            translation_prompt: Optional prompt to modify the transcribed text
            
        Returns:
            Tuple of (TranscriptionResult, AudioGenerationResult)
        """
        # Transcribe the audio
        transcription = self.transcribe_audio(audio_file)
        
        # Optionally modify the text
        text_to_generate = transcription.text
        if translation_prompt:
            text_to_generate = f"{translation_prompt}\n\n{text_to_generate}"
        
        # Generate new audio
        generation = self.generate_audio(
            text=text_to_generate,
            voice=target_voice
        )
        
        return transcription, generation
    
    def get_supported_voices(self) -> Dict[str, Any]:
        """Get list of supported voices for audio generation.
        
        Returns:
            Dictionary with voice information
        """
        try:
            response = self.client._make_request("GET", "/audio/voices")
            return response.json()
        except Exception:
            # Return default voices if API call fails
            return {
                "voices": [
                    {"id": "alloy", "name": "Alloy", "language": "en"},
                    {"id": "echo", "name": "Echo", "language": "en"},
                    {"id": "fable", "name": "Fable", "language": "en"},
                    {"id": "onyx", "name": "Onyx", "language": "en"},
                    {"id": "nova", "name": "Nova", "language": "en"},
                    {"id": "shimmer", "name": "Shimmer", "language": "en"},
                ]
            }
    
    def get_supported_models(self, operation: str = "all") -> Dict[str, list]:
        """Get supported models for audio operations.
        
        Args:
            operation: Type of operation ('transcription', 'generation', 'all')
            
        Returns:
            Dictionary with supported models
        """
        models = {
            "transcription": ["whisper-1"],
            "generation": ["tts-1", "tts-1-hd"]
        }
        
        if operation == "all":
            return models
        elif operation in models:
            return {operation: models[operation]}
        else:
            raise ValueError(f"Invalid operation: {operation}")
    
    def validate_audio_for_transcription(self, audio_file: Union[str, Path, AudioFile]) -> Dict[str, Any]:
        """Validate audio file for transcription requirements.
        
        Args:
            audio_file: Audio file to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            if isinstance(audio_file, (str, Path)):
                audio_obj = load_audio_file(audio_file)
            else:
                audio_obj = audio_file
            
            validation_result = {
                "valid": True,
                "warnings": [],
                "errors": [],
                "file_info": {
                    "format": audio_obj.format.value,
                    "size_mb": round(audio_obj.file_size_mb, 2),
                    "duration_seconds": audio_obj.duration_seconds,
                    "sample_rate": audio_obj.sample_rate,
                    "channels": audio_obj.channels,
                }
            }
            
            # Check file size
            if audio_obj.is_large_file:
                validation_result["warnings"].append(
                    f"File is large ({audio_obj.file_size_mb:.1f}MB). May exceed provider limits."
                )
            
            # Check duration
            if audio_obj.duration_seconds and audio_obj.duration_seconds > 300:  # 5 minutes
                validation_result["warnings"].append(
                    "Audio is longer than 5 minutes. May take longer to process."
                )
            
            # Check sample rate
            if audio_obj.sample_rate and audio_obj.sample_rate > 48000:
                validation_result["warnings"].append(
                    "High sample rate detected. Consider downsampling for faster processing."
                )
            
            # Check format support
            supported_formats = ["wav", "mp3", "flac", "ogg", "m4a", "webm"]
            if audio_obj.format.value not in supported_formats:
                validation_result["errors"].append(
                    f"Unsupported format: {audio_obj.format.value}"
                )
                validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "file_info": {}
            }
