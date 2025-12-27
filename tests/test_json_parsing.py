"""Tests for JSON parsing utilities."""

import pytest
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities.json_parsing import parse_json_from_text, JsonParseError, create_repair_prompt


class TestParseJsonFromText:
    """Test the parse_json_from_text function."""
    
    def test_parse_pure_json_object(self):
        """Test parsing pure JSON object."""
        text = '{"name": "test", "value": 42}'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_pure_json_array(self):
        """Test parsing pure JSON array."""
        text = '["item1", "item2", 123]'
        result = parse_json_from_text(text)
        assert result == ["item1", "item2", 123]
    
    def test_parse_json_with_code_fences(self):
        """Test parsing JSON wrapped in ```json fences."""
        text = '```json\n{"name": "test", "value": 42}\n```'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_json_with_generic_code_fences(self):
        """Test parsing JSON wrapped in generic ``` fences."""
        text = '```\n{"name": "test", "value": 42}\n```'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_json_with_leading_prose(self):
        """Test parsing JSON with leading text."""
        text = 'Here is the result: {"name": "test", "value": 42}'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_json_with_trailing_prose(self):
        """Test parsing JSON with trailing text."""
        text = '{"name": "test", "value": 42} This is the end.'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_json_with_surrounding_prose(self):
        """Test parsing JSON with both leading and trailing text."""
        text = 'The result is: {"name": "test", "value": 42} - End of response.'
        result = parse_json_from_text(text)
        assert result == {"name": "test", "value": 42}
    
    def test_parse_json_with_multiple_objects_returns_first(self):
        """Test that first valid JSON object is returned when multiple exist."""
        text = '{"first": 1} {"second": 2}'
        result = parse_json_from_text(text)
        assert result == {"first": 1}
    
    def test_parse_nested_json(self):
        """Test parsing nested JSON structures."""
        text = '{"outer": {"inner": {"value": 42}}, "array": [1, 2, 3]}'
        result = parse_json_from_text(text)
        assert result == {"outer": {"inner": {"value": 42}}, "array": [1, 2, 3]}
    
    def test_parse_json_types(self):
        """Test parsing various JSON types."""
        # String
        assert parse_json_from_text('"hello world"') == "hello world"
        # Number
        assert parse_json_from_text('42') == 42
        # Float
        assert parse_json_from_text('3.14') == 3.14
        # Boolean
        assert parse_json_from_text('true') is True
        assert parse_json_from_text('false') is False
        # Null
        assert parse_json_from_text('null') is None
    
    def test_error_empty_text(self):
        """Test error on empty text."""
        with pytest.raises(JsonParseError) as exc_info:
            parse_json_from_text("")
        assert "Empty text" in str(exc_info.value)
    
    def test_error_whitespace_only(self):
        """Test error on whitespace-only text."""
        with pytest.raises(JsonParseError):
            parse_json_from_text("   \n\t   ")
    
    def test_error_no_json_found(self):
        """Test error when no JSON is found in text."""
        with pytest.raises(JsonParseError) as exc_info:
            parse_json_from_text("This is just plain text with no JSON.")
        assert "No valid JSON" in str(exc_info.value)
    
    def test_error_malformed_json(self):
        """Test error on malformed JSON."""
        with pytest.raises(JsonParseError) as exc_info:
            parse_json_from_text('{"name": "test", "value":}')  # Missing value
        assert exc_info.value.text == '{"name": "test", "value":}'
    
    def test_error_incomplete_json(self):
        """Test error on incomplete JSON."""
        with pytest.raises(JsonParseError):
            parse_json_from_text('{"name": "test"')  # Missing closing brace
    
    def test_preserves_original_error_info(self):
        """Test that original JSON error is preserved."""
        try:
            parse_json_from_text('{"name": "test", "value":}')
        except JsonParseError as e:
            assert e.original_error is not None
            assert isinstance(e.original_error, json.JSONDecodeError)


class TestCreateRepairPrompt:
    """Test the create_repair_prompt function."""
    
    def test_repair_prompt_content(self):
        """Test that repair prompt contains all required elements."""
        original = "List 5 colors"
        output = '{"colors": ["red", "blue"'  # Missing closing bracket/brace
        error = "Expecting ',' delimiter"
        
        prompt = create_repair_prompt(original, output, error)
        
        assert original in prompt
        assert output in prompt
        assert error in prompt
        assert "VALID JSON" in prompt
        assert "No prose" in prompt
        assert "No code fences" in prompt
    
    def test_repair_prompt_format(self):
        """Test that repair prompt has proper format."""
        prompt = create_repair_prompt("test", "output", "error")
        
        # Should contain the main sections
        assert "Original prompt:" in prompt
        assert "Previous output:" in prompt
        assert "Error:" in prompt
        assert "Requirements:" in prompt
        assert "JSON response:" in prompt
