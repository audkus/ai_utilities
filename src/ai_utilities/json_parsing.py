"""
JSON parsing utilities for robust structured response extraction.

This module provides utilities to extract JSON from AI responses that may contain
extra text, code fences, or minor syntax errors.
"""

import json
from typing import Any, Optional
from json import JSONDecodeError


class JsonParseError(Exception):
    """Raised when JSON cannot be parsed from text."""
    
    def __init__(self, message: str, text: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.text = text
        self.original_error = original_error


def parse_json_from_text(text: str) -> Any:
    """
    Parse JSON from text that may contain extra content or code fences.
    
    This function attempts to extract JSON from text that might include:
    - JSON wrapped in ```json ... ``` code fences
    - Leading or trailing prose around JSON
    - Multiple JSON objects/arrays (returns first valid one)
    
    Args:
        text: Text that potentially contains JSON
        
    Returns:
        Parsed JSON data (dict, list, str, int, float, bool, or None)
        
    Raises:
        JsonParseError: If no valid JSON can be found in the text
        
    Examples:
        >>> parse_json_from_text('{"name": "test"}')
        {'name': 'test'}
        
        >>> parse_json_from_text('```json\\n{"name": "test"}\\n```')
        {'name': 'test'}
        
        >>> parse_json_from_text('Here is the result: {"name": "test"}')
        {'name': 'test'}
    """
    if not text or not text.strip():
        raise JsonParseError("Empty text cannot contain JSON", text)
    
    # Remove code fences if present
    cleaned_text = _remove_code_fences(text.strip())
    
    # Try parsing the entire text first
    try:
        return json.loads(cleaned_text)
    except JSONDecodeError:
        pass  # Continue with more complex extraction
    
    # Try to find JSON within the text
    return _extract_json_from_mixed_text(cleaned_text)


def _remove_code_fences(text: str) -> str:
    """Remove ```json or ``` code fences from text."""
    # Handle ```json ... ``` fences
    if text.startswith('```json'):
        # Find the closing ```
        end_fence = text.find('```', 7)  # Start after '```json'
        if end_fence != -1:
            return text[7:end_fence].strip()
        else:
            # No closing fence, remove the opening
            return text[7:].strip()
    
    # Handle generic ``` fences
    if text.startswith('```'):
        end_fence = text.find('```', 3)
        if end_fence != -1:
            return text[3:end_fence].strip()
        else:
            return text[3:].strip()
    
    return text


def _extract_json_from_mixed_text(text: str) -> Any:
    """
    Extract the first valid JSON object or array from mixed text.
    
    Uses json.JSONDecoder().raw_decode to find JSON at any position.
    """
    decoder = json.JSONDecoder()
    last_error = None
    
    # Look for JSON object or array start
    for i, char in enumerate(text):
        if char in '{[':
            try:
                # Try to decode from this position
                result, end_index = decoder.raw_decode(text, i)
                return result
            except JSONDecodeError as e:
                last_error = e
                continue
    
    # If we get here, no valid JSON was found
    raise JsonParseError(
        "No valid JSON object or array found in text",
        text,
        original_error=last_error
    )


def create_repair_prompt(original_prompt: str, previous_output: str, error_message: str) -> str:
    """
    Create a repair prompt for when JSON parsing fails.
    
    Args:
        original_prompt: The original user prompt
        previous_output: The malformed output that failed to parse
        error_message: The parsing error message
        
    Returns:
        A prompt asking the AI to fix the JSON output
    """
    return f"""The previous response to this prompt could not be parsed as JSON:

Original prompt: {original_prompt}

Previous output: {previous_output}

Error: {error_message}

Please provide a VALID JSON response that directly answers the original prompt.
Requirements:
- Return ONLY valid JSON (object or array)
- No prose, explanations, or code fences
- No leading or trailing text
- No code fences (```json or ```)
- Fix any syntax errors (missing commas, quotes, etc.)

JSON response:"""
