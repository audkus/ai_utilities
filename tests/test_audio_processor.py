"""Comprehensive tests for audio_processor.py module.

This module provides thorough testing for the AudioProcessor class,
covering all transcription, generation, validation, and utility methods.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

import pytest

from ai_utilities.audio.audio_processor import AudioProcessor
from ai_utilities.audio.audio_models import (
    AudioFile,
    TranscriptionRequest,
    TranscriptionResult,
    AudioGenerationRequest,
    AudioGenerationResult,
    AudioFormat,
    TranscriptionSegment
)
from ai_utilities.audio.audio_utils import AudioProcessingError
from ai_utilities.client import AiClient


class TestAudioProcessor:
    """Test the AudioProcessor class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock AI client."""
        client = Mock(spec=AiClient)
        client.provider = Mock()
        client.provider.client = Mock()
        client._make_request = Mock()
        return client
    
    @pytest.fixture
    def audio_processor(self, mock_client):
        """Create AudioProcessor instance with mock client."""
        return AudioProcessor(client=mock_client)
    
    @pytest.fixture
    def mock_audio_file(self, tmp_path):
        """Create a mock audio file with actual file."""
        # Create a temporary file
        audio_file_path = tmp_path / "test.wav"
        audio_file_path.write_bytes(b"fake audio data")
        
        return AudioFile(
            file_path=audio_file_path,
            format=AudioFormat.WAV,
            file_size_bytes=1048576,  # 1MB in bytes
            duration_seconds=10.0,
            sample_rate=44100,
            channels=1
        )
    
    def test_init_with_client(self, mock_client):
        """Test AudioProcessor initialization with client."""
        processor = AudioProcessor(client=mock_client)
        assert processor.client == mock_client
    
    def test_init_without_client(self):
        """Test AudioProcessor initialization without client."""
        with patch('ai_utilities.audio.audio_processor.AiClient') as mock_client_class:
            mock_instance = Mock()
            mock_client_class.return_value = mock_instance
            
            processor = AudioProcessor()
            assert processor.client == mock_instance
            mock_client_class.assert_called_once()
    
    def test_transcribe_audio_with_path(self, audio_processor, mock_audio_file):
        """Test transcribe_audio with file path."""
        with patch('ai_utilities.audio.audio_processor.load_audio_file') as mock_load:
            mock_load.return_value = mock_audio_file
            
            with patch.object(audio_processor, '_transcribe_with_provider') as mock_transcribe:
                expected_result = TranscriptionResult(
                    text="Test transcription",
                    model_used="whisper-1"
                )
                mock_transcribe.return_value = expected_result
                
                result = audio_processor.transcribe_audio("test.wav")
                
                assert result == expected_result
                mock_load.assert_called_once_with("test.wav")
                mock_transcribe.assert_called_once()
                assert result.processing_time_seconds > 0
    
    def test_transcribe_audio_with_audiofile_object(self, audio_processor, mock_audio_file):
        """Test transcribe_audio with AudioFile object."""
        with patch.object(audio_processor, '_transcribe_with_provider') as mock_transcribe:
            expected_result = TranscriptionResult(
                text="Test transcription",
                model_used="whisper-1"
            )
            mock_transcribe.return_value = expected_result
            
            result = audio_processor.transcribe_audio(mock_audio_file)
            
            assert result == expected_result
            mock_transcribe.assert_called_once()
    
    def test_transcribe_audio_large_file_error(self, audio_processor, tmp_path):
        """Test transcribe_audio with large file raises error."""
        # Create a large file (over 25MB)
        large_file_path = tmp_path / "large.wav"
        large_file_path.write_bytes(b"x" * 30 * 1024 * 1024)  # 30MB
        
        large_file = AudioFile(
            file_path=large_file_path,
            format=AudioFormat.WAV,
            file_size_bytes=30 * 1024 * 1024,  # 30MB in bytes
            duration_seconds=300.0,
            sample_rate=44100,
            channels=1
        )
        
        with pytest.raises(AudioProcessingError, match="Audio file is too large"):
            audio_processor.transcribe_audio(large_file)
    
    def test_transcribe_audio_provider_error(self, audio_processor, mock_audio_file):
        """Test transcribe_audio when provider fails."""
        with patch.object(audio_processor, '_transcribe_with_provider') as mock_transcribe:
            mock_transcribe.side_effect = Exception("Provider error")
            
            with pytest.raises(AudioProcessingError, match="Transcription failed"):
                audio_processor.transcribe_audio(mock_audio_file)
    
    def test_transcribe_with_provider_success(self, audio_processor, mock_audio_file):
        """Test _transcribe_with_provider successful transcription."""
        # Mock OpenAI client response
        mock_response = Mock()
        mock_response.text = "Transcribed text"
        
        audio_processor.client.provider.client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b"fake audio data")):
            request = TranscriptionRequest(
                audio_file=mock_audio_file,
                model="whisper-1"
            )
            
            result = audio_processor._transcribe_with_provider(request)
            
            assert result.text == "Transcribed text"
            assert result.model_used == "whisper-1"
            assert "provider_response" in result.metadata
    
    def test_transcribe_with_provider_verbose_response(self, audio_processor, mock_audio_file):
        """Test _transcribe_with_provider with verbose JSON response."""
        # Mock verbose response
        mock_response = Mock()
        mock_response.model_dump.return_value = {
            "text": "Transcribed text",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello",
                    "confidence": 0.95
                }
            ]
        }
        del mock_response.text  # Remove simple text attribute
        
        audio_processor.client.provider.client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b"fake audio data")):
            request = TranscriptionRequest(
                audio_file=mock_audio_file,
                model="whisper-1"
            )
            
            result = audio_processor._transcribe_with_provider(request)
            
            assert result.text == "Transcribed text"
            assert result.language == "en"
            assert len(result.segments) == 1
            assert result.segments[0].text == "Hello"
    
    def test_transcribe_with_provider_no_client_support(self, audio_processor, mock_audio_file):
        """Test _transcribe_with_provider when provider doesn't support audio."""
        audio_processor.client.provider = Mock()  # No client attribute
        
        request = TranscriptionRequest(
            audio_file=mock_audio_file,
            model="whisper-1"
        )
        
        with pytest.raises(AudioProcessingError, match="Provider transcription failed"):
            audio_processor._transcribe_with_provider(request)
    
    def test_transcribe_with_provider_exception(self, audio_processor, mock_audio_file):
        """Test _transcribe_with_provider handles exceptions."""
        audio_processor.client.provider.client.audio.transcriptions.create.side_effect = Exception("API error")
        
        with patch('builtins.open', mock_open(read_data=b"fake audio data")):
            request = TranscriptionRequest(
                audio_file=mock_audio_file,
                model="whisper-1"
            )
            
            with pytest.raises(AudioProcessingError, match="Provider transcription failed"):
                audio_processor._transcribe_with_provider(request)
    
    def test_parse_transcription_response_simple(self, audio_processor, mock_audio_file):
        """Test _parse_transcription_response with simple response."""
        response_data = {"text": "Simple transcription"}
        request = TranscriptionRequest(
            audio_file=mock_audio_file,
            model="whisper-1"
        )
        
        result = audio_processor._parse_transcription_response(response_data, request)
        
        assert result.text == "Simple transcription"
        assert result.model_used == "whisper-1"
        assert result.segments is None
    
    def test_parse_transcription_response_verbose(self, audio_processor, mock_audio_file):
        """Test _parse_transcription_response with verbose response."""
        response_data = {
            "text": "Verbose transcription",
            "language": "en",
            "confidence": 0.92,
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello world",
                    "confidence": 0.95
                }
            ]
        }
        request = TranscriptionRequest(
            audio_file=mock_audio_file,
            model="whisper-1"
        )
        
        result = audio_processor._parse_transcription_response(response_data, request)
        
        assert result.text == "Verbose transcription"
        assert result.language == "en"
        assert result.confidence == 0.92
        assert len(result.segments) == 1
        assert result.segments[0].text == "Hello world"
        assert result.segments[0].start_time == 0.0
        assert result.segments[0].end_time == 2.5
    
    def test_generate_audio_success(self, audio_processor):
        """Test generate_audio successful generation."""
        with patch.object(audio_processor, '_generate_with_provider') as mock_generate:
            expected_result = AudioGenerationResult(
                audio_data=b"fake audio data",
                format=AudioFormat.MP3,
                text="Hello world",
                voice="alloy",
                model_used="tts-1",
                file_size_bytes=len(b"fake audio data")
            )
            mock_generate.return_value = expected_result
            
            result = audio_processor.generate_audio("Hello world")
            
            assert result == expected_result
            mock_generate.assert_called_once()
            assert result.processing_time_seconds > 0
    
    def test_generate_audio_provider_error(self, audio_processor):
        """Test generate_audio when provider fails."""
        with patch.object(audio_processor, '_generate_with_provider') as mock_generate:
            mock_generate.side_effect = Exception("Provider error")
            
            with pytest.raises(AudioProcessingError, match="Audio generation failed"):
                audio_processor.generate_audio("Hello world")
    
    def test_generate_with_provider_success(self, audio_processor):
        """Test _generate_with_provider successful generation."""
        mock_response = Mock()
        mock_response.content = b"generated audio data"
        mock_response.response.headers = {"content-type": "audio/mpeg"}
        
        audio_processor.client.provider.client.audio.speech.create.return_value = mock_response
        
        request = AudioGenerationRequest(
            text="Hello world",
            voice="alloy",
            model="tts-1",
            speed=1.0,
            response_format=AudioFormat.MP3
        )
        
        result = audio_processor._generate_with_provider(request)
        
        assert result.audio_data == b"generated audio data"
        assert result.format == AudioFormat.MP3
        assert result.text == "Hello world"
        assert result.voice == "alloy"
        assert result.model_used == "tts-1"
        assert result.file_size_bytes == len(b"generated audio data")
    
    def test_generate_with_provider_no_client_support(self, audio_processor):
        """Test _generate_with_provider when provider doesn't support audio."""
        audio_processor.client.provider = Mock()  # No client attribute
        
        request = AudioGenerationRequest(
            text="Hello world",
            voice="alloy"
        )
        
        with pytest.raises(AudioProcessingError, match="Provider audio generation failed"):
            audio_processor._generate_with_provider(request)
    
    def test_generate_with_provider_exception(self, audio_processor):
        """Test _generate_with_provider handles exceptions."""
        audio_processor.client.provider.client.audio.speech.create.side_effect = Exception("API error")
        
        request = AudioGenerationRequest(
            text="Hello world",
            voice="alloy"
        )
        
        with pytest.raises(AudioProcessingError, match="Provider audio generation failed"):
            audio_processor._generate_with_provider(request)
    
    def test_transcribe_and_generate_success(self, audio_processor, mock_audio_file):
        """Test transcribe_and_generate successful workflow."""
        transcription_result = TranscriptionResult(
            text="Original text",
            model_used="whisper-1"
        )
        generation_result = AudioGenerationResult(
            audio_data=b"generated audio",
            format=AudioFormat.MP3,
            text="Original text",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=len(b"generated audio")
        )
        
        with patch.object(audio_processor, 'transcribe_audio', return_value=transcription_result) as mock_transcribe:
            with patch.object(audio_processor, 'generate_audio', return_value=generation_result) as mock_generate:
                
                result = audio_processor.transcribe_and_generate(mock_audio_file, target_voice="nova")
                
                assert result == (transcription_result, generation_result)
                mock_transcribe.assert_called_once()
                mock_generate.assert_called_once_with(text="Original text", voice="nova")
    
    def test_transcribe_and_generate_with_translation_prompt(self, audio_processor, mock_audio_file):
        """Test transcribe_and_generate with translation prompt."""
        transcription_result = TranscriptionResult(
            text="Original text",
            model_used="whisper-1"
        )
        generation_result = AudioGenerationResult(
            audio_data=b"generated audio",
            format=AudioFormat.MP3,
            text="Translate to English:\n\nOriginal text",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=len(b"generated audio")
        )
        
        with patch.object(audio_processor, 'transcribe_audio', return_value=transcription_result):
            with patch.object(audio_processor, 'generate_audio', return_value=generation_result):
                
                result = audio_processor.transcribe_and_generate(
                    mock_audio_file, 
                    target_voice="alloy",
                    translation_prompt="Translate to English:"
                )
                
                assert result == (transcription_result, generation_result)
    
    def test_get_supported_voices_success(self, audio_processor):
        """Test get_supported_voices successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {"voices": [{"id": "custom", "name": "Custom"}]}
        audio_processor.client._make_request.return_value = mock_response
        
        result = audio_processor.get_supported_voices()
        
        assert result == {"voices": [{"id": "custom", "name": "Custom"}]}
        audio_processor.client._make_request.assert_called_once_with("GET", "/audio/voices")
    
    def test_get_supported_voices_fallback(self, audio_processor):
        """Test get_supported_voices falls back to defaults on error."""
        audio_processor.client._make_request.side_effect = Exception("API error")
        
        result = audio_processor.get_supported_voices()
        
        assert "voices" in result
        assert len(result["voices"]) == 6  # Default voices
        voice_ids = [v["id"] for v in result["voices"]]
        assert "alloy" in voice_ids
        assert "echo" in voice_ids
        assert "nova" in voice_ids
    
    def test_get_supported_models_all(self, audio_processor):
        """Test get_supported_models for all operations."""
        result = audio_processor.get_supported_models("all")
        
        assert "transcription" in result
        assert "generation" in result
        assert "whisper-1" in result["transcription"]
        assert "tts-1" in result["generation"]
        assert "tts-1-hd" in result["generation"]
    
    def test_get_supported_models_transcription(self, audio_processor):
        """Test get_supported_models for transcription only."""
        result = audio_processor.get_supported_models("transcription")
        
        assert "transcription" in result
        assert "generation" not in result
        assert result["transcription"] == ["whisper-1"]
    
    def test_get_supported_models_generation(self, audio_processor):
        """Test get_supported_models for generation only."""
        result = audio_processor.get_supported_models("generation")
        
        assert "generation" in result
        assert "transcription" not in result
        assert result["generation"] == ["tts-1", "tts-1-hd"]
    
    def test_get_supported_models_invalid_operation(self, audio_processor):
        """Test get_supported_models with invalid operation."""
        with pytest.raises(ValueError, match="Invalid operation"):
            audio_processor.get_supported_models("invalid")
    
    def test_validate_audio_for_transcription_success(self, audio_processor, mock_audio_file):
        """Test validate_audio_for_transcription with valid file."""
        result = audio_processor.validate_audio_for_transcription(mock_audio_file)
        
        assert result["valid"] is True
        assert result["errors"] == []
        assert "file_info" in result
        assert result["file_info"]["format"] == "wav"
        assert result["file_info"]["size_mb"] == 1.0
        assert result["file_info"]["duration_seconds"] == 10.0
    
    def test_validate_audio_for_transcription_with_path(self, audio_processor, mock_audio_file):
        """Test validate_audio_for_transcription with file path."""
        with patch('ai_utilities.audio.audio_processor.load_audio_file') as mock_load:
            mock_load.return_value = mock_audio_file
            
            result = audio_processor.validate_audio_for_transcription("test.wav")
            
            assert result["valid"] is True
            mock_load.assert_called_once_with("test.wav")
    
    def test_validate_audio_large_file_warning(self, audio_processor, tmp_path):
        """Test validation warning for large file."""
        # Create a large file (over 25MB)
        large_file_path = tmp_path / "large.wav"
        large_file_path.write_bytes(b"x" * 30 * 1024 * 1024)  # 30MB
        
        large_file = AudioFile(
            file_path=large_file_path,
            format=AudioFormat.WAV,
            file_size_bytes=30 * 1024 * 1024,  # 30MB in bytes
            duration_seconds=300.0,
            sample_rate=44100,
            channels=1
        )
        
        result = audio_processor.validate_audio_for_transcription(large_file)
        
        assert result["valid"] is True
        assert len(result["warnings"]) == 1
        assert "large" in result["warnings"][0].lower()
    
    def test_validate_audio_long_duration_warning(self, audio_processor, tmp_path):
        """Test validation warning for long duration."""
        long_file_path = tmp_path / "long.wav"
        long_file_path.write_bytes(b"x" * 10 * 1024 * 1024)  # 10MB
        
        long_file = AudioFile(
            file_path=long_file_path,
            format=AudioFormat.WAV,
            file_size_bytes=10 * 1024 * 1024,
            duration_seconds=400.0,  # Over 5 minutes
            sample_rate=44100,
            channels=1
        )
        
        result = audio_processor.validate_audio_for_transcription(long_file)
        
        assert result["valid"] is True
        assert len(result["warnings"]) == 1
        assert "longer than 5 minutes" in result["warnings"][0]
    
    def test_validate_audio_high_sample_rate_warning(self, audio_processor, tmp_path):
        """Test validation warning for high sample rate."""
        high_sr_file_path = tmp_path / "high_sr.wav"
        high_sr_file_path.write_bytes(b"x" * 10 * 1024 * 1024)  # 10MB
        
        high_sr_file = AudioFile(
            file_path=high_sr_file_path,
            format=AudioFormat.WAV,
            file_size_bytes=10 * 1024 * 1024,
            duration_seconds=60.0,
            sample_rate=96000,  # Over 48000
            channels=1
        )
        
        result = audio_processor.validate_audio_for_transcription(high_sr_file)
        
        assert result["valid"] is True
        assert len(result["warnings"]) == 1
        assert "sample rate" in result["warnings"][0].lower()
    
    def test_validate_audio_exception_handling(self, audio_processor):
        """Test validate_audio_for_transcription handles exceptions."""
        with patch('ai_utilities.audio.audio_processor.load_audio_file') as mock_load:
            mock_load.side_effect = Exception("File not found")
            
            result = audio_processor.validate_audio_for_transcription("nonexistent.wav")
            
            assert result["valid"] is False
            assert len(result["errors"]) == 1
            assert "File not found" in result["errors"][0]
            assert result["warnings"] == []
            assert result["file_info"] == {}
    
    def test_transcribe_audio_all_parameters(self, audio_processor, mock_audio_file):
        """Test transcribe_audio with all optional parameters."""
        with patch.object(audio_processor, '_transcribe_with_provider') as mock_transcribe:
            expected_result = TranscriptionResult(
                text="Test transcription",
                model_used="whisper-1"
            )
            mock_transcribe.return_value = expected_result
            
            result = audio_processor.transcribe_audio(
                audio_file=mock_audio_file,
                language="en",
                model="whisper-1",
                prompt="Test prompt",
                temperature=0.5,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"]
            )
            
            assert result == expected_result
            mock_transcribe.assert_called_once()
            
            # Check the request was created with correct parameters
            call_args = mock_transcribe.call_args[0][0]
            assert call_args.language == "en"
            assert call_args.model == "whisper-1"
            assert call_args.prompt == "Test prompt"
            assert call_args.temperature == 0.5
            assert call_args.response_format == "verbose_json"
            assert call_args.timestamp_granularities == ["word", "segment"]
    
    def test_generate_audio_all_parameters(self, audio_processor):
        """Test generate_audio with all optional parameters."""
        with patch.object(audio_processor, '_generate_with_provider') as mock_generate:
            expected_result = AudioGenerationResult(
                audio_data=b"fake audio data",
                format=AudioFormat.FLAC,
                text="Hello world",
                voice="nova",
                model_used="tts-1-hd",
                file_size_bytes=len(b"fake audio data")
            )
            mock_generate.return_value = expected_result
            
            result = audio_processor.generate_audio(
                text="Hello world",
                voice="nova",
                model="tts-1-hd",
                speed=1.5,
                response_format=AudioFormat.FLAC
            )
            
            assert result == expected_result
            mock_generate.assert_called_once()
            
            # Check the request was created with correct parameters
            call_args = mock_generate.call_args[0][0]
            assert call_args.text == "Hello world"
            assert call_args.voice == "nova"
            assert call_args.model == "tts-1-hd"
            assert call_args.speed == 1.5
            assert call_args.response_format == AudioFormat.FLAC
