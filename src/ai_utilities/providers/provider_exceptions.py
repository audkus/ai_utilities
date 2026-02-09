"""Provider-specific exceptions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfigurationError(Exception):
    """Raised when provider configuration is invalid."""
    message: str
    provider: str

    def __str__(self) -> str:
        return f"Provider '{self.provider}' configuration error: {self.message}"


@dataclass
class ProviderCapabilityError(Exception):
    """Raised when a requested capability is not supported by the provider."""
    capability: str
    provider: Optional[str] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.message is None:
            self.message = self.capability  # keep default simple for tests

    def __str__(self) -> str:
        return str(self.message)


@dataclass
class MissingOptionalDependencyError(Exception):
    """Raised when an optional dependency is required but not installed."""
    dependency: str

    @property
    def message(self) -> str:
        return self.dependency

    def __str__(self) -> str:
        return self.dependency


@dataclass
class FileTransferError(Exception):
    """Raised when file upload/download operations fail."""
    operation: str
    provider: str
    inner_error: Optional[BaseException] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.message is None:
            self.message = self.operation

    def __str__(self) -> str:
        base_msg = f"{self.operation} failed for provider '{self.provider}'"
        if self.inner_error:
            # Include the original error message for better debugging
            return f"{base_msg}: {str(self.inner_error)}"
        return base_msg
