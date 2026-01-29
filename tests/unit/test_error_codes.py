"""Comprehensive tests for error codes infrastructure - Phase 7.

This module provides thorough testing for the error_codes.py module,
covering all error codes, exception classes, and utility functions.
"""

import pytest
from typing import Dict, Any

from ai_utilities.error_codes import (
    # Enums and classes
    ErrorCode,
    ErrorInfo,
    AIUtilitiesError,
    ConfigurationError,
    ProviderError,
    CacheError,
    FileError,
    UsageError,
    JsonParseError,
    
    # Functions
    create_error,
    handle_provider_error,
    get_error_severity,
    
    # Mappings and constants
    ERROR_CODE_MAPPING,
    
    # Legacy constants
    ERROR_AI_USAGE_DISABLED,
    ERROR_INVALID_PROMPT,
    ERROR_MEMORY_USAGE_EXCEEDED,
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_LOGGING_CODE,
    ERROR_CONFIG_INITIALIZATION_FAILED,
    ERROR_CONFIG_DEFAULT_SETTING_FAILED,
    ERROR_CONFIG_API_KEY_MISSING,
    ERROR_CONFIG_MODEL_NAME_MISSING,
    ERROR_CONFIG_UNSUPPORTED_PROVIDER
)


class TestErrorCodeEnum:
    """Test the ErrorCode enum."""
    
    def test_error_code_values(self):
        """Test that error codes have correct string values."""
        assert ErrorCode.CONFIG_MISSING_API_KEY.value == "E1001"
        assert ErrorCode.PROVIDER_UNREACHABLE.value == "E2001"
        assert ErrorCode.CACHE_CONNECTION_FAILED.value == "E3001"
        assert ErrorCode.FILE_NOT_FOUND.value == "E4001"
        assert ErrorCode.USAGE_TRACKING_FAILED.value == "E5001"
        assert ErrorCode.JSON_PARSE_FAILED.value == "E6001"
        assert ErrorCode.CAPABILITY_NOT_SUPPORTED.value == "E7001"
        assert ErrorCode.SYSTEM_MEMORY_ERROR.value == "E9001"
        assert ErrorCode.UNKNOWN_ERROR.value == "E9999"
    
    def test_legacy_error_codes(self):
        """Test that legacy error codes are maintained."""
        assert ErrorCode.AI_USAGE_DISABLED.value == "AIU_E001"
        assert ErrorCode.INVALID_PROMPT.value == "AIU_E002"
        assert ErrorCode.CONFIG_API_KEY_MISSING.value == "CFG_E003"
    
    def test_error_code_categories(self):
        """Test that error codes are properly categorized."""
        # Configuration errors (1000-1099)
        config_errors = [
            ErrorCode.CONFIG_MISSING_API_KEY,
            ErrorCode.CONFIG_INVALID_MODEL,
            ErrorCode.CONFIG_VALIDATION_FAILED
        ]
        for error in config_errors:
            assert error.value.startswith("E10")
        
        # Provider errors (2000-2099)
        provider_errors = [
            ErrorCode.PROVIDER_UNREACHABLE,
            ErrorCode.PROVIDER_AUTHENTICATION_FAILED,
            ErrorCode.PROVIDER_SERVER_ERROR
        ]
        for error in provider_errors:
            assert error.value.startswith("E20")
        
        # Cache errors (3000-3099)
        cache_errors = [
            ErrorCode.CACHE_CONNECTION_FAILED,
            ErrorCode.CACHE_WRITE_FAILED,
            ErrorCode.CACHE_CORRUPTION
        ]
        for error in cache_errors:
            assert error.value.startswith("E30")
    
    def test_error_code_uniqueness(self):
        """Test that all error codes have unique values."""
        values = [error.value for error in ErrorCode]
        assert len(values) == len(set(values)), "Error code values must be unique"


class TestErrorInfo:
    """Test the ErrorInfo class."""
    
    def test_error_info_initialization(self):
        """Test ErrorInfo initialization with all parameters."""
        cause = Exception("Original error")
        error_info = ErrorInfo(
            code=ErrorCode.CONFIG_MISSING_API_KEY,
            message="Test message",
            details={"key": "value"},
            cause=cause,
            retry_suggested=True,
            user_action="Check configuration"
        )
        
        assert error_info.code == ErrorCode.CONFIG_MISSING_API_KEY
        assert error_info.message == "Test message"
        assert error_info.details == {"key": "value"}
        assert error_info.cause is cause
        assert error_info.retry_suggested is True
        assert error_info.user_action == "Check configuration"
    
    def test_error_info_defaults(self):
        """Test ErrorInfo initialization with default values."""
        error_info = ErrorInfo(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test message"
        )
        
        assert error_info.code == ErrorCode.UNKNOWN_ERROR
        assert error_info.message == "Test message"
        assert error_info.details == {}
        assert error_info.cause is None
        assert error_info.retry_suggested is False
        assert error_info.user_action is None
    
    def test_error_info_to_dict(self):
        """Test ErrorInfo to_dict conversion."""
        error_info = ErrorInfo(
            code=ErrorCode.PROVIDER_RATE_LIMITED,
            message="Rate limited",
            details={"retry_after": 60},
            retry_suggested=True,
            user_action="Wait and retry"
        )
        
        result = error_info.to_dict()
        expected = {
            "error_code": "E2003",
            "message": "Rate limited",
            "details": {"retry_after": 60},
            "retry_suggested": True,
            "user_action": "Wait and retry"
        }
        assert result == expected


class TestAIUtilitiesError:
    """Test the AIUtilitiesError base exception class."""
    
    def test_basic_initialization(self):
        """Test basic AIUtilitiesError initialization."""
        error = AIUtilitiesError("Test error")
        
        assert str(error) == "[ErrorCode.UNKNOWN_ERROR] Test error"
        assert error.error_info.code == ErrorCode.UNKNOWN_ERROR
        assert error.error_info.message == "Test error"
    
    def test_full_initialization(self):
        """Test AIUtilitiesError with all parameters."""
        cause = Exception("Cause")
        error = AIUtilitiesError(
            message="Full error",
            code=ErrorCode.CONFIG_MISSING_API_KEY,
            details={"config": "test"},
            cause=cause,
            retry_suggested=False,
            user_action="Fix config"
        )
        
        assert str(error) == "[ErrorCode.CONFIG_MISSING_API_KEY] Full error"
        assert error.error_info.code == ErrorCode.CONFIG_MISSING_API_KEY
        assert error.error_info.details == {"config": "test"}
        assert error.error_info.cause is cause
        assert error.error_info.retry_suggested is False
        assert error.error_info.user_action == "Fix config"
    
    def test_to_dict(self):
        """Test AIUtilitiesError to_dict method."""
        error = AIUtilitiesError(
            "Test error",
            code=ErrorCode.PROVIDER_TIMEOUT,
            details={"timeout": 30}
        )
        
        result = error.to_dict()
        expected = {
            "error_code": "E2007",
            "message": "Test error",
            "details": {"timeout": 30},
            "retry_suggested": False,
            "user_action": None
        }
        assert result == expected
    
    def test_inheritance(self):
        """Test that AIUtilitiesError inherits from Exception."""
        error = AIUtilitiesError("Test")
        assert isinstance(error, Exception)


class TestSpecializedExceptions:
    """Test specialized exception classes."""
    
    def test_configuration_error(self):
        """Test ConfigurationError class."""
        error = ConfigurationError(
            "Invalid configuration",
            details={"field": "api_key"},
            retry_suggested=True
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.CONFIG_VALIDATION_FAILED
        assert error.error_info.message == "Invalid configuration"
        assert error.error_info.retry_suggested is True
    
    def test_configuration_error_custom_code(self):
        """Test ConfigurationError with custom error code."""
        error = ConfigurationError(
            "Missing API key",
            code=ErrorCode.CONFIG_MISSING_API_KEY
        )
        
        assert error.error_info.code == ErrorCode.CONFIG_MISSING_API_KEY
    
    def test_provider_error(self):
        """Test ProviderError class."""
        error = ProviderError(
            "Provider failed",
            code=ErrorCode.PROVIDER_RATE_LIMITED,
            retry_suggested=True
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.PROVIDER_RATE_LIMITED
        assert error.error_info.retry_suggested is True
    
    def test_cache_error(self):
        """Test CacheError class."""
        error = CacheError(
            "Cache connection failed",
            details={"host": "localhost"}
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.CACHE_CONNECTION_FAILED
    
    def test_file_error(self):
        """Test FileError class."""
        error = FileError(
            "File not found",
            code=ErrorCode.FILE_TOO_LARGE,
            details={"size": "100MB"}
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.FILE_TOO_LARGE
    
    def test_usage_error(self):
        """Test UsageError class."""
        error = UsageError(
            "Rate limit exceeded",
            retry_suggested=True,
            user_action="Wait before retrying"
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert error.error_info.retry_suggested is True
        assert error.error_info.user_action == "Wait before retrying"
    
    def test_json_parse_error(self):
        """Test JsonParseError class."""
        error = JsonParseError(
            "Invalid JSON",
            details={"line": 5, "column": 10}
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.JSON_PARSE_FAILED


class TestErrorCodeMapping:
    """Test the ERROR_CODE_MAPPING dictionary."""
    
    def test_mapping_completeness(self):
        """Test that key error codes have corresponding exception classes."""
        # Test that all major error codes are mapped
        key_error_codes = [
            "E1001", "E1002", "E1003", "E1004", "E1005", "E1006",  # Config
            "E2001", "E2002", "E2003", "E2004", "E2005", "E2006", "E2007", "E2008", "E2009",  # Provider
            "E3001", "E3002", "E3003", "E3004", "E3005", "E3006",  # Cache
            "E4001", "E4002", "E4003", "E4004", "E4005", "E4006",  # File
            "E5001", "E5002", "E5003", "E5004",  # Usage
            "E6001", "E6002", "E6003", "E6004",  # JSON
        ]
        
        for error_code in key_error_codes:
            assert error_code in ERROR_CODE_MAPPING, f"Error code {error_code} not mapped"
    
    def test_mapping_values(self):
        """Test specific error code mappings."""
        assert ERROR_CODE_MAPPING["E1001"] == ConfigurationError
        assert ERROR_CODE_MAPPING["E2001"] == ProviderError
        assert ERROR_CODE_MAPPING["E3001"] == CacheError
        assert ERROR_CODE_MAPPING["E4001"] == FileError
        assert ERROR_CODE_MAPPING["E5001"] == UsageError
        assert ERROR_CODE_MAPPING["E6001"] == JsonParseError
    
    def test_unknown_error_mapping(self):
        """Test that unknown error codes map to base class."""
        # Test with a non-existent error code
        assert "E9999" not in ERROR_CODE_MAPPING  # Should map to base class


class TestCreateError:
    """Test the create_error function."""
    
    def test_create_configuration_error(self):
        """Test creating a configuration error."""
        error = create_error(
            ErrorCode.CONFIG_MISSING_API_KEY,
            "API key is missing",
            details={"field": "api_key"}
        )
        
        assert isinstance(error, ConfigurationError)
        assert error.error_info.code == ErrorCode.CONFIG_MISSING_API_KEY
        assert error.error_info.message == "API key is missing"
    
    def test_create_provider_error(self):
        """Test creating a provider error."""
        original_error = Exception("Original")
        error = create_error(
            ErrorCode.PROVIDER_RATE_LIMITED,
            "Rate limited",
            cause=original_error
        )
        
        assert isinstance(error, ProviderError)
        assert error.error_info.cause is original_error
    
    def test_create_unknown_error(self):
        """Test creating an unknown error."""
        error = create_error(
            ErrorCode.UNKNOWN_ERROR,
            "Something went wrong"
        )
        
        assert isinstance(error, AIUtilitiesError)
        assert error.error_info.code == ErrorCode.UNKNOWN_ERROR
    
    def test_create_error_with_all_params(self):
        """Test create_error with all parameters."""
        cause = Exception("Cause")
        error = create_error(
            code=ErrorCode.CACHE_WRITE_FAILED,
            message="Cache write failed",
            details={"path": "/tmp/cache"},
            cause=cause
        )
        
        assert isinstance(error, CacheError)
        assert error.error_info.message == "Cache write failed"
        assert error.error_info.details == {"path": "/tmp/cache"}
        assert error.error_info.cause is cause


class TestHandleProviderError:
    """Test the handle_provider_error function."""
    
    def test_authentication_error(self):
        """Test handling authentication errors."""
        original_error = Exception("Authentication failed: 401 Unauthorized")
        error = handle_provider_error(original_error, "test operation")
        
        assert isinstance(error, ProviderError)
        assert error.error_info.code == ErrorCode.PROVIDER_AUTHENTICATION_FAILED
        assert error.error_info.retry_suggested is False
        assert "API key" in error.error_info.user_action
    
    def test_rate_limit_error(self):
        """Test handling rate limit errors."""
        original_error = Exception("Rate limit exceeded: 429")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_RATE_LIMITED
        assert error.error_info.retry_suggested is True
        assert "Wait" in error.error_info.user_action
    
    def test_quota_error(self):
        """Test handling quota errors."""
        original_error = Exception("Insufficient quota")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_QUOTA_EXCEEDED
        assert error.error_info.retry_suggested is False
        assert "quota" in error.error_info.user_action.lower()
    
    def test_model_not_found_error(self):
        """Test handling model not found errors."""
        original_error = Exception("Model gpt-5 not found")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_MODEL_NOT_FOUND
        assert error.error_info.retry_suggested is False
        assert "model name" in error.error_info.user_action.lower()
    
    def test_timeout_error(self):
        """Test handling timeout errors."""
        original_error = Exception("Request timed out")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_TIMEOUT
        assert error.error_info.retry_suggested is True
        assert "timeout" in error.error_info.user_action.lower()
    
    def test_network_error(self):
        """Test handling network errors."""
        original_error = Exception("Connection failed")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_NETWORK_ERROR
        assert error.error_info.retry_suggested is True
        assert "internet" in error.error_info.user_action.lower()
    
    def test_server_error(self):
        """Test handling server errors."""
        original_error = Exception("500 Internal server error")
        error = handle_provider_error(original_error)
        
        assert error.error_info.code == ErrorCode.PROVIDER_SERVER_ERROR
        assert error.error_info.retry_suggested is True
        assert "later" in error.error_info.user_action.lower()
    
    def test_generic_error(self):
        """Test handling generic provider errors."""
        original_error = Exception("Unknown provider error")
        error = handle_provider_error(original_error, "custom operation")
        
        assert error.error_info.code == ErrorCode.PROVIDER_SERVER_ERROR
        assert error.error_info.retry_suggested is True
        assert "custom operation" in error.error_info.message
    
    def test_error_details(self):
        """Test that error details are properly set."""
        original_error = Exception("Rate limit: 429")
        error = handle_provider_error(original_error, "test op")
        
        assert error.error_info.details["original_error"] == "Rate limit: 429"
        assert error.error_info.details["operation"] == "test op"
        assert error.error_info.cause is original_error


class TestGetErrorSeverity:
    """Test the get_error_severity function."""
    
    def test_critical_severity(self):
        """Test critical severity errors."""
        critical_errors = [
            ErrorCode.CONFIG_MISSING_API_KEY,
            ErrorCode.PROVIDER_AUTHENTICATION_FAILED,
            ErrorCode.PROVIDER_QUOTA_EXCEEDED,
            ErrorCode.SYSTEM_PERMISSION_ERROR
        ]
        
        for error_code in critical_errors:
            assert get_error_severity(error_code) == "critical"
    
    def test_high_severity(self):
        """Test high severity errors."""
        high_errors = [
            ErrorCode.PROVIDER_SERVER_ERROR,
            ErrorCode.CACHE_CORRUPTION,
            ErrorCode.SYSTEM_DISK_ERROR,
            ErrorCode.SYSTEM_MEMORY_ERROR
        ]
        
        for error_code in high_errors:
            assert get_error_severity(error_code) == "high"
    
    def test_medium_severity(self):
        """Test medium severity errors."""
        medium_errors = [
            ErrorCode.PROVIDER_RATE_LIMITED,
            ErrorCode.PROVIDER_TIMEOUT,
            ErrorCode.CACHE_CONNECTION_FAILED,
            ErrorCode.FILE_TOO_LARGE
        ]
        
        for error_code in medium_errors:
            assert get_error_severity(error_code) == "medium"
    
    def test_low_severity(self):
        """Test low severity errors."""
        low_errors = [
            ErrorCode.CONFIG_INVALID_MODEL,
            ErrorCode.FILE_INVALID_FORMAT,
            ErrorCode.JSON_INVALID_STRUCTURE,
            ErrorCode.CAPABILITY_NOT_SUPPORTED
        ]
        
        for error_code in low_errors:
            assert get_error_severity(error_code) == "low"


class TestLegacyConstants:
    """Test legacy error message constants."""
    
    def test_legacy_constants_format(self):
        """Test that legacy constants have proper format."""
        assert ERROR_AI_USAGE_DISABLED.startswith("AIU_E001:")
        assert ERROR_INVALID_PROMPT.startswith("AIU_E002:")
        assert ERROR_RATE_LIMIT_EXCEEDED.startswith("AIU_E004:")
        
        assert ERROR_CONFIG_API_KEY_MISSING.startswith("CFG_E003:")
        assert ERROR_CONFIG_MODEL_NAME_MISSING.startswith("CFG_E004:")
    
    def test_legacy_constants_content(self):
        """Test that legacy constants contain expected content."""
        assert "AI usage is disabled" in ERROR_AI_USAGE_DISABLED
        assert "Invalid prompt" in ERROR_INVALID_PROMPT
        assert "Rate limit exceeded" in ERROR_RATE_LIMIT_EXCEEDED
        assert "API key missing" in ERROR_CONFIG_API_KEY_MISSING
        assert "Model name missing" in ERROR_CONFIG_MODEL_NAME_MISSING


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_error_with_none_details(self):
        """Test error with None details."""
        error = AIUtilitiesError(
            "Test error",
            details=None
        )
        assert error.error_info.details == {}
    
    def test_error_with_empty_details(self):
        """Test error with empty details."""
        error = AIUtilitiesError(
            "Test error",
            details={}
        )
        assert error.error_info.details == {}
    
    def test_error_with_complex_details(self):
        """Test error with complex nested details."""
        complex_details = {
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"}
            },
            "simple": "value"
        }
        
        error = AIUtilitiesError(
            "Complex error",
            details=complex_details
        )
        
        assert error.error_info.details == complex_details
        assert error.to_dict()["details"] == complex_details
    
    def test_error_str_representation(self):
        """Test error string representation."""
        error = ConfigurationError(
            "Configuration failed",
            code=ErrorCode.CONFIG_MISSING_API_KEY
        )
        
        assert str(error) == "[ErrorCode.CONFIG_MISSING_API_KEY] Configuration failed"
    
    def test_error_repr(self):
        """Test error repr representation."""
        error = ProviderError("Provider error")
        repr_str = repr(error)
        
        assert "ProviderError" in repr_str
        assert "Provider error" in repr_str
