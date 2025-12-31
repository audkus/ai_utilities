"""Integration tests for audio processing functionality.

This module tests the integration between audio processing and the main AI client.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_utilities import AiClient, AudioProcessor
from ai_utilities.audio.audio_models import AudioFormat, TranscriptionResult, AudioGenerationResult
from ai_utilities.audio.audio_utils import AudioProcessingError


class TestAudioClientIntegration:
    """Test audio processing integration with AiClient."""
    
    def setUp(self):
        """Set up mock settings for tests."""
        from ai_utilities import AiSettings
        return AiSettings(api_key="test-key", model="test-model")
    
    def test_audio_processor_initialization(self):
        """Test that AudioProcessor can be initialized with AiClient."""
        settings = self.setUp()
        client = AiClient(settings)
        processor = AudioProcessor(client=client)
        
        assert processor.client == client
    
    def test_audio_processor_default_initialization(self):
        """Test that AudioProcessor can be initialized without client."""
        with patch('ai_utilities.audio.audio_processor.AiClient') as mock_client:
            mock_client.return_value = MagicMock()
            processor = AudioProcessor()
            
            assert processor.client is not None
            assert hasattr(processor.client, 'ask')
    
    @patch('ai_utilities.audio.audio_processor.AudioProcessor.transcribe_audio')
    def test_client_transcribe_audio_integration(self, mock_transcribe):
        """Test AiClient.transcribe_audio method integration."""
        # Mock the processor result
        mock_result = TranscriptionResult(
            text="Hello world",
            model_used="whisper-1",
            processing_time_seconds=1.5
        )
        mock_transcribe.return_value = mock_result
        
        # Create client with mock settings to avoid interactive setup
        from ai_utilities import AiSettings
        settings = AiSettings(api_key="test-key", model="test-model")
        client = AiClient(settings)
        
        result = client.transcribe_audio("test.wav")
        
        # Verify the result format
        assert result["text"] == "Hello world"
        assert result["model_used"] == "whisper-1"
        assert result["processing_time_seconds"] == 1.5
        assert result["word_count"] == 2
        assert result["character_count"] == len("Hello world")
        assert result["segments"] == []
        
        # Verify the processor was called
        mock_transcribe.assert_called_once_with(
            audio_file="test.wav",
            language=None,
            model="whisper-1",
            prompt=None,
            temperature=0.0,
            response_format="json"
        )
    
    @patch('ai_utilities.audio.audio_processor.AudioProcessor.generate_audio')
    def test_client_generate_audio_integration(self, mock_generate):
        """Test AiClient.generate_audio method integration."""
        # Mock the processor result
        mock_result = AudioGenerationResult(
            audio_data=b"fake audio data",
            format=AudioFormat.MP3,
            text="Hello world",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=100
        )
        mock_generate.return_value = mock_result
        
        settings = self.setUp()
        client = AiClient(settings)
        result = client.generate_audio("Hello world", voice="alloy")
        
        # Verify the result
        assert result == b"fake audio data"
        
        # Verify the processor was called
        mock_generate.assert_called_once_with(
            text="Hello world",
            voice="alloy",
            model="tts-1",
            speed=1.0,
            response_format=AudioFormat.MP3
        )
    
    @patch('ai_utilities.audio.audio_processor.AudioProcessor.get_supported_voices')
    def test_client_get_audio_voices_integration(self, mock_voices):
        """Test AiClient.get_audio_voices method integration."""
        # Mock voice data
        mock_voices.return_value = {
            "voices": [
                {"id": "alloy", "name": "Alloy", "language": "en"},
                {"id": "echo", "name": "Echo", "language": "en"}
            ]
        }
        
        settings = self.setUp()
        client = AiClient(settings)
        result = client.get_audio_voices()
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["id"] == "alloy"
        assert result[1]["id"] == "echo"
        
        # Verify the processor was called
        mock_voices.assert_called_once()
    
    @patch('ai_utilities.audio.audio_processor.AudioProcessor.validate_audio_for_transcription')
    def test_client_validate_audio_file_integration(self, mock_validate):
        """Test AiClient.validate_audio_file method integration."""
        # Mock validation result
        mock_validate.return_value = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_info": {
                "format": "wav",
                "size_mb": 1.5,
                "duration_seconds": 10.0
            }
        }
        
        settings = self.setUp()
        client = AiClient(settings)
        result = client.validate_audio_file("test.wav")
        
        # Verify the result
        assert result["valid"] is True
        assert result["file_info"]["format"] == "wav"
        
        # Verify the processor was called
        mock_validate.assert_called_once_with("test.wav")


class TestAudioProcessorFunctionality:
    """Test AudioProcessor core functionality."""
    
    @patch('ai_utilities.audio.audio_processor.AiClient')
    def test_get_supported_models(self, mock_client):
        """Test getting supported models."""
        mock_client.return_value = MagicMock()
        processor = AudioProcessor(client=mock_client.return_value)
        
        models = processor.get_supported_models()
        
        assert "transcription" in models
        assert "generation" in models
        assert "whisper-1" in models["transcription"]
        assert "tts-1" in models["generation"]
    
    @patch('ai_utilities.audio.audio_processor.AiClient')
    def test_get_supported_models_by_operation(self, mock_client):
        """Test getting models for specific operation."""
        mock_client.return_value = MagicMock()
        processor = AudioProcessor(client=mock_client.return_value)
        
        transcription_models = processor.get_supported_models("transcription")
        generation_models = processor.get_supported_models("generation")
        
        assert "transcription" in transcription_models
        assert "generation" in generation_models
        assert len(transcription_models["transcription"]) > 0
        assert len(generation_models["generation"]) > 0
    
    @patch('ai_utilities.audio.audio_processor.AiClient')
    def test_get_supported_models_invalid_operation(self, mock_client):
        """Test getting models for invalid operation."""
        mock_client.return_value = MagicMock()
        processor = AudioProcessor(client=mock_client.return_value)
        
        with pytest.raises(ValueError, match="Invalid operation"):
            processor.get_supported_models("invalid")


class TestAudioProcessingImports:
    """Test that audio processing can be imported from main package."""
    
    def test_main_package_imports(self):
        """Test importing audio components from main package."""
        from ai_utilities import (
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
        
        # Verify all imports work
        assert AudioProcessor is not None
        assert AudioFormat is not None
        assert AudioFile is not None
        assert TranscriptionRequest is not None
        assert TranscriptionResult is not None
        assert AudioGenerationRequest is not None
        assert AudioGenerationResult is not None
        assert load_audio_file is not None
        assert save_audio_file is not None
        assert validate_audio_file is not None
        assert get_audio_info is not None
    
    def test_audio_format_enum(self):
        """Test AudioFormat enum values."""
        from ai_utilities import AudioFormat
        
        expected_formats = ["wav", "mp3", "flac", "ogg", "m4a", "webm"]
        actual_formats = [fmt.value for fmt in AudioFormat]
        
        assert actual_formats == expected_formats
        assert AudioFormat("wav") == AudioFormat.WAV
        assert AudioFormat("mp3") == AudioFormat.MP3


class TestAudioErrorHandling:
    """Test error handling in audio processing."""
    
    def test_audio_processing_error(self):
        """Test AudioProcessingError creation."""
        error = AudioProcessingError("Test error")
        assert str(error) == "Test error"
    
    @patch('ai_utilities.audio.audio_processor.AudioProcessor')
    def test_client_audio_error_handling(self, mock_processor_class):
        """Test that client properly handles audio processing errors."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(api_key="test-key", model="test-model")
        client = AiClient(settings)
        
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Mock transcription to raise an error
        from ai_utilities.audio.audio_utils import AudioProcessingError
        mock_processor.transcribe_audio.side_effect = AudioProcessingError("Test error")
        
        with pytest.raises(Exception):  # Should be wrapped in FileTransferError
            client.transcribe_audio("test.wav")


@pytest.mark.integration
class TestAudioProcessingRealAPI:
    """Integration tests that require real API access.
    
    These tests are marked as integration and will only run with explicit request.
    """
    
    @pytest.mark.skip(reason="Requires real API key and audio file")
    def test_real_transcription(self):
        """Test real audio transcription with API."""
        client = AiClient()
        
        # This test would require a real audio file
        # result = client.transcribe_audio("real_audio.wav")
        # assert "text" in result
        pass
    
    @pytest.mark.skip(reason="Requires real API key")
    def test_real_audio_generation(self):
        """Test real audio generation with API."""
        client = AiClient()
        
        # This test would make a real API call
        # audio_data = client.generate_audio("Hello world", voice="alloy")
        # assert len(audio_data) > 0
        pass
