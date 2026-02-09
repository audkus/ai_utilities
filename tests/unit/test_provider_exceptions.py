"""Unit tests for provider_exceptions module."""

import pytest

from ai_utilities.providers.provider_exceptions import (
    ProviderConfigurationError,
    ProviderCapabilityError,
    MissingOptionalDependencyError,
    FileTransferError
)


class TestProviderConfigurationError:
    """Test cases for ProviderConfigurationError."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating ProviderConfigurationError with required fields."""
        error = ProviderConfigurationError(
            message="Invalid API key",
            provider="openai"
        )
        
        assert error.message == "Invalid API key"
        assert error.provider == "openai"
        assert isinstance(error, Exception)

    def test_string_representation(self) -> None:
        """Test string representation of ProviderConfigurationError."""
        error = ProviderConfigurationError(
            message="Missing base URL",
            provider="anthropic"
        )
        
        str_repr = str(error)
        expected = "Provider 'anthropic' configuration error: Missing base URL"
        assert str_repr == expected

    def test_exception_inheritance(self) -> None:
        """Test that ProviderConfigurationError is an Exception."""
        error = ProviderConfigurationError(
            message="Test error",
            provider="test"
        )
        
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_raising_and_catching(self) -> None:
        """Test raising and catching ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError) as exc_info:
            raise ProviderConfigurationError(
                message="Configuration failed",
                provider="test-provider"
            )
        
        error = exc_info.value
        assert error.message == "Configuration failed"
        assert error.provider == "test-provider"
        assert "Configuration failed" in str(error)

    def test_dataclass_properties(self) -> None:
        """Test dataclass properties of ProviderConfigurationError."""
        error1 = ProviderConfigurationError(
            message="Same message",
            provider="same-provider"
        )
        error2 = ProviderConfigurationError(
            message="Same message",
            provider="same-provider"
        )
        error3 = ProviderConfigurationError(
            message="Different message",
            provider="same-provider"
        )
        
        # Dataclasses should be equal if all fields are equal
        assert error1 == error2
        assert error1 != error3


class TestProviderCapabilityError:
    """Test cases for ProviderCapabilityError."""

    def test_creation_with_capability_only(self) -> None:
        """Test creating ProviderCapabilityError with only capability."""
        error = ProviderCapabilityError(capability="streaming")
        
        assert error.capability == "streaming"
        assert error.provider is None
        assert error.message == "streaming"  # Default message

    def test_creation_with_all_fields(self) -> None:
        """Test creating ProviderCapabilityError with all fields."""
        error = ProviderCapabilityError(
            capability="tools",
            provider="openai",
            message="Tools not supported in current model"
        )
        
        assert error.capability == "tools"
        assert error.provider == "openai"
        assert error.message == "Tools not supported in current model"

    def test_post_init_default_message(self) -> None:
        """Test that post_init sets default message when None."""
        error = ProviderCapabilityError(
            capability="json_mode",
            provider="test"
        )
        
        # message should be set to capability when None
        assert error.message == "json_mode"

    def test_post_init_custom_message(self) -> None:
        """Test that post_init preserves custom message."""
        custom_message = "Custom capability error message"
        error = ProviderCapabilityError(
            capability="images",
            provider="test",
            message=custom_message
        )
        
        # message should remain unchanged when provided
        assert error.message == custom_message

    def test_string_representation(self) -> None:
        """Test string representation of ProviderCapabilityError."""
        error = ProviderCapabilityError(
            capability="files",
            provider="anthropic",
            message="File upload not supported"
        )
        
        str_repr = str(error)
        assert str_repr == "File upload not supported"

    def test_string_representation_with_default_message(self) -> None:
        """Test string representation with default message."""
        error = ProviderCapabilityError(capability="streaming")
        
        str_repr = str(error)
        assert str_repr == "streaming"

    def test_exception_inheritance(self) -> None:
        """Test that ProviderCapabilityError is an Exception."""
        error = ProviderCapabilityError(capability="test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_raising_and_catching(self) -> None:
        """Test raising and catching ProviderCapabilityError."""
        with pytest.raises(ProviderCapabilityError) as exc_info:
            raise ProviderCapabilityError(
                capability="tools",
                provider="test",
                message="Tools not available"
            )
        
        error = exc_info.value
        assert error.capability == "tools"
        assert error.provider == "test"
        assert error.message == "Tools not available"

    def test_dataclass_properties(self) -> None:
        """Test dataclass properties of ProviderCapabilityError."""
        error1 = ProviderCapabilityError(
            capability="same",
            provider="same",
            message="same"
        )
        error2 = ProviderCapabilityError(
            capability="same",
            provider="same",
            message="same"
        )
        error3 = ProviderCapabilityError(
            capability="different",
            provider="same",
            message="same"
        )
        
        assert error1 == error2
        assert error1 != error3


class TestMissingOptionalDependencyError:
    """Test cases for MissingOptionalDependencyError."""

    def test_creation(self) -> None:
        """Test creating MissingOptionalDependencyError."""
        error = MissingOptionalDependencyError(dependency="openai")
        
        assert error.dependency == "openai"
        assert isinstance(error, Exception)

    def test_message_property(self) -> None:
        """Test message property returns dependency."""
        error = MissingOptionalDependencyError(dependency="anthropic")
        
        assert error.message == "anthropic"

    def test_string_representation(self) -> None:
        """Test string representation of MissingOptionalDependencyError."""
        error = MissingOptionalDependencyError(dependency="requests")
        
        str_repr = str(error)
        assert str_repr == "requests"

    def test_message_property_and_str_are_same(self) -> None:
        """Test that message property and str() return the same value."""
        error = MissingOptionalDependencyError(dependency="numpy")
        
        assert error.message == str(error) == "numpy"

    def test_exception_inheritance(self) -> None:
        """Test that MissingOptionalDependencyError is an Exception."""
        error = MissingOptionalDependencyError(dependency="test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_raising_and_catching(self) -> None:
        """Test raising and catching MissingOptionalDependencyError."""
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            raise MissingOptionalDependencyError(dependency="pandas")
        
        error = exc_info.value
        assert error.dependency == "pandas"
        assert str(error) == "pandas"

    def test_dataclass_properties(self) -> None:
        """Test dataclass properties of MissingOptionalDependencyError."""
        error1 = MissingOptionalDependencyError(dependency="same")
        error2 = MissingOptionalDependencyError(dependency="same")
        error3 = MissingOptionalDependencyError(dependency="different")
        
        assert error1 == error2
        assert error1 != error3


class TestFileTransferError:
    """Test cases for FileTransferError."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating FileTransferError with required fields."""
        error = FileTransferError(
            operation="upload",
            provider="openai"
        )
        
        assert error.operation == "upload"
        assert error.provider == "openai"
        assert error.inner_error is None
        assert error.message == "upload"  # Default message

    def test_creation_with_all_fields(self) -> None:
        """Test creating FileTransferError with all fields."""
        inner_error = ValueError("Original error")
        error = FileTransferError(
            operation="download",
            provider="anthropic",
            inner_error=inner_error,
            message="Custom download error"
        )
        
        assert error.operation == "download"
        assert error.provider == "anthropic"
        assert error.inner_error == inner_error
        assert error.message == "Custom download error"

    def test_post_init_default_message(self) -> None:
        """Test that post_init sets default message when None."""
        error = FileTransferError(
            operation="delete",
            provider="test"
        )
        
        # message should be set to operation when None
        assert error.message == "delete"

    def test_post_init_custom_message(self) -> None:
        """Test that post_init preserves custom message."""
        custom_message = "Custom file operation error"
        error = FileTransferError(
            operation="upload",
            provider="test",
            message=custom_message
        )
        
        # message should remain unchanged when provided
        assert error.message == custom_message

    def test_string_representation_without_inner_error(self) -> None:
        """Test string representation without inner error."""
        error = FileTransferError(
            operation="upload",
            provider="openai"
        )
        
        str_repr = str(error)
        expected = "upload failed for provider 'openai'"
        assert str_repr == expected

    def test_string_representation_with_inner_error(self) -> None:
        """Test string representation with inner error."""
        inner_error = ConnectionError("Network timeout")
        error = FileTransferError(
            operation="download",
            provider="anthropic",
            inner_error=inner_error
        )
        
        str_repr = str(error)
        expected = "download failed for provider 'anthropic': Network timeout"
        assert str_repr == expected

    def test_string_representation_with_custom_message_and_inner_error(self) -> None:
        """Test string representation with custom message and inner error."""
        inner_error = PermissionError("Access denied")
        error = FileTransferError(
            operation="upload",
            provider="test",
            inner_error=inner_error,
            message="Custom upload message"
        )
        
        str_repr = str(error)
        expected = "upload failed for provider 'test': Access denied"
        assert str_repr == expected

    def test_exception_inheritance(self) -> None:
        """Test that FileTransferError is an Exception."""
        error = FileTransferError(
            operation="test",
            provider="test"
        )
        
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_raising_and_catching(self) -> None:
        """Test raising and catching FileTransferError."""
        with pytest.raises(FileTransferError) as exc_info:
            raise FileTransferError(
                operation="upload",
                provider="test",
                message="Upload failed"
            )
        
        error = exc_info.value
        assert error.operation == "upload"
        assert error.provider == "test"
        assert error.message == "Upload failed"

    def test_dataclass_properties(self) -> None:
        """Test dataclass properties of FileTransferError."""
        inner_error = ValueError("test")
        error1 = FileTransferError(
            operation="same",
            provider="same",
            inner_error=inner_error,
            message="same"
        )
        error2 = FileTransferError(
            operation="same",
            provider="same",
            inner_error=inner_error,
            message="same"
        )
        error3 = FileTransferError(
            operation="different",
            provider="same",
            inner_error=inner_error,
            message="same"
        )
        
        assert error1 == error2
        assert error1 != error3

    def test_inner_error_can_be_any_exception(self) -> None:
        """Test that inner_error can be any type of exception."""
        exceptions_to_test = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            KeyError("Key error"),
            CustomException("Custom error")
        ]
        
        for exc in exceptions_to_test:
            error = FileTransferError(
                operation="test",
                provider="test",
                inner_error=exc
            )
            assert error.inner_error == exc
            assert str(exc) in str(error)


class CustomException(Exception):
    """Custom exception for testing."""
    pass


class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_all_exceptions_are_distinct(self) -> None:
        """Test that all exception classes are distinct."""
        exceptions = [
            ProviderConfigurationError("msg", "provider"),
            ProviderCapabilityError("capability"),
            MissingOptionalDependencyError("dependency"),
            FileTransferError("op", "provider")
        ]
        
        # All should be instances of Exception
        for exc in exceptions:
            assert isinstance(exc, Exception)
        
        # All should be different types
        types = [type(exc) for exc in exceptions]
        assert len(set(types)) == len(types)

    def test_exception_catching_specificity(self) -> None:
        """Test that exceptions can be caught specifically."""
        try:
            raise ProviderConfigurationError("config error", "test")
        except ProviderCapabilityError:
            pytest.fail("Should not catch ProviderCapabilityError")
        except ProviderConfigurationError as e:
            assert e.message == "config error"
            assert e.provider == "test"

    def test_exception_catching_base_exception(self) -> None:
        """Test that all exceptions can be caught as base Exception."""
        exceptions_to_test = [
            ProviderConfigurationError("config", "test"),
            ProviderCapabilityError("capability"),
            MissingOptionalDependencyError("dep"),
            FileTransferError("op", "provider")
        ]
        
        for exc in exceptions_to_test:
            try:
                raise exc
            except Exception as caught:
                assert caught is exc
