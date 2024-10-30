"""
ai_config_manager.py

This module provides functions for setting up and managing AI-related configurations within a Python project.
It defines default configurations, validates configuration settings, and retrieves model-specific settings.

Key functionalities include:
- Setting default AI and model-specific configuration values.
- Validating and retrieving AI model settings.
- Handling different AI providers and their respective configurations.

Example usage:
    from ai_config_manager import set_default_ai_config, get_model_from_config

    config = configparser.ConfigParser()
    set_default_ai_config(config)
    model = get_model_from_config(config, config_path)

Executing main in module for test use:
    python -m ai_utilities.ai_config_manager

"""

# Standard Library Imports
import os
import configparser
import logging
from typing import Optional

# Local application Imports
from .error_codes import (
    ERROR_CONFIG_API_KEY_MISSING,
    ERROR_CONFIG_MODEL_NAME_MISSING,
    ERROR_CONFIG_UNSUPPORTED_PROVIDER,
    ERROR_LOGGING_CODE,
)
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


def initialize_config_file(config: configparser.ConfigParser, config_path: str = "config.ini") -> None:
    """
    Initializes the configuration file with default settings if it does not exist.

    Args:
        config (configparser.ConfigParser): The configuration object to update.
        config_path (str): The path to the configuration file.
    """
    # Check if the configuration file exists
    if not os.path.exists(config_path):
        # Set default configurations
        set_default_ai_config(config)
        set_default_model_configs(config)

        # Save to the specified path
        with open(config_path, "w") as config_file:
            config.write(config_file)
        logger.info(f"Created a new configuration file at {config_path}")
    else:
        # Load existing configurations
        config.read(config_path)
        logger.info(f"Loaded configuration from {config_path}")


def set_default_ai_config(config: configparser.ConfigParser) -> None:
    """
    Sets default AI configuration values in the provided ConfigParser object.

    Args:
        config (configparser.ConfigParser): The configuration object to update.

    Returns:
        None
    """
    try:
        if not config.has_section("AI"):
            config.add_section("AI")
        config.set("AI", "use_ai", config.get("AI", "use_ai", fallback="true"))
        config.set("AI", "ai_provider", config.get("AI", "ai_provider", fallback="openai"))
        config.set(
            "AI",
            "waiting_message",
            config.get(
                "AI", "waiting_message",
                fallback="Waiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]"
            )
        )
        config.set(
            "AI", "processing_message",
            config.get(
                "AI", "processing_message",
                fallback="AI response received. Processing..."
            )
        )
        config.set("AI", "memory_threshold", config.get("AI", "memory_threshold", fallback="0.8"))

        if not config.has_section("openai"):
            config.add_section("openai")
        config.set("openai", "model", config.get("openai", "model", fallback="gpt-4"))
        config.set("openai", "api_key", config.get("openai", "api_key", fallback="OPENAI_API_KEY"))

    except configparser.Error as e:
        logger.error(f"ConfigParser Error in set_default_ai_config: {str(e)}")
        raise ConfigError(ERROR_LOGGING_CODE, "Failed to set default AI configuration values.") from e


def set_default_model_configs(config: configparser.ConfigParser) -> None:
    """
    Sets default configuration values for specific AI models, such as 'gpt-4' and 'gpt-3.5-turbo'.

    Args:
        config (configparser.ConfigParser): The configuration object to update.

    Returns:
        None
    """
    try:
        if not config.has_section("gpt-4"):
            config.add_section("gpt-4")
        config.set("gpt-4", "requests_per_minute", config.get("gpt-4", "requests_per_minute", fallback="5000"))
        config.set("gpt-4", "tokens_per_minute", config.get("gpt-4", "tokens_per_minute", fallback="450000"))
        config.set("gpt-4", "tokens_per_day", config.get("gpt-4", "tokens_per_day", fallback="1350000"))

        if not config.has_section("gpt-3.5-turbo"):
            config.add_section("gpt-3.5-turbo")
        config.set(
            "gpt-3.5-turbo", "requests_per_minute",
            config.get("gpt-3.5-turbo", "requests_per_minute", fallback="5000")
        )
        config.set(
            "gpt-3.5-turbo", "tokens_per_minute",
            config.get("gpt-3.5-turbo", "tokens_per_minute", fallback="2000000")
        )
        config.set("gpt-3.5-turbo", "tokens_per_day",
                   config.get("gpt-3.5-turbo", "tokens_per_day", fallback="20000000"))

    except configparser.Error as e:
        logger.error(f"ConfigParser Error in set_default_model_configs: {str(e)}")
        raise ConfigError(ERROR_LOGGING_CODE, "Failed to set default model configuration values.") from e


def get_model_from_config(config: configparser.ConfigParser, config_path: str, model: Optional[str] = None) -> Optional[
    'OpenAIModel']:
    """
    Initializes and returns an OpenAIModel instance based on configuration.

    Args:
        config (configparser.ConfigParser): Configuration object.
        config_path (str): Path to the configuration file.
        model (Optional[str]): Model name override.

    Returns:
        Optional[OpenAIModel]: Initialized OpenAIModel instance or None if not configured.

    Raises:
        ConfigError: For configuration-related issues (e.g., missing API key).
    """
    # Delay import to avoid circular dependencies
    from .openai_model import OpenAIModel

    use_ai = config.getboolean('AI', 'use_ai', fallback=True)
    if not use_ai:
        logger.info("AI usage is disabled in the configuration.")
        return None

    ai_provider = config.get('AI', 'ai_provider')
    if ai_provider != 'openai':
        logger.error(f"Unsupported AI provider: {ai_provider}")
        raise ConfigError(ERROR_CONFIG_UNSUPPORTED_PROVIDER)

    api_key = os.getenv(config.get('openai', 'api_key'))
    if not api_key:
        raise ConfigError(ERROR_CONFIG_API_KEY_MISSING)

    model_name = model or config.get('openai', 'model', fallback=None)
    if not model_name:
        raise ConfigError(ERROR_CONFIG_MODEL_NAME_MISSING)

    logger.debug(f"Initializing OpenAIModel with model: {model_name}")
    return OpenAIModel(api_key=api_key, model=model_name, config=config, config_path=config_path)


def main() -> None:
    """
    Demonstrates usage of AI configuration utilities, setting up and validating AI-related configurations.

    Initializes a configuration object, sets default values, and retrieves an AI model.
    """
    logging.basicConfig(level=logging.DEBUG)
    config = configparser.ConfigParser()

    set_default_ai_config(config)
    set_default_model_configs(config)

    config_path = "../config.ini"  # Update to your actual path
    initialize_config_file(config, config_path)
    model = get_model_from_config(config, config_path)

    if model:
        logger.info("Model successfully initialized.")
    else:
        logger.warning("No model initialized; AI usage is disabled or configuration is invalid.")


if __name__ == "__main__":
    main()
