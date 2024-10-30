# ai_integration.py
"""
This module provides functionality for interacting with AI models, specifically through the OpenAI API.
It includes mechanisms for loading configuration settings, checking if AI usage is enabled, and
initializing AI models based on the configuration. Additionally, it enforces rate limits for
requests per minute (RPM), tokens per minute (TPM), and tokens per day (TPD) based on the model's
configuration. The rate limiter generates an ai_stats_file.json to monitor AI usage.
Responses from the AI are not validated and are returned as is. If you add the parameter "json" to the call,
the script will ensure that only the JSON part of the answer is returned. If no JSON exists, the whole answer
is returned.

Key functionalities include:
- Interaction with the OpenAI API
- Rate limiting for API usage
- Memory usage monitoring

Example usage:
    from ai_utilities import ask_ai, is_ai_usage_enabled

    if is_ai_usage_enabled():
        response = ask_ai("Your prompt here")
        print(response)

    json_response = ask_ai("Your prompt here should also require a JSON return value", 'json')
    print(json_response)

Executing main in module for test use:
    python -m ai_utilities.ai_integration
"""

# Standard Library Imports
import configparser
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Union

# Third-Party Library Imports
import psutil
from openai import OpenAIError

# Local application Imports
from .ai_config_manager import get_model_from_config, initialize_config_file
from .exceptions import RateLimitExceededError
from .error_codes import ERROR_RATE_LIMIT_EXCEEDED
from .ai_call_timer import AICallTimer
from .openai_model import OpenAIModel

# Module-level logger
logger = logging.getLogger(__name__)

# Global variables
_config_path = "config.ini"
_config = configparser.ConfigParser()
initialize_config_file(_config, _config_path)
_model = get_model_from_config(_config, _config_path)
_thread_pool: Optional[ThreadPoolExecutor] = None
_timer_started = False


def is_ai_usage_enabled() -> bool:
    """Checks if AI usage is enabled in the configuration.

    Returns:
        bool: True if AI usage is enabled, False otherwise.
    """
    use_ai: bool = _config.getboolean('AI', 'use_ai')
    logger.debug(f"AI usage enabled: {use_ai}")
    if not use_ai:
        logger.info("AI usage is disabled in the configuration.")
    return use_ai


def ask_ai(prompt: Union[str, List[str]], return_format: str = 'text', model: Optional[str] = None) -> Union[str, List[str]]:
    """Handles error management for sending a prompt or list of prompts to the AI model.

    Args:
        prompt (Union[str, List[str]]): The prompt(s) to send to the AI model.
        return_format (str): The format of the returned response ('text' or 'json'). Defaults to 'text'.
        model (Optional[str]): The model to use for the AI request. Defaults to the global model if None.

    Returns:
        Union[str, List[str]]: The AI model's response(s), formatted as specified.
    """
    with AICallTimer() as buffer_handler:
        try:
            return _execute_ai_request(prompt, return_format, model)
        except OpenAIError as e:
            logger.error(f"OpenAIError: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise


def _execute_ai_request(prompt: Union[str, List[str]], return_format: str, model: Optional[str]) -> Union[str, List[str]]:
    """Executes the core logic for sending a prompt or list of prompts to the AI model.

    Args:
        prompt (Union[str, List[str]]): The prompt(s) to send to the AI model.
        return_format (str): The format of the returned response ('text' or 'json').
        model (Optional[str]): The model to use for the AI request.

    Returns:
        Union[str, List[str]]: The AI model's response(s), formatted as specified.
    """
    global _model

    # Ensure _model is initialized with the correct API key and model
    if model or _model is None:
        _initialize_model(model)

    # Process single or multiple prompts
    if isinstance(prompt, str):
        response = _send_single_prompt(prompt, return_format)
    else:
        response = _process_prompt_list(prompt, return_format)

    return response


def _check_memory_and_rate_limit(prompt: str) -> int:
    """Monitors memory usage and checks if rate limits allow the request.

    Args:
        prompt (str): The prompt to send to the AI model.

    Returns:
        int: Estimated token count of the prompt.

    Raises:
        RateLimitExceededError: If rate limit is exceeded.
    """
    memory_threshold = float(_config.get('AI', 'memory_threshold', fallback=0.8))
    _monitor_memory_usage(memory_threshold)

    tokens: int = len(prompt.split())  # Estimate token count

    if not _model.rate_limiter.can_proceed(tokens):
        logger.error(f"Rate limit exceeded for prompt: {prompt}")
        raise RateLimitExceededError(f"{ERROR_RATE_LIMIT_EXCEEDED}: Rate limit exceeded")

    return tokens


def _send_prompt_and_process_response(prompt: str, return_format: str, tokens: int) -> Optional[str]:
    """Sends the prompt to the AI model, processes the response, and formats it if needed.

    Args:
        prompt (str): The prompt to send to the AI model.
        return_format (str): The desired format of the response ('text' or 'json').
        tokens (int): Token count of the prompt.

    Returns:
        Optional[str]: The processed response from the AI model.
    """
    logger.info(f"Sending prompt to AI model: {prompt}")

    chatgpt_answer = _model.client.chat.completions.create(
        model=_model.model,
        messages=[{"role": "user", "content": prompt}]
    )

    response: str = chatgpt_answer.choices[0].message.content.strip()
    logger.info(f"Received AI response: {response}")

    if return_format.lower() == 'json':
        response = OpenAIModel.clean_response(response)
        logger.debug(f"Cleaned JSON response: {response}")

    _model.rate_limiter.record_usage(tokens)
    return response


def _send_single_prompt(prompt: str, return_format: str = 'text') -> Optional[str]:
    """Sends a single prompt to the AI model and returns the response.

    Args:
        prompt (str): The prompt to send to the AI model.
        return_format (str): The desired format of the response ('text' or 'json'). Defaults to 'text'.

    Returns:
        Optional[str]: The AI model's response in the specified format, or None if an error occurred.
    """
    try:
        tokens = _check_memory_and_rate_limit(prompt)
        return _send_prompt_and_process_response(prompt, return_format, tokens)

    except OpenAIError as e:
        logger.error(f"OpenAIError: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def _initialize_model(model: Optional[str] = None) -> None:
    """Initializes the global AI model based on the configuration.

    Args:
        model (Optional[str]): The model to initialize if alternative from default provided.
    """
    global _model, _config_path

    # Reload config and initialize the model
    _config.read(_config_path)
    _model = get_model_from_config(_config, _config_path, model=model)
    if not _model:
        logger.error("Failed to initialize AI model from configuration.")


def _process_prompt_list(prompts: List[str], return_format: str) -> List[Optional[str]]:
    """Processes a list of prompts using the AI model.

    Args:
        prompts (List[str]): The list of prompts to process.
        return_format (str): The format of the returned response ('text' or 'json').

    Returns:
        List[Optional[str]]: A list of responses for each prompt, formatted as specified.
    """
    results: List[Optional[str]] = []

    for prompt in prompts:
        try:
            result = _send_single_prompt(prompt, return_format)
            results.append(result)
        except OpenAIError as e:
            logger.error(f"OpenAIError: {str(e)}")
            results.append(f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            results.append(f"Error: {str(e)}")

    return results


def _monitor_memory_usage(threshold: float) -> None:
    """Monitors memory usage and waits if it exceeds the threshold.

    Args:
        threshold (float): Memory usage percentage threshold (e.g., 0.8 for 80%).

    Raises:
        MemoryUsageExceededError: If memory usage exceeds the threshold.
    """
    while not _is_memory_usage_below_threshold(threshold):
        logger.warning("Memory usage too high, waiting to submit tasks.")
        time.sleep(5)


def _is_memory_usage_below_threshold(threshold: float) -> bool:
    """Checks if memory usage is below the threshold.

    Args:
        threshold (float): Memory usage percentage threshold.

    Returns:
        bool: True if memory usage is below the threshold, False otherwise.
    """
    memory_info = psutil.virtual_memory()
    return memory_info.percent / 100.0 < threshold


def main() -> None:
    """Demonstrates example usage of the ai_integration module."""
    if is_ai_usage_enabled():
        prompt_single_text = "Who was the first human to walk on the moon?"
        print(f'\n# Example with a single prompt:\nQuestion: {prompt_single_text}')
        result_single_text = ask_ai(prompt_single_text)
        print(f'Answer: {result_single_text}')

        print(f'\n# Example with multiple prompts:')
        prompts_multiple_text = [
            "Who was the last person to walk on the moon?",
            "What is Kant’s categorical imperative in simple terms?",
            "What is the Fibonacci sequence? Do not include examples."
        ]

        results_multiple_text = ask_ai(prompts_multiple_text)

        if results_multiple_text:
            for question, result in zip(prompts_multiple_text, results_multiple_text):
                print(f"\nQuestion: {question}")
                print(f"Answer: {result}")

        print(f'\n# Example with a single prompt in JSON format:')
        prompt_single = "What are the current top 5 trends in AI, just the title? Please return the answer as a JSON format"
        return_format = "json"
        print(f'\nQuestion: {prompt_single}')
        result_single_json = ask_ai(prompt_single, return_format)
        print(f'Answer:\n{result_single_json}')

        print(f'\n# Example using a custom model "gpt-3.5-turbo":')
        prompt_custom_model = "What is the capital of France?"
        print(f'\nQuestion: {prompt_custom_model}')
        response = ask_ai(prompt_custom_model, model="gpt-3.5-turbo")
        print(f'Answer:{response}')
    else:
        print("AI usage is disabled in the configuration.")


if __name__ == "__main__":
    main()
