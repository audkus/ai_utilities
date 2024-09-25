
"""
ai_integration.py

This module provides functionality for interacting with AI models, specifically through the OpenAI API.
It includes mechanisms for loading configuration settings, checking if AI usage is enabled, and
initializing AI models based on the configuration. Additionally, it enforces rate limits for
requests per minute (RPM), tokens per minute (TPM), and tokens per day (TPD) based on the model's
configuration. The rate limiter generates an ai_stats_file.json to monitor AI usage.
Responses from the AI are not validated and are returned as is. If you add the parameter "json" to the call,
the script will ensure that only the JSON part of the answer is returned. If no JSON exists, the whole answer is returned.
The script does not validate the answer.

Key functionalities include:
- Interaction with the OpenAI API
- Rate limiting for API usage
- Memory usage monitoring

Example usage:
    from test_generator.ai_models import ask_ai

    response = ask_ai("Your prompt here")
    print(response)

    json_response = ask_ai("Your prompt here should also require a JSON return value", 'json')
    print(json_response)
"""

# Standard Library Imports
import logging
import configparser
import os
import psutil
import time
from typing import Optional, Protocol, Dict, Any, List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-Party Library Imports
from openai import OpenAIError
import config_utilities
from config_utilities.config_manager import load_and_validate_config, save_config

# Local application Imports
from ai_utilities.ai_config_manager import get_model_from_config, set_default_ai_config, set_default_model_configs
from ai_utilities.rate_limiter import RateLimiter

# Global model instance
_model: Optional['AIModel'] = None
_thread_pool: Optional[ThreadPoolExecutor] = None  # _thread_pool is defined at module level

# Set up logging configuration
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_error_message(error: OpenAIError) -> str:
    """
    Extract a meaningful error message from an OpenAIError exception.

    Args:
        error (OpenAIError): The error object returned by the OpenAI API.

    Returns:
        str: A detailed error message string.
    """
    try:
        return error.json_body.get('error', {}).get('message', 'No additional details available.')
    except AttributeError:
        return str(error)


class AIModel(Protocol):
    """
    A protocol that defines the interface for an AI model.

    Methods:
        ask_ai(prompt: str, return_format: str = 'text') -> Optional[str]:
            Sends a prompt to the AI model and returns the response.
    """
    def ask_ai(self, prompt: str, return_format: str = 'text') -> Optional[str]:
        pass


class OpenAIModel:
    """
    A class that represents an AI model using OpenAI's GPT API.

    Attributes:
        client (OpenAI): The OpenAI client instance.
        model (str): The model identifier for OpenAI API.
        rate_limiter (RateLimiter): Rate limiting for API requests.

    Args:
        api_key (str): The API key for OpenAI.
        model (str): The specific model to use.
        config (configparser.ConfigParser): Configuration settings for rate limits.
    """

    def __init__(self, api_key: str, model: str, config: configparser.ConfigParser, config_path: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.rate_limiter = RateLimiter(
            module_name=model,  # Pass the model name as the module_name
            rpm=config.getint(model, 'requests_per_minute'),
            tpm=config.getint(model, 'tokens_per_minute'),
            tpd=config.getint(model, 'tokens_per_day'),
            config_path=config_path
        )
        self.rate_limiter.start_reset_timer()
        logging.debug(f"OpenAIModel initialized with model: {model}")

    def ask_ai(self, prompt: str, return_format: str = 'text') -> Optional[str]:
        """
        Sends a prompt to the OpenAI model and returns the response.

        Args:
            prompt (str): The prompt to send to the AI model.
            return_format (str): The format of the returned response ('text' or 'json').

        Returns:
            Optional[str]: The AI model's response, formatted as specified.
        """
        # Monitor memory usage before processing the prompt
        memory_threshold: float = 0.8  # Set your desired memory threshold (80%)
        monitor_memory_usage(memory_threshold)

        tokens: int = len(prompt.split())
        if not self.rate_limiter.can_proceed(tokens):
            logging.error("Rate limit exceeded")
            raise Exception("Rate limit exceeded")

        try:
            logging.debug(f"Sending prompt to OpenAI model: {prompt}")
            chatgpt_answer = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            response: str = chatgpt_answer.choices[0].message.content.strip()
            logging.debug(f"Received response: {response}")

            # Directly return the response based on the specified format
            if response and return_format.lower() == 'json':
                response = self.clean_response(response)
                print(f'response: {response}')
                logging.debug(f"Cleaned JSON response: {response}")

            self.rate_limiter.record_usage(tokens)

            return response
        except OpenAIError as e:
            error_message = get_error_message(e)
            logging.error(f"OpenAIError: {error_message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    @staticmethod
    def clean_response(response: str) -> str:
        """
        Cleans the AI model's response to extract a valid JSON structure if required.

        Args:
            response (str): The raw response from the AI model.

        Returns:
            str: The cleaned JSON response or the original response if no valid JSON is found.
        """
        start_idx: int = response.find('{')
        end_idx: int = response.rfind('}') + 1

        if start_idx == -1 or end_idx == -1:
            logging.error(
                f"Response does not contain a valid JSON structure. Returning the original response:\n{response}")
            return response  # Return the original response instead of raising an error

        cleaned_response: str = response[start_idx:end_idx]
        logging.debug(f"Cleaned response: {cleaned_response}")
        return cleaned_response


def handle_ai_responses(futures: List[Any]) -> None:
    """
    Handles the completed AI response from threaded execution.

    Args:
        futures (list): List of Future objects from the thread pool.
    """
    for future in as_completed(futures):
        try:
            result = future.result()
            logging.info(f"Received AI result: {result}")
        except Exception as e:
            logging.error(f"Error in AI request: {e}")


def initialize_model(config: configparser.ConfigParser) -> Optional[ThreadPoolExecutor]:
    """
    Initializes the global AI model based on the configuration.

    Args:
        config (configparser.ConfigParser): The configuration object.

    Returns:
        Optional[ThreadPoolExecutor]: A ThreadPoolExecutor instance for concurrent task execution,
                                       or None if AI usage is disabled.
    """
    global _model, _thread_pool
    _thread_pool = initialize_thread_pool(config)

    # Ensure AI and model-specific configurations are set
    config, config_path = load_and_validate_config()
    set_default_ai_config(config)
    set_default_model_configs(config)
    save_config(config, config_path)

    if not is_ai_usage_enabled(config):
        _model = None
        return None

    # Initialize the global AI model if not already initialized
    if _model is None:
        _model = get_model_from_config(config, config_path)

    return _thread_pool


def initialize_thread_pool(config: configparser.ConfigParser) -> ThreadPoolExecutor:
    """
    Initializes a thread pool for concurrent task execution.

    Args:
        config (configparser.ConfigParser): The configuration object.

    Returns:
        ThreadPoolExecutor: A ThreadPoolExecutor instance for concurrent task execution.
    """
    max_workers: int = min(32, os.cpu_count() + 4)
    if config.has_option('thread_pool', 'max_workers'):
        max_workers = config.getint('thread_pool', 'max_workers')

    return ThreadPoolExecutor(max_workers=max_workers)


def monitor_memory_threshold(threshold: float) -> bool:
    """
    Monitors the system memory usage and returns True if it is below the threshold.

    Args:
        threshold (float): Memory usage percentage threshold (e.g., 0.8 for 80%).

    Returns:
        bool: True if memory usage is below the threshold, False otherwise.
    """
    memory_info = psutil.virtual_memory()
    return memory_info.percent / 100.0 < threshold


def ask_ai(prompt: Union[str, List[str]], return_format: str = 'text') -> Union[str, List[str], None]:
    """
    Sends a prompt or list of prompts to the global AI model and returns the response(s).

    Args:
        prompt (Union[str, List[str]]): The prompt(s) to send to the AI model.
        return_format (str): The format of the returned response ('text' or 'json').

    Returns:
        Union[str, List[str], None]: The AI model's response(s), formatted as specified,
                                       or None if AI usage is disabled.
    """
    return_format = return_format.strip().lower()

    global _model, _thread_pool

    # Initialize model and thread pool if not already initialized
    if _model is None:
        config = configparser.ConfigParser()
        config.read('config.ini')
        if initialize_model(config) is None:
            logging.debug("AI model initialization skipped because AI usage is disabled.")
            return None

    if _thread_pool is None:
        initialize_thread_pool(config)

    # Convert single prompt to list if necessary
    if isinstance(prompt, str):
        prompts: List[str] = [prompt]
    elif isinstance(prompt, list):
        prompts = prompt
    else:
        raise TypeError("Prompt must be a string or a list of strings")

    # Monitor memory usage before submitting tasks
    memory_threshold: float = 0.8
    monitor_memory_usage(memory_threshold)

    # Use threading for multiple prompts
    if len(prompts) > 1:
        futures: List[Any] = []
        for prompt in prompts:
            future = _thread_pool.submit(_model.ask_ai, prompt, return_format)
            futures.append(future)

        results: List[Optional[str]] = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except OpenAIError as e:
                error_message = get_error_message(e)
                logging.error(f"OpenAIError: {error_message}")
                results.append(f"Error: {error_message}")
            except Exception as e:
                logging.error(f"Unexpected error in AI request: {str(e)}")
                results.append(f"Error: {str(e)}")

        return results
    else:
        try:
            return _model.ask_ai(prompts[0], return_format)
        except OpenAIError as e:
            error_message = get_error_message(e)
            logging.error(f"OpenAIError: {error_message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in AI request: {str(e)}")
            raise


def is_ai_usage_enabled(config: configparser.ConfigParser) -> bool:
    """
    Checks if AI usage is enabled in the configuration.

    Args:
        config (configparser.ConfigParser): The configuration object.

    Returns:
        bool: True if AI usage is enabled, False otherwise.
    """
    use_ai: bool = config.getboolean('AI', 'use_ai')
    logging.debug(f"AI usage enabled: {use_ai}")
    if not use_ai:
        logging.info("AI usage is disabled in the configuration.")
    return use_ai


def monitor_memory_usage(threshold: float) -> None:
    """
    Monitors memory usage and logs a warning if it exceeds the threshold.

    Args:
        threshold (float): Memory usage percentage threshold (e.g., 0.8 for 80%).
    """
    logged_warning: bool = False  # Flag to track if warning has been logged

    while not monitor_memory_threshold(threshold):
        if not logged_warning:
            logging.warning("Memory usage too high, waiting to submit tasks.")
            logged_warning = True
        time.sleep(5)  # Wait for 5 seconds and check memory again


def main() -> None:
    """
    Example usage of the ai_integration module.
    """
    prompt_single_text = "What are the current top 2 trends in AI?"
    result_single_text = ask_ai(prompt_single_text)
    print(f'Example with a single prompt:\n{result_single_text}')

    prompts_multiple_text = [
        "Hello, how are you?",
        "What are your plans for today?",
        "Tell me about your favorite book."
    ]
    results_multiple_text = ask_ai(prompts_multiple_text)
    print(f'Example with multiple prompts:')
    if results_multiple_text:
        for result in results_multiple_text:
            print(result)

    prompt_single = "What are the current top 2 trends in AI, just the title? Please return the answer as a JSON format"

    return_format = "json"

    result_single_json = ask_ai(prompt_single, return_format)
    print(f'\nExample with a single prompt in JSON format: \n{result_single_json}')


if __name__ == "__main__":
    main()
