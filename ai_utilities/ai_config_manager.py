
"""
ai_config_manager.py

This module provides utilities for setting up and managing AI-related configurations
within a Python project. It handles setting default configurations for AI models,
validating the configuration, and retrieving model-specific settings.

Key functionalities include:
- Setting default AI and model-specific configuration values.
- Validating and retrieving AI model settings.
- Handling different AI providers and their respective configurations.

Example usage:
    from ai_config_manager import set_default_ai_config, get_model_from_config

    config = configparser.ConfigParser()
    set_default_ai_config(config)

    model = get_model_from_config(config, config_path)
"""

import os
import configparser
import logging
from typing import Optional


def set_default_ai_config(config: configparser.ConfigParser) -> None:
    """
    Set default AI configuration values in the provided ConfigParser object.

    Args:
        config (configparser.ConfigParser): The configuration object to update.
    """
    if not config.has_section("AI"):
        config.add_section("AI")
    config.set("AI", "use_ai", config.get("AI", "use_ai", fallback="true"))
    config.set("AI", "ai_provider", config.get("AI", "ai_provider", fallback="openai"))

    if not config.has_section("openai"):
        config.add_section("openai")
    config.set("openai", "model", config.get("openai", "model", fallback="gpt-4"))
    config.set("openai", "api_key", config.get("openai", "api_key", fallback="OPENAI_API_KEY"))


    # if not config.has_section("copilot"):
    #     config.add_section("copilot")
    # config.set("copilot", "model", config.get("copilot", "model", fallback=""))
    # config.set("copilot", "api_key", config.get("copilot", "api_key", fallback=""))


def set_default_model_configs(config: configparser.ConfigParser) -> None:
    """
    Set default configuration values for specific models, such as 'gpt-4' and 'gpt-3.5-turbo'.

    Args:
        config (configparser.ConfigParser): The configuration object to update.
    """
    if not config.has_section("gpt-4"):
        config.add_section("gpt-4")
    config.set("gpt-4", "requests_per_minute", config.get("gpt-4", "requests_per_minute", fallback="5000"))
    config.set("gpt-4", "tokens_per_minute", config.get("gpt-4", "tokens_per_minute", fallback="450000"))
    config.set("gpt-4", "tokens_per_day", config.get("gpt-4", "tokens_per_day", fallback="1350000"))

    if not config.has_section("gpt-3.5-turbo"):
        config.add_section("gpt-3.5-turbo")
    config.set("gpt-3.5-turbo", "requests_per_minute",
               config.get("gpt-3.5-turbo", "requests_per_minute", fallback="5000"))
    config.set("gpt-3.5-turbo", "tokens_per_minute",
               config.get("gpt-3.5-turbo", "tokens_per_minute", fallback="2000000"))
    config.set("gpt-3.5-turbo", "tokens_per_day", config.get("gpt-3.5-turbo", "tokens_per_day", fallback="20000000"))


def get_model_from_config(config: configparser.ConfigParser, config_path: str) -> Optional['OpenAIModel']:
    """
    Initializes and returns an AI model based on the configuration.

    Args:
        config (configparser.ConfigParser): The configuration object.
        config_path (str): The path to the configuration file.

    Returns:
        Optional[OpenAIModel]: An instance of OpenAIModel if AI usage is enabled, otherwise None.

    Raises:
        ValueError: If the AI provider specified in the config is unsupported.
    """
    from ai_utilities.ai_integration import OpenAIModel

    use_ai = config.getboolean('AI', 'use_ai')
    if not use_ai:
        logging.info("AI usage is disabled in the configuration.")
        return None

    ai_provider = config.get('AI', 'ai_provider')
    logging.debug(f"Configured AI provider: {ai_provider}")

    if ai_provider.lower() == 'none':
        logging.warning('No ai_provider set in config.ini section [AI]')
        return None
    elif ai_provider == 'openai':
        try:
            api_key = os.getenv(config.get('openai', 'api_key'))
            if not api_key:
                raise ValueError("API key not found in environment variables.")
        except Exception as e:
            logging.error(f"Failed to retrieve OpenAI API key: {e}")
            return None

        try:
            model_name = config.get('openai', 'model')
            if not model_name:
                raise ValueError("Model name not found in the config.")
        except Exception as e:
            logging.error(f"Failed to retrieve OpenAI model name: {e}")
            return None

        logging.debug(f"Initializing OpenAIModel with model: {model_name}")
        logging.debug(f"OpenAI API Key: {api_key[:4]}****")

        return OpenAIModel(api_key=api_key, model=model_name, config=config, config_path=config_path)
    else:
        logging.error(f"Unsupported AI provider: {ai_provider}")
        raise ValueError(f"Unsupported AI provider: {ai_provider}")

def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Create a configuration parser
    config = configparser.ConfigParser()

    # Set default AI configuration values
    set_default_ai_config(config)

    # Optionally, set default model configurations
    set_default_model_configs(config)

    # Specify the path for the configuration (you can modify this as needed)
    config_path = "../config.ini"  # Update to your actual path

    # Retrieve model based on the configuration
    model = get_model_from_config(config, config_path)

    if model:
        logging.info("Model successfully initialized.")
        # You can now use the model for further tasks
    else:
        logging.warning("No model initialized; AI usage is disabled or configuration is invalid.")


if __name__ == "__main__":
    main()