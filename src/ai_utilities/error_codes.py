"""
Standardized error codes for AI Utilities.

This module provides comprehensive error codes and structured error handling
for better programmatic error response and monitoring in production environments.

Error Code Categories:
- E1000-E1099: Configuration and Setup Errors
- E2000-E2099: Provider Errors  
- E3000-E3099: Cache Errors
- E4000-E4099: File and Media Errors
- E5000-E5099: Usage and Rate Limiting Errors
- E6000-E6099: JSON Parsing Errors
- E7000-E7099: Provider Capability Errors
- E9000-E9099: System and Infrastructure Errors
- E9999: Generic Unknown Error
"""

# Standard Library Imports
from enum import Enum
from typing import Dict, Any, Optional


class ErrorCode(Enum):
    """Standardized error codes for AI Utilities."""
    
    # Configuration and Setup Errors (1000-1099)
    CONFIG_MISSING_API_KEY = "E1001"
    CONFIG_INVALID_MODEL = "E1002"
    CONFIG_INVALID_TIMEOUT = "E1003"
    CONFIG_INVALID_TEMPERATURE = "E1004"
    CONFIG_MISSING_REQUIRED_FIELD = "E1005"
    CONFIG_VALIDATION_FAILED = "E1006"
    
    # Legacy error codes (maintained for backwards compatibility)
    AI_USAGE_DISABLED = "AIU_E001"
    INVALID_PROMPT = "AIU_E002"
    MEMORY_USAGE_EXCEEDED = "AIU_E003"
    RATE_LIMIT_EXCEEDED_OLD = "AIU_E004"
    ERROR_LOGGING_CODE = "AIU_E005"
    CONFIG_INITIALIZATION_FAILED = "CFG_E001"
    CONFIG_DEFAULT_SETTING_FAILED = "CFG_E002"
    CONFIG_API_KEY_MISSING = "CFG_E003"
    CONFIG_MODEL_NAME_MISSING = "CFG_E004"
    CONFIG_UNSUPPORTED_PROVIDER = "CFG_E005"
    
    # Provider Errors (2000-2099)
    PROVIDER_UNREACHABLE = "E2001"
    PROVIDER_AUTHENTICATION_FAILED = "E2002"
    PROVIDER_RATE_LIMITED = "E2003"
    PROVIDER_QUOTA_EXCEEDED = "E2004"
    PROVIDER_MODEL_NOT_FOUND = "E2005"
    PROVIDER_INVALID_REQUEST = "E2006"
    PROVIDER_TIMEOUT = "E2007"
    PROVIDER_SERVER_ERROR = "E2008"
    PROVIDER_NETWORK_ERROR = "E2009"
    
    # Cache Errors (3000-3099)
    CACHE_CONNECTION_FAILED = "E3001"
    CACHE_WRITE_FAILED = "E3002"
    CACHE_READ_FAILED = "E3003"
    CACHE_CORRUPTION = "E3004"
    CACHE_PERMISSION_DENIED = "E3005"
    CACHE_DISK_FULL = "E3006"
    
    # File and Media Errors (4000-4099)
    FILE_NOT_FOUND = "E4001"
    FILE_TOO_LARGE = "E4002"
    FILE_INVALID_FORMAT = "E4003"
    FILE_UPLOAD_FAILED = "E4004"
    FILE_PROCESSING_FAILED = "E4005"
    AUDIO_CONVERSION_FAILED = "E4006"
    
    # Usage and Rate Limiting Errors (5000-5099)
    USAGE_TRACKING_FAILED = "E5001"
    RATE_LIMIT_EXCEEDED = "E5002"
    QUOTA_EXCEEDED = "E5003"
    BILLING_ISSUE = "E5004"
    
    # JSON Parsing Errors (6000-6099)
    JSON_PARSE_FAILED = "E6001"
    JSON_INVALID_STRUCTURE = "E6002"
    JSON_TOO_LARGE = "E6003"
    JSON_REPAIR_FAILED = "E6004"
    
    # Provider Capability Errors (7000-7099)
    CAPABILITY_NOT_SUPPORTED = "E7001"
    FEATURE_NOT_AVAILABLE = "E7002"
    MODEL_CAPABILITY_MISMATCH = "E7003"
    
    # System and Infrastructure Errors (9000-9099)
    SYSTEM_MEMORY_ERROR = "E9001"
    SYSTEM_DISK_ERROR = "E9002"
    SYSTEM_PERMISSION_ERROR = "E9003"
    SYSTEM_CONFIGURATION_ERROR = "E9004"
    
    # Generic Errors (9999)
    UNKNOWN_ERROR = "E9999"


class ErrorInfo:
    """Structured error information for better error handling."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        retry_suggested: bool = False,
        user_action: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.cause = cause
        self.retry_suggested = retry_suggested
        self.user_action = user_action
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "retry_suggested": self.retry_suggested,
            "user_action": self.user_action
        }


class AIUtilitiesError(Exception):
    """Base exception class for AI Utilities with error codes."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        retry_suggested: bool = False,
        user_action: Optional[str] = None
    ):
        super().__init__(message)
        self.error_info = ErrorInfo(
            code=code,
            message=message,
            details=details,
            cause=cause,
            retry_suggested=retry_suggested,
            user_action=user_action
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return self.error_info.to_dict()
    
    def __str__(self) -> str:
        return f"[{self.error_info.code.value}] {self.error_info.message}"


# Specialized exception classes
class ConfigurationError(AIUtilitiesError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.CONFIG_VALIDATION_FAILED, **kwargs):
        super().__init__(message, code=code, **kwargs)


class ProviderError(AIUtilitiesError):
    """Provider-related errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.PROVIDER_SERVER_ERROR, **kwargs):
        super().__init__(message, code=code, **kwargs)


class CacheError(AIUtilitiesError):
    """Cache-related errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.CACHE_CONNECTION_FAILED, **kwargs):
        super().__init__(message, code=code, **kwargs)


class FileError(AIUtilitiesError):
    """File and media-related errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.FILE_NOT_FOUND, **kwargs):
        super().__init__(message, code=code, **kwargs)


class UsageError(AIUtilitiesError):
    """Usage and rate limiting errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED, **kwargs):
        super().__init__(message, code=code, **kwargs)


class JsonParseError(AIUtilitiesError):
    """JSON parsing errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.JSON_PARSE_FAILED, **kwargs):
        super().__init__(message, code=code, **kwargs)


# Error code mapping for quick lookup
ERROR_CODE_MAPPING: Dict[str, type] = {
    # Configuration errors
    ErrorCode.CONFIG_MISSING_API_KEY.value: ConfigurationError,
    ErrorCode.CONFIG_INVALID_MODEL.value: ConfigurationError,
    ErrorCode.CONFIG_INVALID_TIMEOUT.value: ConfigurationError,
    ErrorCode.CONFIG_INVALID_TEMPERATURE.value: ConfigurationError,
    ErrorCode.CONFIG_MISSING_REQUIRED_FIELD.value: ConfigurationError,
    ErrorCode.CONFIG_VALIDATION_FAILED.value: ConfigurationError,
    
    ErrorCode.CONFIG_API_KEY_MISSING.value: ConfigurationError,
    ErrorCode.CONFIG_MODEL_NAME_MISSING.value: ConfigurationError,
    ErrorCode.CONFIG_INITIALIZATION_FAILED.value: ConfigurationError,
    
    # Provider errors
    ErrorCode.PROVIDER_UNREACHABLE.value: ProviderError,
    ErrorCode.PROVIDER_AUTHENTICATION_FAILED.value: ProviderError,
    ErrorCode.PROVIDER_RATE_LIMITED.value: ProviderError,
    ErrorCode.PROVIDER_QUOTA_EXCEEDED.value: ProviderError,
    ErrorCode.PROVIDER_MODEL_NOT_FOUND.value: ProviderError,
    ErrorCode.PROVIDER_INVALID_REQUEST.value: ProviderError,
    ErrorCode.PROVIDER_TIMEOUT.value: ProviderError,
    ErrorCode.PROVIDER_SERVER_ERROR.value: ProviderError,
    ErrorCode.PROVIDER_NETWORK_ERROR.value: ProviderError,
    
    # Cache errors
    ErrorCode.CACHE_CONNECTION_FAILED.value: CacheError,
    ErrorCode.CACHE_WRITE_FAILED.value: CacheError,
    ErrorCode.CACHE_READ_FAILED.value: CacheError,
    ErrorCode.CACHE_CORRUPTION.value: CacheError,
    ErrorCode.CACHE_PERMISSION_DENIED.value: CacheError,
    ErrorCode.CACHE_DISK_FULL.value: CacheError,
    
    # File errors
    ErrorCode.FILE_NOT_FOUND.value: FileError,
    ErrorCode.FILE_TOO_LARGE.value: FileError,
    ErrorCode.FILE_INVALID_FORMAT.value: FileError,
    ErrorCode.FILE_UPLOAD_FAILED.value: FileError,
    ErrorCode.FILE_PROCESSING_FAILED.value: FileError,
    ErrorCode.AUDIO_CONVERSION_FAILED.value: FileError,
    
    # Usage errors
    ErrorCode.USAGE_TRACKING_FAILED.value: UsageError,
    ErrorCode.RATE_LIMIT_EXCEEDED.value: UsageError,
    ErrorCode.QUOTA_EXCEEDED.value: UsageError,
    ErrorCode.BILLING_ISSUE.value: UsageError,
    
    # JSON errors
    ErrorCode.JSON_PARSE_FAILED.value: JsonParseError,
    ErrorCode.JSON_INVALID_STRUCTURE.value: JsonParseError,
    ErrorCode.JSON_TOO_LARGE.value: JsonParseError,
    ErrorCode.JSON_REPAIR_FAILED.value: JsonParseError,
}


def create_error(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    cause: Optional[Exception] = None
) -> AIUtilitiesError:
    """Create an appropriate error instance from error code."""
    error_class = ERROR_CODE_MAPPING.get(code.value, AIUtilitiesError)
    return error_class(
        message=message,
        code=code,
        details=details,
        cause=cause
    )


def handle_provider_error(
    provider_error: Exception,
    operation: str = "AI request"
) -> ProviderError:
    """Convert provider-specific errors to standardized ProviderError."""
    error_message = str(provider_error).lower()
    
    # Determine error code based on message content
    if "authentication" in error_message or "unauthorized" in error_message or "401" in error_message:
        code = ErrorCode.PROVIDER_AUTHENTICATION_FAILED
        user_action = "Check your API key and permissions"
        retry_suggested = False
    elif "rate limit" in error_message or "429" in error_message:
        code = ErrorCode.PROVIDER_RATE_LIMITED
        user_action = "Wait before making another request"
        retry_suggested = True
    elif "quota" in error_message or "insufficient" in error_message:
        code = ErrorCode.PROVIDER_QUOTA_EXCEEDED
        user_action = "Check your account quota and billing"
        retry_suggested = False
    elif "model" in error_message and "not found" in error_message:
        code = ErrorCode.PROVIDER_MODEL_NOT_FOUND
        user_action = "Check if the model name is correct and available"
        retry_suggested = False
    elif "timeout" in error_message or "timed out" in error_message:
        code = ErrorCode.PROVIDER_TIMEOUT
        user_action = "Try again with a longer timeout or shorter prompt"
        retry_suggested = True
    elif "connection" in error_message or "network" in error_message:
        code = ErrorCode.PROVIDER_NETWORK_ERROR
        user_action = "Check your internet connection"
        retry_suggested = True
    elif "server error" in error_message or "500" in error_message or "502" in error_message:
        code = ErrorCode.PROVIDER_SERVER_ERROR
        user_action = "Try again later or contact support"
        retry_suggested = True
    else:
        code = ErrorCode.PROVIDER_SERVER_ERROR
        user_action = "Check the error details and try again"
        retry_suggested = True
    
    return ProviderError(
        message=f"Provider error during {operation}: {str(provider_error)}",
        code=code,
        details={"original_error": str(provider_error), "operation": operation},
        cause=provider_error,
        retry_suggested=retry_suggested,
        user_action=user_action
    )


def get_error_severity(code: ErrorCode) -> str:
    """Get error severity level for monitoring and alerting."""
    if code in [
        ErrorCode.CONFIG_MISSING_API_KEY,
        ErrorCode.PROVIDER_AUTHENTICATION_FAILED,
        ErrorCode.PROVIDER_QUOTA_EXCEEDED,
        ErrorCode.SYSTEM_PERMISSION_ERROR
    ]:
        return "critical"
    elif code in [
        ErrorCode.PROVIDER_SERVER_ERROR,
        ErrorCode.CACHE_CORRUPTION,
        ErrorCode.SYSTEM_DISK_ERROR,
        ErrorCode.SYSTEM_MEMORY_ERROR
    ]:
        return "high"
    elif code in [
        ErrorCode.PROVIDER_RATE_LIMITED,
        ErrorCode.PROVIDER_TIMEOUT,
        ErrorCode.CACHE_CONNECTION_FAILED,
        ErrorCode.FILE_TOO_LARGE
    ]:
        return "medium"
    else:
        return "low"


# Legacy error message constants (maintained for backwards compatibility)
ERROR_AI_USAGE_DISABLED = f"{ErrorCode.AI_USAGE_DISABLED.value}: AI usage is disabled."
ERROR_INVALID_PROMPT = f"{ErrorCode.INVALID_PROMPT.value}: Invalid prompt provided."
ERROR_MEMORY_USAGE_EXCEEDED = f"{ErrorCode.MEMORY_USAGE_EXCEEDED.value}: Memory usage exceeded."
ERROR_RATE_LIMIT_EXCEEDED = f"{ErrorCode.RATE_LIMIT_EXCEEDED_OLD.value}: Rate limit exceeded."
ERROR_LOGGING_CODE = f"{ErrorCode.ERROR_LOGGING_CODE.value}: An error occurred during logging operations."

# Configuration error messages (legacy)
ERROR_CONFIG_INITIALIZATION_FAILED = f"{ErrorCode.CONFIG_INITIALIZATION_FAILED.value}: Configuration initialization failed."
ERROR_CONFIG_DEFAULT_SETTING_FAILED = f"{ErrorCode.CONFIG_DEFAULT_SETTING_FAILED.value}: Failed to set default configuration values."
ERROR_CONFIG_API_KEY_MISSING = f"{ErrorCode.CONFIG_API_KEY_MISSING.value}: API key missing in environment variables."
ERROR_CONFIG_MODEL_NAME_MISSING = f"{ErrorCode.CONFIG_MODEL_NAME_MISSING.value}: Model name missing in configuration."
ERROR_CONFIG_UNSUPPORTED_PROVIDER = f"{ErrorCode.CONFIG_UNSUPPORTED_PROVIDER.value}: Unsupported AI provider specified in configuration."
