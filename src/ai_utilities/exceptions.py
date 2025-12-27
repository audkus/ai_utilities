"""
This module defines custom exception classes for the AI integration module.

Each exception class corresponds to a specific error condition and includes an error code
from the error_codes module.

Classes:
    AIUsageDisabledError
    InvalidPromptError
    MemoryUsageExceededError
    RateLimitExceededError
    LoggingError
    ConfigError

Example:
    try:
        # Some code that may raise an exception
    except InvalidPromptError as e:
        logging.error(f"An error occurred: {e}")
"""

# Standard Library Imports
import logging

# Local application Imports
from .error_codes import (
    ERROR_AI_USAGE_DISABLED,
    ERROR_INVALID_PROMPT,
    ERROR_LOGGING_CODE,
    ERROR_MEMORY_USAGE_EXCEEDED,
    ERROR_RATE_LIMIT_EXCEEDED,
)


class AIUsageDisabledError(Exception):
    """Exception raised when AI usage is disabled in the configuration."""
    def __init__(self, message: str = ERROR_AI_USAGE_DISABLED) -> None:
        super().__init__(message)
        logging.error(f"AIUsageDisabledError: {message}")


class InvalidPromptError(Exception):
    """Exception raised when the provided prompt is invalid."""
    def __init__(self, message: str = ERROR_INVALID_PROMPT) -> None:
        super().__init__(message)
        logging.error(f"InvalidPromptError: {message}")


class MemoryUsageExceededError(Exception):
    """Exception raised when memory usage exceeds the specified threshold."""
    def __init__(self, message: str = ERROR_MEMORY_USAGE_EXCEEDED) -> None:
        super().__init__(message)
        logging.error(f"MemoryUsageExceededError: {message}")


class RateLimitExceededError(Exception):
    """Exception raised when the rate limit is exceeded."""
    def __init__(self, message: str = ERROR_RATE_LIMIT_EXCEEDED) -> None:
        super().__init__(message)
        logging.error(f"RateLimitExceededError: {message}")


class LoggingError(Exception):
    """Exception raised for errors that occur during logging operations."""
    def __init__(self, message: str = ERROR_LOGGING_CODE) -> None:
        super().__init__(message)
        logging.error(f"LoggingError: {message}")


class ConfigError(Exception):
    """Exception raised for errors related to configuration setup or retrieval.

    Attributes:
        message (str): Description of the configuration error encountered.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        logging.error(f"ConfigError: {message}")
