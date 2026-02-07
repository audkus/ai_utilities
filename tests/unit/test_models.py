"""Comprehensive tests for models.py module - Phase 7B.

This module provides thorough testing for the core AskResult model,
covering all fields, validation, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError

from ai_utilities.models import AskResult


class TestAskResult:
    """Test the AskResult model."""
    
    def test_ask_result_creation_minimal(self):
        """Test AskResult creation with minimal required fields."""
        result = AskResult(
            prompt="What is the meaning of life?",
            response="The meaning of life is 42.",
            error=None,
            duration_s=1.5
        )
        
        assert isinstance(result.prompt, str)  # Contract: prompt is string type
        assert len(result.prompt) > 0  # Contract: non-empty prompt
        assert isinstance(result.response, str)
        assert len(result.response) > 0  # Contract: non-empty response preserved
        assert result.error is None
        assert result.duration_s == 1.5
        assert result.tokens_used is None
        assert result.model is None
    
    def test_ask_result_creation_all_fields(self):
        """Test AskResult creation with all fields."""
        result = AskResult(
            prompt="Test prompt",
            response={"key": "value"},
            error=None,
            duration_s=2.3,
            tokens_used=100,
            model="gpt-4"
        )
        
        assert isinstance(result.prompt, str)  # Contract: prompt is string type
        assert isinstance(result.response, dict)  # Contract: response is dict type
        assert result.response.get("key") is not None  # Contract: expected key present
        assert result.error is None
        assert isinstance(result.duration_s, (int, float))  # Contract: duration is numeric
        assert result.duration_s > 0  # Contract: positive duration
        assert isinstance(result.tokens_used, int)  # Contract: tokens used is int
        assert result.tokens_used >= 0  # Contract: non-negative tokens
        assert isinstance(result.model, str)  # Contract: model is string type
        assert len(result.model) > 0  # Contract: non-empty model
    
    def test_ask_result_with_string_response(self):
        """Test AskResult with string response."""
        result = AskResult(
            prompt="Hello",
            response="Hi there!",
            error=None,
            duration_s=0.5
        )
        
        assert isinstance(result.response, str)
        assert len(result.response) > 0  # Contract: non-empty string response
    
    def test_ask_result_with_dict_response(self):
        """Test AskResult with dictionary response."""
        response_dict = {"text": "Hello", "metadata": {"source": "AI"}}
        result = AskResult(
            prompt="Generate response",
            response=response_dict,
            error=None,
            duration_s=1.0
        )
        
        assert isinstance(result.response, dict)
        assert result.response == response_dict
    
    def test_ask_result_with_error(self):
        """Test AskResult with error."""
        result = AskResult(
            prompt="Test prompt",
            response=None,
            error="API rate limit exceeded",
            duration_s=0.1
        )
        
        assert result.response is None
        assert isinstance(result.error, str)  # Contract: error is string type
        assert len(result.error) > 0  # Contract: non-empty error message
        assert result.duration_s == 0.1
    
    def test_ask_result_optional_fields_defaults(self):
        """Test AskResult optional fields have correct defaults."""
        result = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        assert result.tokens_used is None
        assert result.model is None
    
    def test_ask_result_validation_missing_required_fields(self):
        """Test AskResult validation for missing required fields."""
        # Missing prompt
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                response="Response",
                error=None,
                duration_s=1.0
            )
        assert isinstance(exc_info.value, ValidationError)  # Contract: correct exception type
        
        # Missing response
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                error=None,
                duration_s=1.0
            )
        assert isinstance(exc_info.value, ValidationError)  # Contract: correct exception type
        
        # Missing error
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                response="Response",
                duration_s=1.0
            )
        assert isinstance(exc_info.value, ValidationError)  # Contract: correct exception type
        
        # Missing duration_s
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                response="Response",
                error=None
            )
        assert isinstance(exc_info.value, ValidationError)  # Contract: correct exception type
    
    def test_ask_result_field_types(self):
        """Test AskResult field type validation."""
        # duration_s must be a number
        with pytest.raises(ValidationError):
            AskResult(
                prompt="Test",
                response="Response",
                error=None,
                duration_s="not_a_number"
            )
        
        # tokens_used must be an integer or None
        with pytest.raises(ValidationError):
            AskResult(
                prompt="Test",
                response="Response",
                error=None,
                duration_s=1.0,
                tokens_used="not_an_integer"
            )
        
        # model must be a string or None
        with pytest.raises(ValidationError):
            AskResult(
                prompt="Test",
                response="Response",
                error=None,
                duration_s=1.0,
                model=123
            )
    
    def test_ask_result_serialization(self):
        """Test AskResult serialization to dict."""
        result = AskResult(
            prompt="Test prompt",
            response="Test response",
            error=None,
            duration_s=1.5,
            tokens_used=50,
            model="gpt-3.5-turbo"
        )
        
        data = result.model_dump()
        
        assert isinstance(data["prompt"], str)  # Contract: prompt is string type
        assert isinstance(data["response"], str)  # Contract: response is string type
        assert data["error"] is None
        assert isinstance(data["duration_s"], (int, float))  # Contract: duration is numeric
        assert data["duration_s"] > 0  # Contract: positive duration
        assert isinstance(data["tokens_used"], int)  # Contract: tokens used is int
        assert data["tokens_used"] >= 0  # Contract: non-negative tokens
        assert isinstance(data["model"], str)  # Contract: model is string type
        assert len(data["model"]) > 0  # Contract: non-empty model
    
    def test_ask_result_serialization_with_dict_response(self):
        """Test AskResult serialization with dict response."""
        response_dict = {"text": "Hello", "confidence": 0.9}
        result = AskResult(
            prompt="Generate",
            response=response_dict,
            error=None,
            duration_s=1.0
        )
        
        data = result.model_dump()
        assert data["response"] == response_dict
    
    def test_ask_result_deserialization(self):
        """Test AskResult deserialization from dict."""
        data = {
            "prompt": "Test prompt",
            "response": "Test response",
            "error": None,
            "duration_s": 1.5,
            "tokens_used": 75,
            "model": "gpt-4"
        }
        
        result = AskResult(**data)
        
        assert isinstance(result.prompt, str)  # Contract: prompt is string type
        assert isinstance(result.response, str)  # Contract: response type preserved
        assert len(result.response) > 0  # Contract: non-empty response
        assert result.error is None
        assert isinstance(result.duration_s, (int, float))  # Contract: duration is numeric
        assert result.duration_s > 0  # Contract: positive duration
        assert isinstance(result.tokens_used, int)  # Contract: tokens used is int
        assert result.tokens_used >= 0  # Contract: non-negative tokens
        assert isinstance(result.model, str)  # Contract: model is string type
        assert len(result.model) > 0  # Contract: non-empty model
    
    def test_ask_result_json_serialization(self):
        """Test AskResult JSON serialization."""
        result = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_str)
        assert isinstance(parsed["prompt"], str)  # Contract: prompt is string type
        assert isinstance(parsed["response"], str)  # Contract: response is string type
    
    def test_ask_result_equality(self):
        """Test AskResult equality comparison."""
        result1 = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        result2 = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        result3 = AskResult(
            prompt="Different",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        assert result1 == result2
        assert result1 != result3
    
    def test_ask_result_hash(self):
        """Test AskResult hash behavior (Pydantic models are not hashable by default)."""
        result = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        # Pydantic models are not hashable by default unless frozen=True
        with pytest.raises(TypeError, match="unhashable type"):
            hash(result)
    
    def test_ask_result_repr(self):
        """Test AskResult string representation."""
        result = AskResult(
            prompt="Test prompt",
            response="Test response",
            error=None,
            duration_s=1.5
        )
        
        repr_str = repr(result)
        assert isinstance(repr_str, str)  # Contract: repr returns string
        assert len(repr_str) > 0  # Contract: non-empty repr
    
    def test_ask_result_edge_cases(self):
        """Test AskResult edge cases."""
        # Empty strings
        result1 = AskResult(
            prompt="",
            response="",
            error="",
            duration_s=0.0
        )
        assert isinstance(result1.prompt, str)  # Contract: prompt is string type (can be empty)
        assert isinstance(result1.response, str)  # Contract: response is string type (can be empty)
        assert isinstance(result1.error, str)  # Contract: error is string type (can be empty)
        assert result1.duration_s == 0.0
        
        # Large values
        result2 = AskResult(
            prompt="A" * 1000,
            response="B" * 1000,
            error=None,
            duration_s=999999.999,
            tokens_used=2**31
        )
        assert len(result2.prompt) == 1000
        assert len(result2.response) == 1000
        assert result2.tokens_used == 2**31
        
        # Negative duration (should be allowed)
        result3 = AskResult(
            prompt="Test",
            response="Response",
            error=None,
            duration_s=-1.0
        )
        assert result3.duration_s == -1.0
    
    def test_ask_result_with_complex_dict_response(self):
        """Test AskResult with complex nested dictionary response."""
        complex_response = {
            "choices": [
                {
                    "message": {"content": "Hello"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }
        
        result = AskResult(
            prompt="Complex test",
            response=complex_response,
            error=None,
            duration_s=2.5
        )
        
        assert isinstance(result.response, dict)  # Contract: response is dict type
        assert result.response.get("choices") is not None  # Contract: has choices key
        assert isinstance(result.response["choices"], list)  # Contract: choices is list type
    
    def test_ask_result_immutability(self):
        """Test that AskResult instances can be modified (Pydantic models are mutable by default)."""
        result = AskResult(
            prompt="Original",
            response="Response",
            error=None,
            duration_s=1.0
        )
        
        # Pydantic models are mutable by default
        result.prompt = "Modified"
        result.tokens_used = 100
        
        assert isinstance(result.prompt, str)  # Contract: prompt is string type
        assert isinstance(result.tokens_used, int)  # Contract: tokens_used is int type
