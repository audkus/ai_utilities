"""Comprehensive tests for models.py module.

This module tests the AskResult model and ensures all code paths are exercised.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
import pytest

# Force import to ensure coverage can track the module
import ai_utilities.models
from ai_utilities.models import AskResult


class TestAskResult:
    """Test AskResult model comprehensively."""

    def test_minimal_creation(self) -> None:
        """Test creating AskResult with minimal required fields."""
        result = AskResult(
            prompt="test prompt",
            response="test response",
            error=None,
            duration_s=1.5
        )
        
        assert result.prompt == "test prompt"
        assert result.response == "test response"
        assert result.error is None
        assert result.duration_s == 1.5
        assert result.tokens_used is None
        assert result.model is None

    def test_full_creation(self) -> None:
        """Test creating AskResult with all fields."""
        result = AskResult(
            prompt="full prompt",
            response={"content": "test", "type": "json"},
            error=None,
            duration_s=2.5,
            tokens_used=150,
            model="gpt-4"
        )
        
        assert result.prompt == "full prompt"
        assert result.response == {"content": "test", "type": "json"}
        assert result.error is None
        assert result.duration_s == 2.5
        assert result.tokens_used == 150
        assert result.model == "gpt-4"

    def test_with_error(self) -> None:
        """Test creating AskResult with error."""
        result = AskResult(
            prompt="error prompt",
            response=None,
            error="API timeout",
            duration_s=30.0
        )
        
        assert result.prompt == "error prompt"
        assert result.response is None
        assert result.error == "API timeout"
        assert result.duration_s == 30.0

    @pytest.mark.parametrize("response", [
        "string response",
        {"key": "value", "nested": {"data": "test"}},
        None,  # None response
    ])
    def test_different_response_types(self, response: Optional[Union[str, Dict[str, Any]]]) -> None:
        """Test AskResult with different response types."""
        result = AskResult(
            prompt="test",
            response=response,
            error=None,
            duration_s=1.0
        )
        
        assert result.response == response

    @pytest.mark.parametrize("duration_s", [
        0.0,  # Zero duration
        0.001,  # Very short duration
        999.999,  # Long duration
        1.5,  # Normal duration
    ])
    def test_different_durations(self, duration_s: float) -> None:
        """Test AskResult with different duration values."""
        result = AskResult(
            prompt="test",
            response="response",
            error=None,
            duration_s=duration_s
        )
        
        assert result.duration_s == duration_s

    @pytest.mark.parametrize("tokens_used", [
        0,  # No tokens
        1,  # Single token
        1000,  # Normal token count
        100000,  # Large token count
    ])
    def test_different_token_counts(self, tokens_used: int) -> None:
        """Test AskResult with different token counts."""
        result = AskResult(
            prompt="test",
            response="response",
            error=None,
            duration_s=1.0,
            tokens_used=tokens_used
        )
        
        assert result.tokens_used == tokens_used

    @pytest.mark.parametrize("model", [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3",
        "local-model",
        "",  # Empty model name
        None,  # No model
    ])
    def test_different_models(self, model: Optional[str]) -> None:
        """Test AskResult with different model values."""
        result = AskResult(
            prompt="test",
            response="response",
            error=None,
            duration_s=1.0,
            model=model
        )
        
        assert result.model == model

    def test_model_dict_conversion(self) -> None:
        """Test AskResult can be converted to dict."""
        result = AskResult(
            prompt="dict test",
            response={"data": "test"},
            error=None,
            duration_s=1.5,
            tokens_used=100,
            model="test-model"
        )
        
        result_dict = result.model_dump()
        
        assert isinstance(result_dict, dict)
        assert result_dict["prompt"] == "dict test"
        assert result_dict["response"] == {"data": "test"}
        assert result_dict["error"] is None
        assert result_dict["duration_s"] == 1.5
        assert result_dict["tokens_used"] == 100
        assert result_dict["model"] == "test-model"

    def test_model_json_serialization(self) -> None:
        """Test AskResult can be serialized to JSON."""
        result = AskResult(
            prompt="json test",
            response="json response",
            error=None,
            duration_s=2.0
        )
        
        json_str = result.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "json test" in json_str
        assert "json response" in json_str
        assert "2.0" in json_str

    def test_round_trip_serialization(self) -> None:
        """Test AskResult round-trip serialization."""
        original = AskResult(
            prompt="round trip",
            response={"complex": {"data": [1, 2, 3]}},
            error=None,
            duration_s=1.234,
            tokens_used=567,
            model="round-trip-model"
        )
        
        # Convert to dict and back
        dict_data = original.model_dump()
        restored = AskResult(**dict_data)
        
        assert restored.prompt == original.prompt
        assert restored.response == original.response
        assert restored.error == original.error
        assert restored.duration_s == original.duration_s
        assert restored.tokens_used == original.tokens_used
        assert restored.model == original.model

    def test_equality(self) -> None:
        """Test AskResult equality comparison."""
        result1 = AskResult(
            prompt="test",
            response="response",
            error=None,
            duration_s=1.0
        )
        result2 = AskResult(
            prompt="test",
            response="response",
            error=None,
            duration_s=1.0
        )
        result3 = AskResult(
            prompt="different",
            response="response",
            error=None,
            duration_s=1.0
        )
        
        # Pydantic models support equality
        assert result1 == result2
        assert result1 != result3

    def test_string_representation(self) -> None:
        """Test AskResult string representation."""
        result = AskResult(
            prompt="string test",
            response="response",
            error=None,
            duration_s=1.5
        )
        
        str_repr = str(result)
        assert "prompt" in str_repr
        assert "string test" in str_repr

    def test_repr(self) -> None:
        """Test AskResult repr."""
        result = AskResult(
            prompt="repr test",
            response="response",
            error=None,
            duration_s=1.5
        )
        
        repr_str = repr(result)
        assert isinstance(repr_str, str)
        assert "AskResult" in repr_str
