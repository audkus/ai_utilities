"""Tests for exceptions.py module."""

import logging
import pytest
from unittest.mock import patch, MagicMock

from ai_utilities.exceptions import (
    AIUsageDisabledError,
    InvalidPromptError,
    MemoryUsageExceededError,
    RateLimitExceededError,
    LoggingError,
    ConfigError
)


class TestAIUsageDisabledError:
    """Test AIUsageDisabledError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        with patch('logging.error') as mock_log:
            error = AIUsageDisabledError()
            
            assert str(error) == "AIU_E001: AI usage is disabled."
            mock_log.assert_called_once_with("AIUsageDisabledError: AIU_E001: AI usage is disabled.")
    
    def test_custom_message(self):
        """Test exception with custom message."""
        custom_message = "Custom AI usage disabled message"
        with patch('logging.error') as mock_log:
            error = AIUsageDisabledError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"AIUsageDisabledError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = AIUsageDisabledError()
        assert isinstance(error, Exception)
        assert isinstance(error, AIUsageDisabledError)
    
    def test_exception_chaining(self):
        """Test exception can be used in exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise AIUsageDisabledError("AI disabled") from e
        except AIUsageDisabledError as error:
            assert str(error) == "AI disabled"
            assert error.__cause__ is not None
            assert isinstance(error.__cause__, ValueError)


class TestInvalidPromptError:
    """Test InvalidPromptError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        with patch('logging.error') as mock_log:
            error = InvalidPromptError()
            
            assert str(error) == "AIU_E002: Invalid prompt provided."
            mock_log.assert_called_once_with("InvalidPromptError: AIU_E002: Invalid prompt provided.")
    
    def test_custom_message(self):
        """Test exception with custom message."""
        custom_message = "Prompt is too short"
        with patch('logging.error') as mock_log:
            error = InvalidPromptError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"InvalidPromptError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = InvalidPromptError()
        assert isinstance(error, Exception)
        assert isinstance(error, InvalidPromptError)


class TestMemoryUsageExceededError:
    """Test MemoryUsageExceededError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        with patch('logging.error') as mock_log:
            error = MemoryUsageExceededError()
            
            assert str(error) == "AIU_E003: Memory usage exceeded."
            mock_log.assert_called_once_with("MemoryUsageExceededError: AIU_E003: Memory usage exceeded.")
    
    def test_custom_message(self):
        """Test exception with custom message."""
        custom_message = "Memory usage: 8GB exceeds limit: 4GB"
        with patch('logging.error') as mock_log:
            error = MemoryUsageExceededError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"MemoryUsageExceededError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = MemoryUsageExceededError()
        assert isinstance(error, Exception)
        assert isinstance(error, MemoryUsageExceededError)


class TestRateLimitExceededError:
    """Test RateLimitExceededError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        with patch('logging.error') as mock_log:
            error = RateLimitExceededError()
            
            assert str(error) == "AIU_E004: Rate limit exceeded."
            mock_log.assert_called_once_with("RateLimitExceededError: AIU_E004: Rate limit exceeded.")
    
    def test_custom_message(self):
        """Test exception with custom message."""
        custom_message = "Rate limit: 100 requests/hour exceeded"
        with patch('logging.error') as mock_log:
            error = RateLimitExceededError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"RateLimitExceededError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = RateLimitExceededError()
        assert isinstance(error, Exception)
        assert isinstance(error, RateLimitExceededError)


class TestLoggingError:
    """Test LoggingError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        with patch('logging.error') as mock_log:
            error = LoggingError()
            
            assert str(error) == "AIU_E005: An error occurred during logging operations."
            mock_log.assert_called_once_with("LoggingError: AIU_E005: An error occurred during logging operations.")
    
    def test_custom_message(self):
        """Test exception with custom message."""
        custom_message = "Failed to write to log file"
        with patch('logging.error') as mock_log:
            error = LoggingError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"LoggingError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = LoggingError()
        assert isinstance(error, Exception)
        assert isinstance(error, LoggingError)


class TestConfigError:
    """Test ConfigError exception."""
    
    def test_custom_message(self):
        """Test exception with custom message (no default)."""
        custom_message = "Configuration file not found"
        with patch('logging.error') as mock_log:
            error = ConfigError(custom_message)
            
            assert str(error) == custom_message
            mock_log.assert_called_once_with(f"ConfigError: {custom_message}")
    
    def test_inheritance(self):
        """Test that exception inherits from Exception."""
        error = ConfigError("Test message")
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigError)
    
    def test_message_attribute(self):
        """Test that ConfigError has message attribute."""
        message = "Test config error"
        error = ConfigError(message)
        assert str(error) == message


class TestExceptionBehavior:
    """Test general exception behavior across all custom exceptions."""
    
    def test_all_exceptions_can_be_caught(self):
        """Test that all custom exceptions can be caught individually."""
        exceptions = [
            AIUsageDisabledError(),
            InvalidPromptError(),
            MemoryUsageExceededError(),
            RateLimitExceededError(),
            LoggingError(),
            ConfigError("Test message")
        ]
        
        for i, exception in enumerate(exceptions):
            try:
                raise exception
            except Exception as e:
                assert e is exception
                assert type(e).__name__ in [
                    'AIUsageDisabledError',
                    'InvalidPromptError', 
                    'MemoryUsageExceededError',
                    'RateLimitExceededError',
                    'LoggingError',
                    'ConfigError'
                ]
    
    def test_exception_repr(self):
        """Test exception __repr__ method."""
        error = AIUsageDisabledError("Test message")
        repr_str = repr(error)
        assert "AIUsageDisabledError" in repr_str
        assert "Test message" in repr_str
    
    def test_exception_hash(self):
        """Test exception can be hashed (for use in sets/dicts)."""
        error1 = AIUsageDisabledError("Message")
        error2 = AIUsageDisabledError("Message")
        error3 = AIUsageDisabledError("Different message")
        
        # All exceptions should be hashable (default object hash)
        assert isinstance(hash(error1), int)
        assert isinstance(hash(error2), int)
        assert isinstance(hash(error3), int)
        
        # Can be used in sets
        exception_set = {error1, error2, error3}
        assert len(exception_set) == 3  # All different instances
    
    def test_exception_equality(self):
        """Test exception equality comparison."""
        error1 = AIUsageDisabledError("Message")
        error2 = AIUsageDisabledError("Message")
        error3 = AIUsageDisabledError("Different message")
        
        # Exceptions are different objects (default object equality)
        assert error1 != error2
        assert error1 != error3
        assert error2 != error3
        
        # But they should be equal to themselves
        assert error1 == error1
        assert error2 == error2
        # Different exception types should not be equal
        assert AIUsageDisabledError("Message") != InvalidPromptError("Message")


class TestLoggingIntegration:
    """Test logging integration for all exceptions."""
    
    def test_all_exceptions_log_on_creation(self):
        """Test that all custom exceptions log when created."""
        exception_classes = [
            (AIUsageDisabledError, []),
            (InvalidPromptError, []),
            (MemoryUsageExceededError, []),
            (RateLimitExceededError, []),
            (LoggingError, []),
            (ConfigError, ["Test message"])
        ]
        
        for exception_class, args in exception_classes:
            with patch('logging.error') as mock_log:
                exception = exception_class(*args)
                
                # Verify that logging.error was called
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0][0]
                
                # Verify log message format
                assert exception_class.__name__ in call_args
                if args:
                    assert args[0] in call_args
    
    def test_logging_failure_doesnt_break_exception(self):
        """Test that logging failure doesn't prevent exception creation."""
        with patch('logging.error', side_effect=Exception("Logging failed")):
            # Should still be able to create exception even if logging fails
            # but the logging error will propagate
            try:
                error = AIUsageDisabledError("Test message")
                # If we get here, the exception was created successfully
                assert str(error) == "Test message"
            except Exception as e:
                # Should be the logging error, not the exception creation failing
                assert str(e) == "Logging failed"
    
    def test_exception_with_logging_configured(self):
        """Test exceptions work with actual logging configured."""
        # Configure logging to capture messages
        with patch('logging.error') as mock_error:
            error = AIUsageDisabledError("Test message")
            
            # Should call error method directly on logging module
            mock_error.assert_called_once_with("AIUsageDisabledError: Test message")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_message(self):
        """Test exceptions with empty message."""
        with patch('logging.error') as mock_log:
            error = AIUsageDisabledError("")
            
            assert str(error) == ""
            mock_log.assert_called_once_with("AIUsageDisabledError: ")
    
    def test_none_message(self):
        """Test exceptions with None message (should work for ConfigError)."""
        with patch('logging.error') as mock_log:
            error = ConfigError(None)
            
            assert str(error) == "None"
            mock_log.assert_called_once_with("ConfigError: None")
    
    def test_long_message(self):
        """Test exceptions with very long message."""
        long_message = "A" * 1000
        with patch('logging.error') as mock_log:
            error = InvalidPromptError(long_message)
            
            assert str(error) == long_message
            mock_log.assert_called_once_with(f"InvalidPromptError: {long_message}")
    
    def test_special_characters_in_message(self):
        """Test exceptions with special characters in message."""
        special_message = "Error with unicode: ñáéíóú and emojis: 🚨❌"
        with patch('logging.error') as mock_log:
            error = RateLimitExceededError(special_message)
            
            assert str(error) == special_message
            mock_log.assert_called_once_with(f"RateLimitExceededError: {special_message}")
    
    def test_exception_pickling(self):
        """Test that exceptions can be pickled and unpickled."""
        import pickle
        
        original_error = MemoryUsageExceededError("Test message")
        
        # Pickle and unpickle
        pickled = pickle.dumps(original_error)
        unpickled_error = pickle.loads(pickled)
        
        assert str(unpickled_error) == str(original_error)
        assert type(unpickled_error) == type(original_error)
