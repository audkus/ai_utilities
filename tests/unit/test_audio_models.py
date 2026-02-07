"""Tests for audio processing models.

This module tests the Pydantic models used for audio processing,
including validation, serialization, and business logic.
"""

import pytest
from pathlib import Path
from datetime import datetime

from ai_utilities.audio.audio_models import (
    AudioFormat,
    AudioFile,
    TranscriptionRequest,
    TranscriptionResult,
    TranscriptionSegment,
    AudioGenerationRequest,
    AudioGenerationResult,
    AudioAnalysisResult,
)


class TestAudioFormat:
    """Test AudioFormat enum."""
    
    def test_audio_format_values(self):
        """Test that AudioFormat has expected values."""
        expected_formats = ["wav", "mp3", "flac", "ogg", "m4a", "webm"]
        actual_formats = [fmt.value for fmt in AudioFormat]
        
        assert actual_formats == expected_formats
    
    def test_audio_format_creation(self):
        """Test creating AudioFormat from string."""
        assert AudioFormat("wav") == AudioFormat.WAV
        assert AudioFormat("mp3") == AudioFormat.MP3
    
    def test_audio_format_invalid(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            AudioFormat("invalid")


class TestAudioFile:
    """Test AudioFile model."""
    
    def test_audio_file_creation(self, tmp_path):
        """Test creating a valid AudioFile."""
        # Create a temporary file
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            duration_seconds=10.5,
            sample_rate=44100,
            channels=2,
            file_size_bytes=1024,
            metadata={"title": "Test Audio"}
        )
        
        assert audio_file.file_path == test_file
        assert audio_file.format == AudioFormat.WAV
        assert audio_file.duration_seconds == 10.5
        assert audio_file.sample_rate == 44100
        assert audio_file.channels == 2
        assert audio_file.file_size_bytes == 1024
        assert audio_file.metadata["title"] == "Test Audio"
    
    def test_audio_file_invalid_path(self):
        """Test that non-existent file path raises error."""
        with pytest.raises(ValueError, match="Audio file does not exist"):
            AudioFile(
                file_path=Path("nonexistent.wav"),
                format=AudioFormat.WAV,
                file_size_bytes=1024
            )
    
    def test_audio_file_invalid_size(self, tmp_path):
        """Test that invalid file size raises error."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        with pytest.raises(ValueError, match="File size must be positive"):
            AudioFile(
                file_path=test_file,
                format=AudioFormat.WAV,
                file_size_bytes=0
            )
    
    def test_audio_file_properties(self, tmp_path):
        """Test AudioFile calculated properties."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        # 1MB file
        audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            file_size_bytes=1024 * 1024
        )
        
        assert audio_file.file_size_mb == 1.0
        assert not audio_file.is_large_file
        
        # 30MB file (over 25MB limit)
        audio_file.file_size_bytes = 30 * 1024 * 1024
        assert audio_file.file_size_mb == 30.0
        assert audio_file.is_large_file


class TestTranscriptionRequest:
    """Test TranscriptionRequest model."""
    
    def test_transcription_request_creation(self, tmp_path):
        """Test creating a valid TranscriptionRequest."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            file_size_bytes=1024
        )
        
        request = TranscriptionRequest(
            audio_file=audio_file,
            language="en",
            model="whisper-1",
            temperature=0.5,
            response_format="json"
        )
        
        assert request.audio_file == audio_file
        assert request.language == "en"
        assert request.model == "whisper-1"
        assert request.temperature == 0.5
        assert request.response_format == "json"
    
    def test_transcription_request_temperature_validation(self, tmp_path):
        """Test temperature validation."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        audio_file = AudioFile(file_path=test_file, format=AudioFormat.WAV, file_size_bytes=1024)
        
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0]:
            request = TranscriptionRequest(audio_file=audio_file, temperature=temp)
            assert request.temperature == temp
        
        # Invalid temperatures
        for temp in [-0.1, 1.1]:
            with pytest.raises(ValueError):
                TranscriptionRequest(audio_file=audio_file, temperature=temp)
    
    def test_transcription_request_response_format_validation(self, tmp_path):
        """Test response format validation."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        audio_file = AudioFile(file_path=test_file, format=AudioFormat.WAV, file_size_bytes=1024)
        
        # Valid formats
        valid_formats = ["json", "text", "srt", "verbose_json", "vtt"]
        for fmt in valid_formats:
            request = TranscriptionRequest(audio_file=audio_file, response_format=fmt)
            assert request.response_format == fmt
        
        # Invalid format
        with pytest.raises(ValueError, match="Response format must be one of"):
            TranscriptionRequest(audio_file=audio_file, response_format="invalid")


class TestTranscriptionSegment:
    """Test TranscriptionSegment model."""
    
    def test_transcription_segment_creation(self):
        """Test creating a valid TranscriptionSegment."""
        segment = TranscriptionSegment(
            start_time=1.0,
            end_time=2.5,
            text="Hello world",
            confidence=0.95
        )
        
        assert segment.start_time == 1.0
        assert segment.end_time == 2.5
        assert isinstance(segment.text, str)  # Contract: text is string type
        assert len(segment.text) > 0  # Contract: non-empty text
        assert segment.confidence == 0.95
    
    def test_transcription_segment_end_time_validation(self):
        """Test that end time must be after start time."""
        # Valid: end after start
        segment = TranscriptionSegment(start_time=1.0, end_time=2.0, text="Test")
        assert segment.end_time == 2.0
        
        # Invalid: end before start
        with pytest.raises(ValueError, match="End time must be after start time"):
            TranscriptionSegment(start_time=2.0, end_time=1.0, text="Test")
        
        # Invalid: end equals start
        with pytest.raises(ValueError, match="End time must be after start time"):
            TranscriptionSegment(start_time=1.0, end_time=1.0, text="Test")


class TestTranscriptionResult:
    """Test TranscriptionResult model."""
    
    def test_transcription_result_creation(self):
        """Test creating a valid TranscriptionResult."""
        result = TranscriptionResult(
            text="Hello world, this is a test.",
            language="en",
            duration_seconds=5.0,
            model_used="whisper-1",
            confidence=0.95
        )
        
        assert isinstance(result.text, str)  # Contract: text is string type
        assert len(result.text) > 0  # Contract: non-empty text
        assert result.language == "en"
        assert result.duration_seconds == 5.0
        assert result.model_used == "whisper-1"
        assert result.confidence == 0.95
    
    def test_transcription_result_properties(self):
        """Test TranscriptionResult calculated properties."""
        result = TranscriptionResult(
            text="Hello world, this is a test.",
            model_used="whisper-1"
        )
        
        assert result.word_count == 6
        assert result.character_count == len("Hello world, this is a test.")
    
    def test_transcription_result_with_segments(self):
        """Test TranscriptionResult with segments."""
        segments = [
            TranscriptionSegment(start_time=0.0, end_time=2.0, text="Hello world"),
            TranscriptionSegment(start_time=2.0, end_time=4.0, text="this is a test")
        ]
        
        result = TranscriptionResult(
            text="Hello world this is a test",
            model_used="whisper-1",
            segments=segments
        )
        
        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello world"
        assert result.segments[1].text == "this is a test"


class TestAudioGenerationRequest:
    """Test AudioGenerationRequest model."""
    
    def test_audio_generation_request_creation(self):
        """Test creating a valid AudioGenerationRequest."""
        request = AudioGenerationRequest(
            text="Hello, this is a test.",
            voice="alloy",
            model="tts-1",
            speed=1.0,
            response_format=AudioFormat.MP3
        )
        
        assert isinstance(request.text, str)  # Contract: text is string type
        assert len(request.text) > 0  # Contract: non-empty text
        assert request.voice == "alloy"
        assert request.model == "tts-1"
        assert request.speed == 1.0
        assert request.response_format == AudioFormat.MP3
    
    def test_audio_generation_request_speed_validation(self):
        """Test speed validation."""
        # Valid speeds
        for speed in [0.25, 0.5, 1.0, 2.0, 4.0]:
            request = AudioGenerationRequest(text="Test", speed=speed)
            assert request.speed == speed
        
        # Invalid speeds
        for speed in [0.24, 4.1]:
            with pytest.raises(ValueError):
                AudioGenerationRequest(text="Test", speed=speed)
    
    def test_audio_generation_request_text_validation(self):
        """Test text validation."""
        # Valid text
        request = AudioGenerationRequest(text="Hello world")
        assert isinstance(request.text, str)  # Contract: text is string type
        assert len(request.text) > 0  # Contract: non-empty text
        
        # Empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            AudioGenerationRequest(text="   ")
        
        # Text too long
        long_text = "a" * 4097
        with pytest.raises(ValueError, match="Text is too long"):
            AudioGenerationRequest(text=long_text)


class TestAudioGenerationResult:
    """Test AudioGenerationResult model."""
    
    def test_audio_generation_result_creation(self):
        """Test creating a valid AudioGenerationResult."""
        audio_data = b"fake audio data"
        
        result = AudioGenerationResult(
            audio_data=audio_data,
            format=AudioFormat.MP3,
            text="Hello world",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=len(audio_data)
        )
        
        assert result.audio_data == audio_data
        assert result.format == AudioFormat.MP3
        assert isinstance(result.text, str)  # Contract: text is string type
        assert len(result.text) > 0  # Contract: non-empty text
        assert result.voice == "alloy"
        assert result.model_used == "tts-1"
        assert result.file_size_bytes == len(audio_data)
    
    def test_audio_generation_result_properties(self):
        """Test AudioGenerationResult calculated properties."""
        # 1MB of data
        audio_data = b"x" * (1024 * 1024)
        
        result = AudioGenerationResult(
            audio_data=audio_data,
            format=AudioFormat.MP3,
            text="Test",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=len(audio_data)
        )
        
        assert result.file_size_mb == 1.0
    
    def test_audio_generation_result_save_to_file(self, tmp_path):
        """Test saving audio data to file."""
        audio_data = b"fake audio data"
        
        result = AudioGenerationResult(
            audio_data=audio_data,
            format=AudioFormat.MP3,
            text="Test",
            voice="alloy",
            model_used="tts-1",
            file_size_bytes=len(audio_data)
        )
        
        output_path = tmp_path / "output.mp3"
        saved_path = result.save_to_file(output_path)
        
        assert saved_path == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == audio_data


class TestAudioAnalysisResult:
    """Test AudioAnalysisResult model."""
    
    def test_audio_analysis_result_creation(self, tmp_path):
        """Test creating a valid AudioAnalysisResult."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            file_size_bytes=1024
        )
        
        result = AudioAnalysisResult(
            audio_file=audio_file,
            duration_seconds=10.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16
        )
        
        assert result.audio_file == audio_file
        assert result.duration_seconds == 10.0
        assert result.sample_rate == 44100
        assert result.channels == 2
        assert result.bit_depth == 16
    
    def test_audio_analysis_result_properties(self, tmp_path):
        """Test AudioAnalysisResult boolean properties."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            file_size_bytes=1024
        )
        
        # Mono file
        mono_result = AudioAnalysisResult(
            audio_file=audio_file,
            duration_seconds=10.0,
            sample_rate=44100,
            channels=1
        )
        
        assert mono_result.is_mono
        assert not mono_result.is_stereo
        
        # Stereo file
        stereo_result = AudioAnalysisResult(
            audio_file=audio_file,
            duration_seconds=10.0,
            sample_rate=44100,
            channels=2
        )
        
        assert not stereo_result.is_mono
        assert stereo_result.is_stereo
