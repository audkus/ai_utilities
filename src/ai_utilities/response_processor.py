"""
response_processor.py

Response processing utilities with single responsibility for cleaning and formatting responses.
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """
    Handles response processing with single responsibility for cleaning and formatting.
    
    This class only handles response processing tasks like JSON extraction,
    response cleaning, and format validation. It doesn't make API calls or
    handle rate limiting.
    """

    @staticmethod
    def extract_json(response: str) -> str:
        """
        Extract JSON from response text.
        
        Args:
            response: Raw response text from AI model
            
        Returns:
            Extracted JSON string or original response if no valid JSON found
        """
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1

        if start_idx == -1 or end_idx == -1:
            logger.debug("No valid JSON structure found in response")
            return response

        json_candidate = response[start_idx:end_idx]
        
        # Validate that it's valid JSON
        if ResponseProcessor.is_valid_json(json_candidate):
            logger.debug(f"Valid JSON extracted: {json_candidate[:100]}...")
            return json_candidate
        else:
            logger.debug("Extracted text is not valid JSON")
            return response

    @staticmethod
    def is_valid_json(text: str) -> bool:
        """
        Check if text is valid JSON.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid JSON, False otherwise
        """
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    @staticmethod
    def clean_text(response: str) -> str:
        """
        Clean text response by removing extra whitespace and formatting.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned text
        """
        # Remove leading/trailing whitespace
        cleaned = response.strip()
        
        # Normalize multiple consecutive whitespace to single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        logger.debug(f"Text cleaned: {cleaned[:100]}...")
        return cleaned

    @staticmethod
    def format_response(response: str, return_format: str = "text") -> str:
        """
        Format response according to requested format.
        
        Args:
            response: Raw response from AI model
            return_format: Desired format ("text" or "json")
            
        Returns:
            Formatted response
        """
        if return_format == "json":
            return ResponseProcessor.extract_json(response)
        else:
            return ResponseProcessor.clean_text(response)

    @staticmethod
    def extract_code_blocks(response: str, language: Optional[str] = None) -> list[str]:
        """
        Extract code blocks from response.
        
        Args:
            response: Response text containing code blocks
            language: Optional language filter (e.g., "python", "javascript")
            
        Returns:
            List of extracted code blocks
        """
        if language:
            pattern = rf'```{language}\n(.*?)\n```'
        else:
            pattern = r'```(?:\w+)?\n(.*?)\n```'
        
        matches = re.findall(pattern, response, re.DOTALL)
        logger.debug(f"Found {len(matches)} code blocks")
        return matches
