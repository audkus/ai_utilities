"""Tests for audio processing utilities.

This module tests the audio utility functions including file loading,
validation, format conversion, and basic operations.
"""

import pytest
import tempfile
import mimetypes
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_utilities.exceptions import AudioProcessingError
from ai_utilities.audio.audio_utils import (
    validate_audio_file,
    get_audio_format,
    load_audio_file,
    get_audio_info,
    save_audio_file,
    convert_audio_format,
)
from ai_utilities.audio.audio_models import AudioFile, AudioFormat


class TestAudioValidation:
    """Test audio file validation functions."""
    
    @patch('ai_utilities.audio.audio_utils.mimetypes.guess_type')
    def test_validate_audio_file_valid(self, mock_guess_type, tmp_path):
        """Test validation of valid audio files."""
        # Mock MIME type to return audio types
        mock_guess_type.side_effect = lambda x: (f"audio/{x.split('.')[-1]}", None)
        
        # Create temporary files with different extensions
        valid_extensions = ["wav", "mp3", "flac", "ogg", "m4a", "webm"]
        
        for ext in valid_extensions:
            test_file = tmp_path / f"test.{ext}"
            test_file.write_bytes(b"fake audio data")
            
            assert validate_audio_file(test_file) is True
    
    def test_validate_audio_file_nonexistent(self):
        """Test validation of non-existent file returns False."""
        result = validate_audio_file("nonexistent.wav")
        assert result is False
    
    def test_validate_audio_file_invalid_extension(self, tmp_path):
        """Test validation of file with invalid extension."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"not audio data")
        
        assert validate_audio_file(test_file) is False
    
    def test_get_audio_format_from_extension(self, tmp_path):
        """Test getting audio format from file extension."""
        test_cases = [
            ("test.wav", AudioFormat.WAV),
            ("test.mp3", AudioFormat.MP3),
            ("test.flac", AudioFormat.FLAC),
            ("test.ogg", AudioFormat.OGG),
            ("test.m4a", AudioFormat.M4A),
            ("test.webm", AudioFormat.WEBM),
        ]
        
        for filename, expected_format in test_cases:
            test_file = tmp_path / filename
            test_file.write_bytes(b"fake audio data")
            
            result = get_audio_format(test_file)
            assert result == expected_format
    
    def test_get_audio_format_invalid_extension(self, tmp_path):
        """Test getting format from invalid extension."""
        test_file = tmp_path / "test.xyz"
        test_file.write_bytes(b"fake audio data")
        
        with pytest.raises(AudioProcessingError, match="Unsupported audio format"):
            get_audio_format(test_file)
    
    @patch('ai_utilities.audio.audio_utils.mimetypes.guess_type')
    def test_get_audio_format_from_mime_type(self, mock_guess_type, tmp_path):
        """Test getting format from MIME type when extension fails."""
        # Mock MIME type detection
        mock_guess_type.return_value = ("audio/wav", None)
        
        test_file = tmp_path / "test.unknown"
        test_file.write_bytes(b"fake audio data")
        
        result = get_audio_format(test_file)
        assert result == AudioFormat.WAV


class TestAudioFileLoading:
    """Test audio file loading functionality."""
    
    def test_load_audio_file_basic(self, tmp_path):
        """Test basic audio file loading."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = load_audio_file(test_file)
        
        assert isinstance(audio_file, AudioFile)
        assert audio_file.file_path == test_file
        assert audio_file.format == AudioFormat.WAV
        assert audio_file.file_size_bytes == len(b"fake audio data")
        assert audio_file.metadata == {}
    
    @pytest.mark.skipif(False, reason="Requires mutagen package")
    def test_load_audio_file_with_mutagen(self, tmp_path):
        """Test loading with mutagen metadata extraction."""
        # Import mutagen to check if available
        try:
            import mutagen
        except ImportError:
            pytest.skip("mutagen package not available")
        
        # Create a test audio file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio data")
        
        # Load the audio file
        audio_file = load_audio_file(test_file)
        
        # Verify basic properties (mutagen won't work with fake data, but should not crash)
        assert isinstance(audio_file, AudioFile)
        assert audio_file.file_path == test_file
        assert audio_file.format == AudioFormat.MP3
    
    @patch('ai_utilities.audio.audio_utils.WAVE_AVAILABLE', True)
    @patch('ai_utilities.audio.audio_utils.wave.open')
    def test_load_wav_file_with_wave_module(self, mock_wave_open, tmp_path):
        """Test loading WAV file with Python wave module."""
        # Mock wave file object
        mock_wave_file = MagicMock()
        mock_wave_file.getnframes.return_value = 44100
        mock_wave_file.getframerate.return_value = 44100
        mock_wave_file.getnchannels.return_value = 2
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        audio_file = load_audio_file(test_file)
        
        # Should extract duration from wave file
        assert audio_file.duration_seconds == 1.0  # 44100 frames / 44100 Hz
        assert audio_file.sample_rate == 44100
        assert audio_file.channels == 2


class TestAudioInfo:
    """Test audio information extraction."""
    
    def test_get_audio_info_valid_file(self, tmp_path):
        """Test getting info from valid audio file."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        info = get_audio_info(test_file)
        
        assert info["file_path"] == str(test_file)
        assert info["format"] == "wav"
        assert info["file_size_bytes"] == len(b"fake audio data")
        assert info["file_size_mb"] < 1.0
        assert "error" not in info
    
    def test_get_audio_info_invalid_file(self, tmp_path):
        """Test getting info from invalid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"not audio")
        
        info = get_audio_info(test_file)
        
        assert "error" in info


class TestAudioFileOperations:
    """Test audio file operations."""
    
    def test_save_audio_file(self, tmp_path):
        """Test saving audio data to file."""
        audio_data = b"fake audio data"
        output_path = tmp_path / "output.wav"
        
        saved_path = save_audio_file(audio_data, output_path)
        
        assert saved_path == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == audio_data
    
    def test_save_audio_file_creates_directories(self, tmp_path):
        """Test that save creates parent directories."""
        audio_data = b"fake audio data"
        output_path = tmp_path / "nested" / "dir" / "output.wav"
        
        saved_path = save_audio_file(audio_data, output_path)
        
        assert saved_path == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == audio_data
    
    def test_save_audio_file_error(self, tmp_path):
        """Test error handling when save fails."""
        # Try to save to a path that doesn't exist and can't be created
        audio_data = b"fake audio data"
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(AudioProcessingError, match="Failed to save audio file"):
                save_audio_file(audio_data, "/invalid/path/output.wav")


class TestAudioConversion:
    """Test audio format conversion."""
    
    def test_convert_audio_format_no_pydub(self, tmp_path):
        """Test conversion fails without pydub."""
        # Import the function directly to avoid patching issues
        from ai_utilities.audio.audio_utils import convert_audio_format, PYDUB_AVAILABLE
        
        # Temporarily set PYDUB_AVAILABLE to False
        original_value = PYDUB_AVAILABLE
        
        # Use the module directly to modify the variable
        import ai_utilities.audio.audio_utils as audio_utils_module
        audio_utils_module.PYDUB_AVAILABLE = False
        
        try:
            input_file = tmp_path / "input.wav"
            input_file.write_bytes(b"fake audio data")
            output_file = tmp_path / "output.mp3"
            
            with pytest.raises(AudioProcessingError, match="requires pydub"):
                convert_audio_format(input_file, output_file, AudioFormat.MP3)
        finally:
            # Restore original value
            audio_utils_module.PYDUB_AVAILABLE = original_value
    
    @pytest.mark.skipif(False, reason="Requires pydub package")
    def test_convert_audio_format_with_pydub(self, tmp_path):
        """Test conversion with pydub available."""
        # Import pydub to check if available
        try:
            import pydub
        except ImportError:
            pytest.skip("pydub package not available")
        
        input_file = tmp_path / "input.wav"
        input_file.write_bytes(b"fake audio data")
        output_file = tmp_path / "output.mp3"
        
        # This will fail with fake data, but should not crash due to missing pydub
        from ai_utilities.audio.audio_utils import convert_audio_format
        
        try:
            result = convert_audio_format(input_file, output_file, AudioFormat.MP3)
            # If it works, verify the result
            assert result == output_file
        except Exception as e:
            # Expected to fail with fake audio data, but should not be "requires pydub" error
            assert "requires pydub" not in str(e)
            assert "pydub" not in str(e).lower() or "available" not in str(e).lower()


class TestAudioAnalysis:
    """Test audio analysis functionality."""
    
    @patch('ai_utilities.audio.audio_utils.load_audio_file')
    @patch('ai_utilities.audio.audio_utils.WAVE_AVAILABLE', True)
    @patch('ai_utilities.audio.audio_utils.wave.open')
    def test_analyze_wav_file(self, mock_wave_open, mock_load_audio, tmp_path):
        """Test analyzing WAV file."""
        from ai_utilities.audio.audio_models import AudioFile, AudioFormat
        
        # Create real temporary file
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake wav data")
        
        # Mock audio file
        mock_audio_file = AudioFile(
            file_path=test_file,
            format=AudioFormat.WAV,
            file_size_bytes=1024,
            duration_seconds=1.0,
            sample_rate=44100,
            channels=2,
            metadata={}
        )
        mock_load_audio.return_value = mock_audio_file
        
        # Mock wave file
        mock_wave_file = MagicMock()
        mock_wave_file.getsampwidth.return_value = 2
        mock_wave_file.getnframes.return_value = 44100
        mock_wave_file.getframerate.return_value = 44100
        mock_wave_file.getnchannels.return_value = 2
        mock_wave_file.getcomptype.return_value = "NONE"
        mock_wave_file.getcompname.return_value = "not compressed"
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        
        from ai_utilities.audio.audio_utils import analyze_audio_file
        
        result = analyze_audio_file(tmp_path / "test.wav")
        
        assert result.duration_seconds == 1.0
        assert result.sample_rate == 44100
        assert result.channels == 2
        assert result.bit_depth == 16  # 2 bytes * 8 bits
        assert result.is_stereo
        assert not result.is_mono


class TestErrorHandling:
    """Test error handling in audio utilities."""
    
    def test_audio_processing_error(self):
        """Test AudioProcessingError creation."""
        error = AudioProcessingError("Test error message")
        assert str(error) == "Test error message"
    
    def test_load_invalid_file(self, tmp_path):
        """Test loading invalid file raises appropriate error."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"not audio data")
        
        with pytest.raises(AudioProcessingError):
            load_audio_file(test_file)
