"""
Demo scenarios for testing AI functionality.

This module previously contained demo scenarios but has been removed as dead code.
The stub remains to maintain compatibility with the demo app system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .validation import ValidatedModel


@dataclass
class SelectedModelContext:
    """Selected model configuration.
    
    Attributes:
        provider: Provider string accepted by `create_client`.
        model: Model identifier.
        base_url: Base URL for OpenAI-compatible endpoints.
        endpoint_label: Human-friendly label.
        required_env_vars_used: Environment variables relevant for this model.
    """
    provider: str
    model: str
    base_url: str | None = None
    endpoint_label: str = ""
    required_env_vars_used: list[str] | None = None


def basic_chat_example(context: SelectedModelContext) -> None:
    """Basic chat example - removed as dead code."""
    print("Basic chat example has been removed.")


def json_response_example(context: SelectedModelContext) -> None:
    """JSON response example - removed as dead code."""
    print("JSON response example has been removed.")


def typed_response_example(context: SelectedModelContext) -> None:
    """Typed response example - removed as dead code."""
    print("Typed response example has been removed.")


def real_world_examples(context: SelectedModelContext) -> None:
    """Real-world examples - removed as dead code."""
    print("Real-world examples have been removed.")


def error_handling_examples(context: SelectedModelContext) -> None:
    """Error handling examples - removed as dead code."""
    print("Error handling examples have been removed.")


def provider_comparison_example(context: SelectedModelContext) -> None:
    """Provider comparison example - removed as dead code."""
    print("Provider comparison example has been removed.")
