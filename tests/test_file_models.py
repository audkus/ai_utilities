"""Tests for file_models.py module."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ai_utilities.file_models import UploadedFile


class TestUploadedFile:
    """Test UploadedFile model."""
    
    def test_minimal_creation(self):
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
    
    def test_full_creation(self):
        """Test creating UploadedFile with all fields."""
        created_time = datetime.now()
        file = UploadedFile(
            file_id="file_456",
            filename="document.pdf",
            bytes=2048,
            provider="anthropic",
            purpose="assistants",
            created_at=created_time
        )
        
        assert file.file_id == "file_456"
        assert file.filename == "document.pdf"
        assert file.bytes == 2048
        assert file.provider == "anthropic"
        assert file.purpose == "assistants"
        assert file.created_at == created_time
    
    def test_required_fields_validation(self):
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
    
    def test_field_types_validation(self):
        """Test field type validation."""
        # Invalid bytes type (string instead of int)
        with pytest.raises(ValidationError):
            UploadedFile(
                file_id="file_123",
                filename="test.txt",
                bytes="1024",  # Should be int
                provider="openai"
            )
        
        # Negative bytes should be allowed (Pydantic doesn't validate business logic)
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=-100,
            provider="openai"
        )
        assert file.bytes == -100
    
    def test_optional_fields_default_values(self):
        """Test that optional fields have correct default values."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        assert file.purpose is None
        assert file.created_at is None
    
    def test_purpose_field_various_values(self):
        """Test purpose field with various values."""
        purposes = ["assistants", "fine-tune", "vision", None, ""]
        
        for purpose in purposes:
            file = UploadedFile(
                file_id="file_123",
                filename="test.txt",
                bytes=1024,
                provider="openai",
                purpose=purpose
            )
            assert file.purpose == purpose
    
    def test_created_at_serialization(self):
        """Test datetime serialization for created_at field."""
        created_time = datetime(2023, 1, 15, 10, 30, 45)
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=created_time
        )
        
        # Test serialization through model_dump
        data = file.model_dump()
        assert data["created_at"] == "2023-01-15T10:30:45"
        
        # Test serialization through model_dump_json
        json_str = file.model_dump_json()
        assert "2023-01-15T10:30:45" in json_str
    
    def test_created_at_serialization_none(self):
        """Test datetime serialization when created_at is None."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=None
        )
        
        data = file.model_dump()
        assert data["created_at"] is None
    
    def test_str_representation(self):
        """Test string representation."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        str_repr = str(file)
        expected = "UploadedFile(id=file_123, filename=test.txt, provider=openai)"
        assert str_repr == expected
    
    def test_str_representation_with_long_values(self):
        """Test string representation with long values."""
        file = UploadedFile(
            file_id="very_long_file_id_123456789",
            filename="very_long_filename_with_extension.txt",
            bytes=1024,
            provider="openai"
        )
        
        str_repr = str(file)
        assert "UploadedFile(id=very_long_file_id_123456789" in str_repr
        assert "filename=very_long_filename_with_extension.txt" in str_repr
        assert "provider=openai)" in str_repr
    
    def test_repr_representation(self):
        """Test detailed string representation."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants"
        )
        
        repr_str = repr(file)
        expected = "UploadedFile(file_id='file_123', filename='test.txt', bytes=1024, provider='openai', purpose=assistants)"
        assert repr_str == expected
    
    def test_repr_representation_with_none_purpose(self):
        """Test repr representation when purpose is None."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose=None
        )
        
        repr_str = repr(file)
        expected = "UploadedFile(file_id='file_123', filename='test.txt', bytes=1024, provider='openai', purpose=None)"
        assert repr_str == expected
    
    def test_model_config_populate_by_name(self):
        """Test that model config allows population by name."""
        # Should be able to create using field names
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt", 
            bytes=1024,
            provider="openai"
        )
        
        assert file.file_id == "file_123"
        assert file.filename == "test.txt"
    
    def test_equality(self):
        """Test model equality."""
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
        
        assert file1 == file2
        assert file1 != file3
    
    def test_hashability(self):
        """Test that model is hashable."""
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
        
        # Should be able to use in sets and as dict keys
        file_set = {file1, file2}
        assert len(file_set) == 1  # Should be the same
        
        file_dict = {file1: "value1"}
        assert file_dict[file2] == "value1"  # Should retrieve same value
    
    def test_model_dump_and_load(self):
        """Test serialization and deserialization."""
        original_file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants",
            created_at=datetime(2023, 1, 15, 10, 30, 45)
        )
        
        # Serialize to dict
        data = original_file.model_dump()
        
        # Create new instance from dict
        restored_file = UploadedFile(**data)
        
        # Should be equal (except created_at which is now a string)
        assert restored_file.file_id == original_file.file_id
        assert restored_file.filename == original_file.filename
        assert restored_file.bytes == original_file.bytes
        assert restored_file.provider == original_file.provider
        assert restored_file.purpose == original_file.purpose
        # created_at is serialized as string, so we need to handle that
        assert restored_file.created_at == "2023-01-15T10:30:45"
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants",
            created_at=datetime(2023, 1, 15, 10, 30, 45)
        )
        
        json_str = file.model_dump_json()
        
        # Should contain all fields
        assert "file_123" in json_str
        assert "test.txt" in json_str
        assert "1024" in json_str
        assert "openai" in json_str
        assert "assistants" in json_str
        assert "2023-01-15T10:30:45" in json_str
    
    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_data = '{"file_id": "file_123", "filename": "test.txt", "bytes": 1024, "provider": "openai", "purpose": "assistants", "created_at": "2023-01-15T10:30:45"}'
        
        file = UploadedFile.model_validate_json(json_data)
        
        assert file.file_id == "file_123"
        assert file.filename == "test.txt"
        assert file.bytes == 1024
        assert file.provider == "openai"
        assert file.purpose == "assistants"
        assert file.created_at == "2023-01-15T10:30:45"


class TestUploadedFileEdgeCases:
    """Test edge cases for UploadedFile model."""
    
    def test_empty_string_fields(self):
        """Test with empty string fields."""
        file = UploadedFile(
            file_id="",
            filename="",
            bytes=0,
            provider="",
            purpose=""
        )
        
        assert file.file_id == ""
        assert file.filename == ""
        assert file.bytes == 0
        assert file.provider == ""
        assert file.purpose == ""
    
    def test_very_large_file_size(self):
        """Test with very large file size."""
        large_size = 10 ** 12  # 1 TB
        file = UploadedFile(
            file_id="file_large",
            filename="large_file.bin",
            bytes=large_size,
            provider="openai"
        )
        
        assert file.bytes == large_size
    
    def test_special_characters_in_filename(self):
        """Test filename with special characters."""
        special_filename = "test file-123_åßø&@#%.txt"
        file = UploadedFile(
            file_id="file_123",
            filename=special_filename,
            bytes=1024,
            provider="openai"
        )
        
        assert file.filename == special_filename
    
    def test_unicode_in_fields(self):
        """Test unicode characters in fields."""
        file = UploadedFile(
            file_id="файл_123",
            filename="документ.pdf",
            bytes=2048,
            provider="открытый_ai",
            purpose="ассистенты"
        )
        
        assert file.file_id == "файл_123"
        assert file.filename == "документ.pdf"
        assert file.provider == "открытый_ai"
        assert file.purpose == "ассистенты"
    
    def test_microsecond_precision_datetime(self):
        """Test datetime with microsecond precision."""
        precise_time = datetime(2023, 1, 15, 10, 30, 45, 123456)
        file = UploadedFile(
            file_id="file_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=precise_time
        )
        
        data = file.model_dump()
        assert data["created_at"] == "2023-01-15T10:30:45.123456"
