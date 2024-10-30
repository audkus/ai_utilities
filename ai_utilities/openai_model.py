"""
openai_model.py

This module provides the OpenAIModel class for interacting with OpenAI's API.
"""

# Standard Library Imports
import logging
from configparser import ConfigParser

# Third-Party Library Imports
from openai import OpenAIError

# Local application Imports
from .rate_limiter import RateLimiter
from .exceptions import RateLimitExceededError
from .error_codes import ERROR_RATE_LIMIT_EXCEEDED

logger = logging.getLogger(__name__)


class OpenAIModel:
    """
    Represents an AI model using OpenAI's API with rate limiting and configuration management.

    Attributes:
        api_key (str): The API key for accessing the OpenAI API.
        model (str): The model name to be used (e.g., "gpt-4").
        rate_limiter (RateLimiter): A RateLimiter instance to manage API rate limits.
    """

    def __init__(self, api_key: str, model: str, config: ConfigParser, config_path: str) -> None:
        """
        Initializes the OpenAIModel with the given API key, model name, configuration, and config path.

        Args:
            api_key (str): The API key for OpenAI.
            model (str): The specific model to use.
            config (ConfigParser): Configuration settings for rate limits.
            config_path (str): The path to the configuration file.
        """
        from openai import OpenAI  # Ensure the library is imported here to avoid import issues

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.rate_limiter = RateLimiter(
            module_name=model,
            rpm=config.getint(model, 'requests_per_minute'),
            tpm=config.getint(model, 'tokens_per_minute'),
            tpd=config.getint(model, 'tokens_per_day'),
            config_path=config_path
        )
        self.rate_limiter.start_reset_timer()
        logger.debug(f"OpenAIModel initialized with model: {model}")

    def ask_ai(self, prompt: str, return_format: str = 'text') -> str:
        """Sends a prompt to the OpenAI model and returns the response.

        Args:
            prompt (str): The prompt to send to the AI model.
            return_format (str): The format of the returned response ('text' or 'json').

        Returns:
            str: The AI model's response.

        Raises:
            RateLimitExceededError: If the rate limit is exceeded.
            OpenAIError: If an error occurs with the OpenAI API.
        """
        tokens = len(prompt.split())
        if not self.rate_limiter.can_proceed(tokens):
            logger.error("Rate limit exceeded")
            raise RateLimitExceededError(f"{ERROR_RATE_LIMIT_EXCEEDED}: Rate limit exceeded")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content.strip()

        return response

    @staticmethod
    def clean_response(response: str) -> str:
        """Cleans the AI model's response to extract a valid JSON structure if required.

        Args:
            response (str): The raw response from the AI model.

        Returns:
            str: The cleaned JSON response or the original response if no valid JSON is found.
        """
        start_idx: int = response.find('{')
        end_idx: int = response.rfind('}') + 1

        if start_idx == -1 or end_idx == -1:
            logger.error("Response does not contain a valid JSON structure. Returning the original response.")
            return response

        cleaned_response: str = response[start_idx:end_idx]
        logger.debug(f"Cleaned response: {cleaned_response}")
        return cleaned_response
