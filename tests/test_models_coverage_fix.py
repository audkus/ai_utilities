"""Test to fix coverage measurement for models.py."""

def test_models_coverage():
    """Test that models.py coverage is measured correctly."""
    # Import inside the test to ensure coverage tracking
    import ai_utilities.models
    from ai_utilities.models import AskResult
    
    # Execute actual code
    result = AskResult(
        prompt="test",
        response="test response",
        error=None,
        duration_s=1.0
    )
    
    # Assertions to ensure behavior
    assert result.prompt == "test"
    assert result.response == "test response"
    assert result.error is None
    assert result.duration_s == 1.0
    assert result.tokens_used is None
    assert result.model is None
    
    # Test serialization
    result_dict = result.model_dump()
    assert isinstance(result_dict, dict)
    assert result_dict["prompt"] == "test"
