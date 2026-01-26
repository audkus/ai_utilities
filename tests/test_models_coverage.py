"""Coverage tests for models.py to reach 100%."""

import pytest
from typing import Dict, Any
import ai_utilities.models as m


def test_models_import_and_basic_usage():
    """Test importing models and basic AskResult creation."""
    # Test that we can import the module
    assert hasattr(m, 'AskResult')
    
    # Test basic creation with required fields
    result = m.AskResult(
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


def test_ask_result_with_dict_response():
    """Test AskResult with dictionary response."""
    dict_response = {"content": "test", "type": "text"}
    result = m.AskResult(
        prompt="test",
        response=dict_response,
        error=None,
        duration_s=2.0
    )
    
    assert result.response == dict_response
    assert isinstance(result.response, dict)


def test_ask_result_with_optional_fields():
    """Test AskResult with all optional fields set."""
    result = m.AskResult(
        prompt="test",
        response="response",
        error=None,
        duration_s=1.0,
        tokens_used=100,
        model="gpt-4"
    )
    
    assert result.tokens_used == 100
    assert result.model == "gpt-4"


def test_ask_result_validation():
    """Test that AskResult validates required fields."""
    # This should work - all required fields provided
    result = m.AskResult(
        prompt="test",
        response="response",
        error="error message",
        duration_s=0.5
    )
    assert result.error == "error message"
    
    # Test that the model is properly constructed
    assert hasattr(result, 'prompt')
    assert hasattr(result, 'response')
    assert hasattr(result, 'error')
    assert hasattr(result, 'duration_s')
    assert hasattr(result, 'tokens_used')
    assert hasattr(result, 'model')


def test_ask_result_field_types():
    """Test that field types are correct."""
    result = m.AskResult(
        prompt="string",
        response={"key": "value"},
        error="string",
        duration_s=1.5,
        tokens_used=42,
        model="model-name"
    )
    
    assert isinstance(result.prompt, str)
    assert isinstance(result.response, (str, dict))
    assert isinstance(result.error, (str, type(None)))
    assert isinstance(result.duration_s, float)
    assert isinstance(result.tokens_used, (int, type(None)))
    assert isinstance(result.model, (str, type(None)))
