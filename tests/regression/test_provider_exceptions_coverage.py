"""Coverage tests for provider_exceptions.py to reach 100%."""

import pytest
import ai_utilities.providers.provider_exceptions as pe


def test_provider_configuration_error():
    """Test ProviderConfigurationError exception."""
    # Test creation with required fields
    error = pe.ProviderConfigurationError(
        message="Invalid API key",
        provider="openai"
    )
    
    # Test attributes
    assert error.message == "Invalid API key"
    assert error.provider == "openai"
    
    # Test string representation
    error_str = str(error)
    assert error_str == "Provider 'openai' configuration error: Invalid API key"
    
    # Test that it's an exception
    assert isinstance(error, Exception)
    
    # Test raising and catching
    try:
        raise error
    except pe.ProviderConfigurationError as e:
        assert e.message == "Invalid API key"
        assert e.provider == "openai"


def test_provider_capability_error():
    """Test ProviderCapabilityError exception."""
    # Test creation with capability only
    error1 = pe.ProviderCapabilityError(capability="tools")
    
    # Test default message generation
    assert error1.capability == "tools"
    assert error1.provider is None
    assert error1.message == "tools"  # default message is capability
    
    # Test string representation
    assert str(error1) == "tools"
    
    # Test creation with all fields
    error2 = pe.ProviderCapabilityError(
        capability="images",
        provider="anthropic",
        message="Images not supported"
    )
    
    assert error2.capability == "images"
    assert error2.provider == "anthropic"
    assert error2.message == "Images not supported"
    assert str(error2) == "Images not supported"
    
    # Test that it's an exception
    assert isinstance(error2, Exception)
    
    # Test raising and catching
    try:
        raise error2
    except pe.ProviderCapabilityError as e:
        assert e.capability == "images"
        assert e.provider == "anthropic"


def test_missing_optional_dependency_error():
    """Test MissingOptionalDependencyError exception."""
    # Test creation
    error = pe.MissingOptionalDependencyError(dependency="torch")
    
    # Test attributes
    assert error.dependency == "torch"
    assert error.message == "torch"  # message property returns dependency
    
    # Test string representation
    assert str(error) == "torch"
    
    # Test that it's an exception
    assert isinstance(error, Exception)
    
    # Test raising and catching
    try:
        raise error
    except pe.MissingOptionalDependencyError as e:
        assert e.dependency == "torch"
        assert e.message == "torch"


def test_file_transfer_error():
    """Test FileTransferError exception."""
    # Test creation with required fields only
    error1 = pe.FileTransferError(
        operation="upload",
        provider="openai"
    )
    
    # Test default message generation
    assert error1.operation == "upload"
    assert error1.provider == "openai"
    assert error1.inner_error is None
    assert error1.message == "upload"  # default message is operation
    
    # Test string representation without inner error
    error1_str = str(error1)
    assert error1_str == "upload failed for provider 'openai'"
    
    # Test creation with all fields
    inner_error = ValueError("File too large")
    error2 = pe.FileTransferError(
        operation="download",
        provider="anthropic",
        inner_error=inner_error,
        message="Custom download error"
    )
    
    assert error2.operation == "download"
    assert error2.provider == "anthropic"
    assert error2.inner_error == inner_error
    assert error2.message == "Custom download error"
    
    # Test string representation with inner error - uses base_msg + inner_error
    error2_str = str(error2)
    assert error2_str == "download failed for provider 'anthropic': File too large"
    
    # Test that it's an exception
    assert isinstance(error2, Exception)
    
    # Test raising and catching
    try:
        raise error2
    except pe.FileTransferError as e:
        assert e.operation == "download"
        assert e.provider == "anthropic"
        assert e.inner_error == inner_error


def test_exception_hierarchy():
    """Test that all exceptions are distinct and inherit from Exception."""
    # Create instances of each exception
    config_error = pe.ProviderConfigurationError("msg", "provider")
    capability_error = pe.ProviderCapabilityError("capability")
    dependency_error = pe.MissingOptionalDependencyError("dependency")
    file_error = pe.FileTransferError("op", "provider")
    
    # Test they are all exceptions
    assert isinstance(config_error, Exception)
    assert isinstance(capability_error, Exception)
    assert isinstance(dependency_error, Exception)
    assert isinstance(file_error, Exception)
    
    # Test they are distinct types
    assert type(config_error) is not type(capability_error)
    assert type(capability_error) is not type(dependency_error)
    assert type(dependency_error) is not type(file_error)
    
    # Test specific exception catching works
    exceptions = [config_error, capability_error, dependency_error, file_error]
    
    # Should catch config_error specifically
    try:
        raise config_error
    except pe.ProviderConfigurationError:
        caught_specific = True
    except Exception:
        caught_specific = False
    assert caught_specific
    
    # Should catch capability_error specifically
    try:
        raise capability_error
    except pe.ProviderCapabilityError:
        caught_specific = True
    except Exception:
        caught_specific = False
    assert caught_specific


def test_dataclass_properties():
    """Test that dataclass properties work correctly."""
    # Test ProviderConfigurationError
    config_error = pe.ProviderConfigurationError("test msg", "test provider")
    assert hasattr(config_error, '__dataclass_fields__')
    
    # Test ProviderCapabilityError with None message (triggers __post_init__)
    capability_error = pe.ProviderCapabilityError("test_capability")
    assert capability_error.message == "test_capability"  # set by __post_init__
    
    # Test FileTransferError with None message (triggers __post_init__)
    file_error = pe.FileTransferError("test_op", "test_provider")
    assert file_error.message == "test_op"  # set by __post_init__
    
    # Test MissingOptionalDependencyError property
    dependency_error = pe.MissingOptionalDependencyError("test_dep")
    assert hasattr(dependency_error, 'message')
    assert dependency_error.message == "test_dep"
