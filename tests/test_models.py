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
        
        assert result.prompt == "What is the meaning of life?"
        assert result.response == "The meaning of life is 42."
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
        
        assert result.prompt == "Test prompt"
        assert result.response == {"key": "value"}
        assert result.error is None
        assert result.duration_s == 2.3
        assert result.tokens_used == 100
        assert result.model == "gpt-4"
    
    def test_ask_result_with_string_response(self):
        """Test AskResult with string response."""
        result = AskResult(
            prompt="Hello",
            response="Hi there!",
            error=None,
            duration_s=0.5
        )
        
        assert isinstance(result.response, str)
        assert result.response == "Hi there!"
    
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
        assert result.error == "API rate limit exceeded"
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
        assert "prompt" in str(exc_info.value)
        
        # Missing response
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                error=None,
                duration_s=1.0
            )
        assert "response" in str(exc_info.value)
        
        # Missing error
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                response="Response",
                duration_s=1.0
            )
        assert "error" in str(exc_info.value)
        
        # Missing duration_s
        with pytest.raises(ValidationError) as exc_info:
            AskResult(
                prompt="Test",
                response="Response",
                error=None
            )
        assert "duration_s" in str(exc_info.value)
    
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
        
        assert data["prompt"] == "Test prompt"
        assert data["response"] == "Test response"
        assert data["error"] is None
        assert data["duration_s"] == 1.5
        assert data["tokens_used"] == 50
        assert data["model"] == "gpt-3.5-turbo"
    
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
        
        assert result.prompt == "Test prompt"
        assert result.response == "Test response"
        assert result.error is None
        assert result.duration_s == 1.5
        assert result.tokens_used == 75
        assert result.model == "gpt-4"
    
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
        assert parsed["prompt"] == "Test"
        assert parsed["response"] == "Response"
    
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
        assert "AskResult" in repr_str
        assert "Test prompt" in repr_str
    
    def test_ask_result_edge_cases(self):
        """Test AskResult edge cases."""
        # Empty strings
        result1 = AskResult(
            prompt="",
            response="",
            error="",
            duration_s=0.0
        )
        assert result1.prompt == ""
        assert result1.response == ""
        assert result1.error == ""
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
        
        assert result.response == complex_response
        assert result.response["choices"][0]["message"]["content"] == "Hello"
        assert result.response["usage"]["prompt_tokens"] == 10
    
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
        
        assert result.prompt == "Modified"
        assert result.tokens_used == 100
