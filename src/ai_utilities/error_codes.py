"""
This module defines error codes used throughout the AI integration module.

Each error code corresponds to a specific error condition and is used when raising exceptions.

Constants:
    ERROR_AI_USAGE_DISABLED
    ERROR_INVALID_PROMPT
    ERROR_MEMORY_USAGE_EXCEEDED
    ERROR_RATE_LIMIT_EXCEEDED
    ERROR_LOGGING_CODE
    ERROR_CONFIG_INITIALIZATION_FAILED
    ERROR_CONFIG_DEFAULT_SETTING_FAILED
    ERROR_CONFIG_API_KEY_MISSING
    ERROR_CONFIG_MODEL_NAME_MISSING
    ERROR_CONFIG_UNSUPPORTED_PROVIDER
"""

# Standard Library Imports
from enum import Enum


class ErrorCode(Enum):
    """Enumeration of error codes for the AI integration module."""
    AI_USAGE_DISABLED = "AIU_E001"
    INVALID_PROMPT = "AIU_E002"
    MEMORY_USAGE_EXCEEDED = "AIU_E003"
    RATE_LIMIT_EXCEEDED = "AIU_E004"
    ERROR_LOGGING_CODE = "AIU_E005"
    # Configuration Error Codes
    CONFIG_INITIALIZATION_FAILED = "CFG_E001"
    CONFIG_DEFAULT_SETTING_FAILED = "CFG_E002"
    CONFIG_API_KEY_MISSING = "CFG_E003"
    CONFIG_MODEL_NAME_MISSING = "CFG_E004"
    CONFIG_UNSUPPORTED_PROVIDER = "CFG_E005"


# Error messages associated with the error codes
ERROR_AI_USAGE_DISABLED = f"{ErrorCode.AI_USAGE_DISABLED.value}: AI usage is disabled."
ERROR_INVALID_PROMPT = f"{ErrorCode.INVALID_PROMPT.value}: Invalid prompt provided."
ERROR_MEMORY_USAGE_EXCEEDED = f"{ErrorCode.MEMORY_USAGE_EXCEEDED.value}: Memory usage exceeded."
ERROR_RATE_LIMIT_EXCEEDED = f"{ErrorCode.RATE_LIMIT_EXCEEDED.value}: Rate limit exceeded."
ERROR_LOGGING_CODE = f"{ErrorCode.ERROR_LOGGING_CODE.value}: An error occurred during logging operations."

# Configuration error messages
ERROR_CONFIG_INITIALIZATION_FAILED = f"{ErrorCode.CONFIG_INITIALIZATION_FAILED.value}: Configuration initialization failed."
ERROR_CONFIG_DEFAULT_SETTING_FAILED = f"{ErrorCode.CONFIG_DEFAULT_SETTING_FAILED.value}: Failed to set default configuration values."
ERROR_CONFIG_API_KEY_MISSING = f"{ErrorCode.CONFIG_API_KEY_MISSING.value}: API key missing in environment variables."
ERROR_CONFIG_MODEL_NAME_MISSING = f"{ErrorCode.CONFIG_MODEL_NAME_MISSING.value}: Model name missing in configuration."
ERROR_CONFIG_UNSUPPORTED_PROVIDER = f"{ErrorCode.CONFIG_UNSUPPORTED_PROVIDER.value}: Unsupported AI provider specified in configuration."
