"""Contract-first testing helper assertions.

These helpers provide convenient assertions for contract-first testing
while avoiding coupling to AI output semantics.
"""

from typing import Any, Mapping

import pytest


def assert_dict_has_response_fallback(value: Any) -> None:
    """Assert value is a Mapping and contains key 'response'.
    
    Args:
        value: Value to check for response fallback structure.
        
    Raises:
        AssertionError: If value is not a Mapping or lacks 'response' key.
    """
    if not isinstance(value, Mapping):
        pytest.fail(f"Expected Mapping, got {type(value).__name__}")
    
    if "response" not in value:
        pytest.fail("Mapping missing required 'response' key")


def assert_provider_called_with_model(mock_provider: Any, model: str) -> None:
    """Assert mock_provider.ask was called with specified model.
    
    Args:
        mock_provider: Mocked provider object.
        model: Expected model string in call kwargs.
        
    Raises:
        AssertionError: If provider was not called or model mismatch.
    """
    if not hasattr(mock_provider, "ask") or not mock_provider.ask.called:
        pytest.fail("Provider.ask was not called")
    
    call_args = mock_provider.ask.call_args
    if not call_args.kwargs or "model" not in call_args.kwargs:
        pytest.fail("Provider.ask called without model parameter")
    
    actual_model = call_args.kwargs["model"]
    if actual_model != model:
        pytest.fail(f"Expected model '{model}', got '{actual_model}'")
