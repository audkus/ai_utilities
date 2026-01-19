"""
openai_model.py

Refactored OpenAI model using composition with single-responsibility components.
"""

import logging
import configparser
from configparser import ConfigParser

from .error_codes import ERROR_RATE_LIMIT_EXCEEDED
from .exceptions import RateLimitExceededError
from .openai_client import OpenAIClient

# Local application Imports
from .rate_limiter import RateLimiter
from .response_processor import ResponseProcessor
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)


class OpenAIModel:
    """
    OpenAI model orchestrator using composition of single-responsibility components.
    
    This class coordinates between specialized components instead of handling
    multiple responsibilities directly. Each component has a single, well-defined purpose.
    """

    def __init__(self, api_key: str, model: str, config: ConfigParser, config_path: str) -> None:
        """
        Initializes the OpenAIModel with composed components.

        Args:
            api_key (str): The API key for OpenAI.
            model (str): The specific model to use.
            config (ConfigParser): Configuration settings for rate limits.
            config_path (str): The path to the configuration file.
        """
        # Initialize components with single responsibilities
        self.api_client = OpenAIClient(api_key=api_key)
        self.response_processor = ResponseProcessor()
        self.token_counter = TokenCounter()
        
        # Handle missing config sections gracefully with fallback defaults
        try:
            rpm = config.getint(model, 'requests_per_minute')
        except (configparser.NoSectionError, configparser.NoOptionError):
            rpm = 60  # Default fallback
            
        try:
            tpm = config.getint(model, 'tokens_per_minute')
        except (configparser.NoSectionError, configparser.NoOptionError):
            tpm = 10000  # Default fallback
            
        try:
            tpd = config.getint(model, 'tokens_per_day')
        except (configparser.NoSectionError, configparser.NoOptionError):
            tpd = 100000  # Default fallback
        
        self.rate_limiter = RateLimiter(
            module_name=model,
            rpm=rpm,
            tpm=tpm,
            tpd=tpd,
            config_path=config_path
        )
        
        # Model configuration
        self.model = model
        
        # Start rate limiter
        self.rate_limiter.start_reset_timer()
        logger.debug(f"OpenAIModel initialized with model: {model}")

    def ask_ai(self, prompt: str, return_format: str = 'text') -> str:
        """
        Sends a prompt to the OpenAI model and returns the response.

        Args:
            prompt (str): The prompt to send to the AI model.
            return_format (str): The format of the returned response ('text' or 'json').

        Returns:
            str: The AI model's response.

        Raises:
            RateLimitExceededError: If the rate limit is exceeded.
            OpenAIError: If an error occurs with the OpenAI API.
        """
        # Use token counter for rate limiting
        prompt_tokens = self.token_counter.count_tokens_for_model(prompt, self.model)
        
        # Check rate limiting
        if not self.rate_limiter.can_proceed(prompt_tokens):
            logger.error("Rate limit exceeded")
            raise RateLimitExceededError(f"{ERROR_RATE_LIMIT_EXCEEDED}: Rate limit exceeded")

        # Create messages for API call
        messages = [{"role": "user", "content": prompt}]
        
        # Use API client for communication
        response = self.api_client.create_chat_completion(
            model=self.model,
            messages=messages
        )
        
        # Guard against None content before stripping
        content = response.choices[0].message.content or ""
        raw_response = content.strip()
        
        # Use response processor for formatting
        formatted_response = self.response_processor.format_response(
            raw_response, 
            return_format
        )
        
        return formatted_response

    @staticmethod
    def clean_response(response: str) -> str:
        """
        Clean and format response text (deprecated).
        
        This method is deprecated and will be removed in a future version.
        Use ResponseProcessor.extract_json() instead.
        
        Args:
            response: Raw response string
            
        Returns:
            Cleaned response string
        """
        import warnings
        warnings.warn(
            "OpenAIModel.clean_response() is deprecated. Use ResponseProcessor.extract_json() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Also log the deprecation for test capture
        logger.warning("OpenAIModel.clean_response() is deprecated. Use ResponseProcessor.extract_json() instead.")
        
        # Use ResponseProcessor for backward compatibility
        try:
            return ResponseProcessor.extract_json(response)
        except Exception:
            # If JSON extraction fails, return cleaned text
            return response.strip()
