"""
Knowledge module exceptions.

All knowledge-related exceptions inherit from a common base exception
for proper error handling and type checking.
"""

from __future__ import annotations

from typing import Any


class KnowledgeError(Exception):
    """Base exception for all knowledge module errors."""
    pass


class KnowledgeDisabledError(KnowledgeError):
    """Raised when knowledge functionality is disabled in settings."""
    
    def __init__(self, message: str = "Knowledge functionality is disabled") -> None:
        super().__init__(message)


class SqliteExtensionUnavailableError(KnowledgeError):
    """Raised when required SQLite vector extensions are not available."""
    
    def __init__(self, extension_name: str, message: str | None = None) -> None:
        if message is None:
            message = f"SQLite extension '{extension_name}' is not available"
        super().__init__(message)
        self.extension_name = extension_name


class KnowledgeIndexError(KnowledgeError):
    """Raised when knowledge indexing operations fail."""
    
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class KnowledgeSearchError(KnowledgeError):
    """Raised when knowledge search operations fail."""
    
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class KnowledgeValidationError(KnowledgeError):
    """Raised when knowledge data validation fails."""
    
    def __init__(self, message: str, field: str | None = None, value: Any = None) -> None:
        super().__init__(message)
        self.field = field
        self.value = value
