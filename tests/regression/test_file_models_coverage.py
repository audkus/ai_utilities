"""Coverage tests for file_models.py to reach 100%."""

import pytest
from datetime import datetime
import ai_utilities.file_models as fm


def test_file_models_import_and_basic_usage():
    """Test importing file_models and basic UploadedFile creation."""
    # Test that we can import the module
    assert hasattr(fm, 'UploadedFile')
    
    # Test basic creation with required fields only
    uploaded_file = fm.UploadedFile(
        file_id="file_123",
        filename="test.txt",
        bytes=1024,
        provider="openai"
    )
    
    assert uploaded_file.file_id == "file_123"
    assert uploaded_file.filename == "test.txt"
    assert uploaded_file.bytes == 1024
    assert uploaded_file.provider == "openai"
    assert uploaded_file.purpose is None
    assert uploaded_file.created_at is None


def test_uploaded_file_with_all_fields():
    """Test UploadedFile with all optional fields set."""
    test_time = datetime(2024, 1, 15, 10, 30, 0)
    uploaded_file = fm.UploadedFile(
        file_id="file_456",
        filename="document.pdf",
        bytes=2048,
        provider="anthropic",
        purpose="assistants",
        created_at=test_time
    )
    
    assert uploaded_file.file_id == "file_456"
    assert uploaded_file.filename == "document.pdf"
    assert uploaded_file.bytes == 2048
    assert uploaded_file.provider == "anthropic"
    assert uploaded_file.purpose == "assistants"
    assert uploaded_file.created_at == test_time


def test_uploaded_file_field_validation():
    """Test that UploadedFile validates field types and constraints."""
    # Test with valid data
    uploaded_file = fm.UploadedFile(
        file_id="valid_id",
        filename="valid_file.txt",
        bytes=100,
        provider="valid_provider"
    )
    
    # Test that fields have correct types
    assert isinstance(uploaded_file.file_id, str)
    assert isinstance(uploaded_file.filename, str)
    assert isinstance(uploaded_file.bytes, int)
    assert isinstance(uploaded_file.provider, str)
    assert isinstance(uploaded_file.purpose, (str, type(None)))
    assert isinstance(uploaded_file.created_at, (datetime, type(None)))


def test_uploaded_file_datetime_serialization():
    """Test the datetime field serializer."""
    test_time = datetime(2024, 1, 15, 10, 30, 45)
    
    # Test with datetime
    uploaded_file = fm.UploadedFile(
        file_id="file_789",
        filename="test.json",
        bytes=512,
        provider="openai",
        created_at=test_time
    )
    
    # Test serialization
    serialized = uploaded_file.serialize_created_at(test_time)
    assert serialized == "2024-01-15T10:30:45"
    
    # Test serialization with None
    uploaded_file_none = fm.UploadedFile(
        file_id="file_790",
        filename="test2.json",
        bytes=256,
        provider="openai",
        created_at=None
    )
    
    serialized_none = uploaded_file_none.serialize_created_at(None)
    assert serialized_none is None


def test_uploaded_file_string_representations():
    """Test __str__ and __repr__ methods."""
    uploaded_file = fm.UploadedFile(
        file_id="file_repr",
        filename="repr_test.txt",
        bytes=2048,
        provider="test_provider",
        purpose="test"
    )
    
    # Test __str__
    str_result = str(uploaded_file)
    expected_str = "UploadedFile(id=file_repr, filename=repr_test.txt, provider=test_provider)"
    assert str_result == expected_str
    
    # Test __repr__
    repr_result = repr(uploaded_file)
    expected_repr = "UploadedFile(file_id='file_repr', filename='repr_test.txt', bytes=2048, provider='test_provider', purpose=test)"
    assert repr_result == expected_repr


def test_uploaded_file_model_config():
    """Test that model configuration is properly set."""
    uploaded_file = fm.UploadedFile(
        file_id="config_test",
        filename="config.txt",
        bytes=100,
        provider="test"
    )
    
    # Test that populate_by_name is enabled
    config_dict = uploaded_file.model_config
    assert config_dict.get('populate_by_name') is True


def test_uploaded_file_edge_cases():
    """Test edge cases and boundary conditions."""
    # Test with empty strings
    uploaded_file = fm.UploadedFile(
        file_id="",
        filename="",
        bytes=0,
        provider=""
    )
    assert uploaded_file.file_id == ""
    assert uploaded_file.filename == ""
    assert uploaded_file.bytes == 0
    assert uploaded_file.provider == ""
    
    # Test with very large file size
    large_file = fm.UploadedFile(
        file_id="large_file",
        filename="large.bin",
        bytes=10**12,  # 1TB
        provider="storage"
    )
    assert large_file.bytes == 10**12
