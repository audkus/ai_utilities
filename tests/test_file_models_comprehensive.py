"""Comprehensive tests for file_models.py module.

This module tests the UploadedFile model and ensures all code paths are exercised.
"""

from datetime import datetime
from typing import Optional, Set
import pytest
from pydantic import ValidationError

# Force import to ensure coverage can track the module
import ai_utilities.file_models
from ai_utilities.file_models import UploadedFile


class TestUploadedFile:
    """Test UploadedFile model comprehensively."""

    def test_minimal_creation(self) -> None:
        """Test creating UploadedFile with minimal required fields."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        assert file.file_id == "file_123"
        assert file.filename == "test.txt"
        assert file.bytes == 1024
        assert file.provider == "openai"
        assert file.purpose is None
        assert file.created_at is None

    def test_full_creation(self) -> None:
        """Test creating UploadedFile with all fields."""
        created_time = datetime.now()
        file = UploadedFile(
            file_id="file_456",
            filename="document.pdf",
            bytes=2048,
            provider="openai",
            purpose="assistants",
            created_at=created_time
        )
        
        assert file.file_id == "file_456"
        assert file.filename == "document.pdf"
        assert file.bytes == 2048
        assert file.provider == "openai"
        assert file.purpose == "assistants"
        assert file.created_at == created_time

    def test_required_fields_validation(self) -> None:
        """Test that required fields are validated."""
        # Missing file_id
        with pytest.raises(ValidationError) as exc_info:
            UploadedFile(
                filename="test.txt",
                bytes=1024,
                provider="openai"
            )
        assert "file_id" in str(exc_info.value)
        
        # Missing filename
        with pytest.raises(ValidationError) as exc_info:
            UploadedFile(
                file_id="file_123",
                bytes=1024,
                provider="openai"
            )
        assert "filename" in str(exc_info.value)
        
        # Missing bytes
        with pytest.raises(ValidationError) as exc_info:
            UploadedFile(
                file_id="file_123",
                filename="test.txt",
                provider="openai"
            )
        assert "bytes" in str(exc_info.value)
        
        # Missing provider
        with pytest.raises(ValidationError) as exc_info:
            UploadedFile(
                file_id="file_123",
                filename="test.txt",
                bytes=1024
            )
        assert "provider" in str(exc_info.value)

    def test_field_type_validation(self) -> None:
        """Test field type validation."""
        # Test that Pydantic converts types automatically
        # This test documents the actual behavior rather than forcing failures
        
        # Pydantic automatically converts string to int
        file1 = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes="1024",  # String gets converted to int
            provider="openai"
        )
        assert file1.bytes == 1024
        assert isinstance(file1.bytes, int)
        
        # Pydantic automatically converts int to datetime (timestamp)
        file2 = UploadedFile(
            file_id="file_456",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=123  # Int gets converted to datetime
        )
        assert file2.created_at is not None
        assert isinstance(file2.created_at, datetime)
        
        # Test validation that actually fails - completely wrong types
        with pytest.raises(ValidationError) as exc_info:
            UploadedFile(
                file_id=123,  # Should be string
                filename="test.txt",
                bytes=1024,
                provider="openai"
            )
        assert "file_id" in str(exc_info.value)

    @pytest.mark.parametrize("file_id", [
        "file_123",
        "file-abc-123",
        "file_with_underscores",
        "file.with.dots",
        "file-with-numbers-123",
        "a" * 100,  # Long file ID
    ])
    def test_different_file_ids(self, file_id: str) -> None:
        """Test UploadedFile with different file ID formats."""
        file = UploadedFile(
            file_id=file_id,
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        assert file.file_id == file_id

    @pytest.mark.parametrize("filename", [
        "test.txt",
        "document.pdf",
        "image.jpeg",
        "data.csv",
        "archive.tar.gz",
        "file with spaces.txt",
        "file-with-dashes.doc",
        "file_with_underscores.xlsx",
        "file.with.multiple.dots.tar.gz",
        "unicode-file-ñame.txt",
    ])
    def test_different_filenames(self, filename: str) -> None:
        """Test UploadedFile with different filename formats."""
        file = UploadedFile(
            file_id="file_123",
            filename=filename,
            bytes=1024,
            provider="openai"
        )
        assert file.filename == filename

    @pytest.mark.parametrize("bytes_size", [
        1,  # 1 byte
        1024,  # 1 KB
        1024 * 1024,  # 1 MB
        1024 * 1024 * 1024,  # 1 GB
        0,  # Zero bytes (edge case)
    ])
    def test_different_file_sizes(self, bytes_size: int) -> None:
        """Test UploadedFile with different file sizes."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=bytes_size,
            provider="openai"
        )
        assert file.bytes == bytes_size

    @pytest.mark.parametrize("provider", [
        "openai",
        "anthropic",
        "google",
        "local",
        "custom-provider",
        "provider-with-dashes",
        "provider_with_underscores",
    ])
    def test_different_providers(self, provider: str) -> None:
        """Test UploadedFile with different providers."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider=provider
        )
        assert file.provider == provider

    @pytest.mark.parametrize("purpose", [
        "assistants",
        "fine-tune",
        "vision",
        "batch",
        None,  # No purpose
    ])
    def test_different_purposes(self, purpose: Optional[str]) -> None:
        """Test UploadedFile with different purposes."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose=purpose
        )
        assert file.purpose == purpose

    def test_datetime_serialization(self) -> None:
        """Test datetime field serialization."""
        created_time = datetime(2023, 1, 1, 12, 0, 0)
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=created_time
        )
        
        # Test model_dump
        file_dict = file.model_dump()
        assert file_dict["created_at"] == "2023-01-01T12:00:00"
        
        # Test model_dump_json
        file_json = file.model_dump_json()
        assert "2023-01-01T12:00:00" in file_json

    def test_datetime_none_serialization(self) -> None:
        """Test None datetime serialization."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=None
        )
        
        # Test model_dump
        file_dict = file.model_dump()
        assert file_dict["created_at"] is None
        
        # Test model_dump_json
        file_json = file.model_dump_json()
        assert '"created_at":null' in file_json

    def test_string_representation(self) -> None:
        """Test UploadedFile string representation."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        str_repr = str(file)
        assert "UploadedFile" in str_repr
        assert "file_123" in str_repr
        assert "test.txt" in str_repr
        assert "openai" in str_repr

    def test_repr(self) -> None:
        """Test UploadedFile repr."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants"
        )
        
        repr_str = repr(file)
        assert isinstance(repr_str, str)
        assert "UploadedFile" in repr_str
        assert "file_123" in repr_str
        assert "test.txt" in repr_str
        assert "1024" in repr_str
        assert "openai" in repr_str
        assert "assistants" in repr_str

    def test_model_dict_conversion(self) -> None:
        """Test UploadedFile can be converted to dict."""
        created_time = datetime(2023, 1, 1, 12, 0, 0)
        file = UploadedFile(
            file_id="file_456",
            filename="document.pdf",
            bytes=2048,
            provider="openai",
            purpose="assistants",
            created_at=created_time
        )
        
        file_dict = file.model_dump()
        
        assert isinstance(file_dict, dict)
        assert file_dict["file_id"] == "file_456"
        assert file_dict["filename"] == "document.pdf"
        assert file_dict["bytes"] == 2048
        assert file_dict["provider"] == "openai"
        assert file_dict["purpose"] == "assistants"
        assert file_dict["created_at"] == "2023-01-01T12:00:00"

    def test_round_trip_serialization(self) -> None:
        """Test UploadedFile round-trip serialization."""
        created_time = datetime(2023, 6, 15, 14, 30, 45)
        original = UploadedFile(
            file_id="file_roundtrip",
            filename="roundtrip.txt",
            bytes=4096,
            provider="test-provider",
            purpose="test-purpose",
            created_at=created_time
        )
        
        # Convert to dict and back
        dict_data = original.model_dump()
        restored = UploadedFile(**dict_data)
        
        assert restored.file_id == original.file_id
        assert restored.filename == original.filename
        assert restored.bytes == original.bytes
        assert restored.provider == original.provider
        assert restored.purpose == original.purpose
        assert restored.created_at.isoformat() == original.created_at.isoformat()

    def test_equality(self) -> None:
        """Test UploadedFile equality comparison."""
        file1 = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        file2 = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        file3 = UploadedFile(
            file_id="file_456",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        # Pydantic models support equality
        assert file1 == file2
        assert file1 != file3

    def test_populate_by_name(self) -> None:
        """Test populate_by_name configuration."""
        # Test that we can use field names in serialization
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        # Should work with field names
        dict_data = {
            "file_id": "file_789",
            "filename": "new.txt",
            "bytes": 2048,
            "provider": "new-provider"
        }
        
        new_file = UploadedFile(**dict_data)
        assert new_file.file_id == "file_789"
        assert new_file.filename == "new.txt"
        assert new_file.bytes == 2048
        assert new_file.provider == "new-provider"
