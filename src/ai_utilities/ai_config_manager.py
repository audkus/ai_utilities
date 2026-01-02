"""
ai_config_manager.py

Refactored configuration management using Pydantic models for validation, type safety, and immutability.

This module provides functions for setting up and managing AI-related configurations using
type-safe Pydantic models instead of manual ConfigParser handling.

Key improvements:
- Type validation and conversion
- Immutable configuration once loaded
- Environment variable integration
- Clear validation errors
- Default value handling
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Local application Imports
from .config_models import AIConfig, ModelConfig
from .exceptions import ConfigError
from .rate_limit_fetcher import RateLimitFetcher

logger = logging.getLogger(__name__)


class AIConfigManager:
    """
    Configuration manager using Pydantic models for type-safe configuration.
    
    Provides methods to load, validate, and manage AI configuration with proper
    type safety, validation, and immutability.
    """
    
    def __init__(self, config_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file
            api_key: Optional OpenAI API key for dynamic rate limit fetching
        """
        self.config_path = config_path or "config.ini"
        self._config: Optional[AIConfig] = None
        self._rate_limit_fetcher: Optional[RateLimitFetcher] = None
        
        # Initialize rate limit fetcher if API key is provided
        if api_key:
            # Use 30-day cache to match model checking frequency and conserve API credits
            self._rate_limit_fetcher = RateLimitFetcher(api_key, cache_days=30)
            logger.debug("RateLimitFetcher initialized with 30-day cache")
    
    def load_config(self, config_data: Optional[Dict[str, Any]] = None) -> AIConfig:
        """
        Load configuration from various sources with validation.
        
        Args:
            config_data: Optional configuration data dictionary
            
        Returns:
            Validated AIConfig instance
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            if config_data:
                # Load from provided data
                config = AIConfig(**config_data)
            else:
                # Load from environment and defaults
                config = AIConfig()
            
            self._config = config
            logger.info("AI configuration loaded and validated successfully")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load AI configuration: {str(e)}")
            raise ConfigError(f"Invalid configuration: {str(e)}") from e
    
    def load_from_file(self, file_path: Optional[str] = None) -> AIConfig:
        """
        Load configuration from file with fallback to environment variables.
        
        Args:
            file_path: Optional file path override
            
        Returns:
            Validated AIConfig instance
        """
        path = Path(file_path or self.config_path)
        
        if path.exists():
            try:
                config_parser = configparser.ConfigParser()
                config_parser.read(path)
                
                # Convert to dictionary for Pydantic
                config_dict = self._convert_configparser_to_dict(config_parser)
                
                return self.load_config(config_dict)
                
            except Exception as e:
                logger.warning(f"Failed to load config from {path}: {e}")
                logger.info("Falling back to environment variables and defaults")
        
        # Use environment variables and defaults
        return self.load_config()
    
    def _convert_configparser_to_dict(self, config_parser) -> Dict[str, Any]:
        """Convert ConfigParser to dictionary format for Pydantic."""
        config_dict = {}
        
        # AI section
        if config_parser.has_section('AI'):
            ai_section = config_parser['AI']
            config_dict['use_ai'] = ai_section.getboolean('use_ai', True)
            config_dict['ai_provider'] = ai_section.get('ai_provider', 'openai')
            
            # Only include if explicitly set
            if config_parser.has_option('AI', 'waiting_message'):
                config_dict['waiting_message'] = ai_section.get('waiting_message')
            if config_parser.has_option('AI', 'processing_message'):
                config_dict['processing_message'] = ai_section.get('processing_message')
            
            if config_parser.has_option('AI', 'memory_threshold'):
                try:
                    config_dict['memory_threshold'] = ai_section.getfloat('memory_threshold')
                except ValueError:
                    pass  # Keep default
        
        # OpenAI section
        openai_dict = {}
        if config_parser.has_section('openai'):
            openai_section = config_parser['openai']
            
            if config_parser.has_option('openai', 'model'):
                openai_dict['model'] = openai_section.get('model')
            
            if config_parser.has_option('openai', 'api_key'):
                openai_dict['api_key_env'] = openai_section.get('api_key', 'AI_API_KEY')
            
            if config_parser.has_option('openai', 'base_url'):
                openai_dict['base_url'] = openai_section.get('base_url')
            
            if config_parser.has_option('openai', 'timeout'):
                try:
                    openai_dict['timeout'] = openai_section.getint('timeout')
                except ValueError:
                    pass
            
            if config_parser.has_option('openai', 'temperature'):
                try:
                    openai_dict['temperature'] = openai_section.getfloat('temperature')
                except ValueError:
                    pass
            
            if config_parser.has_option('openai', 'max_tokens'):
                try:
                    max_tokens = openai_section.get('max_tokens')
                    if max_tokens:
                        openai_dict['max_tokens'] = int(max_tokens)
                except ValueError:
                    pass
        
        if openai_dict:
            config_dict['openai'] = openai_dict
        
        # Model sections
        models_dict = {}
        for section_name in config_parser.sections():
            # Skip AI and openai sections, treat everything else as a model
            if section_name not in ['AI', 'openai']:
                try:
                    model_config = {
                        'requests_per_minute': config_parser.getint(section_name, 'requests_per_minute'),
                        'tokens_per_minute': config_parser.getint(section_name, 'tokens_per_minute'),
                        'tokens_per_day': config_parser.getint(section_name, 'tokens_per_day'),
                    }
                    models_dict[section_name] = model_config
                except (ValueError, configparser.NoOptionError):
                    logger.warning(f"Invalid model config for {section_name}, using defaults")
        
        if models_dict:
            config_dict['models'] = models_dict
        
        return config_dict
    
    def save_config(self, config: AIConfig, file_path: Optional[str] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            file_path: Optional file path override
        """
        path = Path(file_path or self.config_path)
        
        try:
            config_parser = configparser.ConfigParser()
            
            # AI section
            config_parser.add_section('AI')
            config_parser.set('AI', 'use_ai', str(config.use_ai).lower())
            config_parser.set('AI', 'ai_provider', config.ai_provider)
            config_parser.set('AI', 'waiting_message', config.waiting_message)
            config_parser.set('AI', 'processing_message', config.processing_message)
            config_parser.set('AI', 'memory_threshold', str(config.memory_threshold))
            
            # OpenAI section
            config_parser.add_section('openai')
            config_parser.set('openai', 'model', config.openai.model)
            config_parser.set('openai', 'api_key', config.openai.api_key_env)
            if config.openai.base_url:
                config_parser.set('openai', 'base_url', config.openai.base_url)
            config_parser.set('openai', 'timeout', str(config.openai.timeout))
            config_parser.set('openai', 'temperature', str(config.openai.temperature))
            if config.openai.max_tokens:
                config_parser.set('openai', 'max_tokens', str(config.openai.max_tokens))
            
            # Model sections
            for model_name, model_config in config.models.items():
                config_parser.add_section(model_name)
                config_parser.set(model_name, 'requests_per_minute', str(model_config.requests_per_minute))
                config_parser.set(model_name, 'tokens_per_minute', str(model_config.tokens_per_minute))
                config_parser.set(model_name, 'tokens_per_day', str(model_config.tokens_per_day))
            
            # Write to file
            with open(path, 'w') as f:
                config_parser.write(f)
            
            logger.info(f"Configuration saved to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {path}: {e}")
            raise ConfigError(f"Failed to save configuration: {str(e)}") from e
    
    @property
    def config(self) -> AIConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            self.load_config()
        return self._config  # type: ignore[return-value]  # _config is set by load_config()
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        return self.config.get_model_config(model_name)
    
    def load_config_with_dynamic_limits(
        self, 
        config_data: Optional[Dict[str, Any]] = None,
        force_refresh_limits: bool = False
    ) -> AIConfig:
        """
        Load configuration with dynamic rate limits from OpenAI API.
        
        Args:
            config_data: Optional configuration data dictionary
            force_refresh_limits: Force refresh rate limits from API
            
        Returns:
            AIConfig instance with dynamic rate limits
        """
        # Load base configuration
        config = self.load_config(config_data)
        
        # Update with dynamic rate limits if available
        if self._rate_limit_fetcher:
            logger.info("Fetching dynamic rate limits from OpenAI API")
            try:
                rate_limits = self._rate_limit_fetcher.get_rate_limits(
                    force_refresh=force_refresh_limits
                )
                
                # Update configuration with dynamic limits
                updated_models = {}
                
                # Start with existing models
                for model_name, model_config in config.models.items():
                    if model_name in rate_limits:
                        # Use dynamic rate limits
                        dynamic_config = rate_limits[model_name].to_model_config()
                        updated_models[model_name] = dynamic_config
                        logger.info(f"Updated {model_name} with dynamic rate limits: "
                                  f"{dynamic_config.requests_per_minute} RPM, "
                                  f"{dynamic_config.tokens_per_minute} TPM")
                    else:
                        # Keep existing configuration
                        updated_models[model_name] = model_config
                
                # Add any new models from rate limits
                for model_name, rate_limit_info in rate_limits.items():
                    if model_name not in updated_models:
                        updated_models[model_name] = rate_limit_info.to_model_config()
                        logger.info(f"Added new model {model_name} with dynamic rate limits")
                
                # Create new configuration with updated models
                config = config.model_copy(update={'models': updated_models})
                
            except Exception as e:
                logger.warning(f"Failed to fetch dynamic rate limits: {e}")
                logger.info("Using default rate limits")
        
        return config
    
    def update_rate_limits(self, force_refresh: bool = False) -> bool:
        """
        Update rate limits with fresh data from OpenAI API.
        
        Args:
            force_refresh: Force refresh from API even if cache is valid
            
        Returns:
            True if rate limits were updated successfully
        """
        if not self._rate_limit_fetcher:
            logger.warning("No API key provided - cannot fetch dynamic rate limits")
            return False
        
        try:
            rate_limits = self._rate_limit_fetcher.get_rate_limits(
                force_refresh=force_refresh
            )
            
            # Load configuration if not already loaded
            if self._config is None:
                self._config = self.load_config()
            
            # Update current configuration
            if self._config:
                updated_models = {}
                
                for model_name, model_config in self._config.models.items():
                    if model_name in rate_limits:
                        updated_models[model_name] = rate_limits[model_name].to_model_config()
                    else:
                        updated_models[model_name] = model_config
                
                # Add new models
                for model_name, rate_limit_info in rate_limits.items():
                    if model_name not in updated_models:
                        updated_models[model_name] = rate_limit_info.to_model_config()
                
                self._config = self._config.model_copy(update={'models': updated_models})
                logger.info("Rate limits updated successfully")
                return True
            
        except Exception as e:
            logger.error(f"Failed to update rate limits: {e}")
        
        return False
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get status of rate limit fetching and caching.
        
        Returns:
            Dictionary with rate limit status information
        """
        if not self._rate_limit_fetcher:
            return {
                "dynamic_limits_enabled": False,
                "reason": "No API key provided"
            }
        
        cache_status = self._rate_limit_fetcher.get_cache_status()
        
        return {
            "dynamic_limits_enabled": True,
            "cache_status": cache_status,
            "available_models": list(self.config.models.keys()) if self._config else []
        }
    
    def clear_rate_limit_cache(self) -> None:
        """Clear the rate limit cache."""
        if self._rate_limit_fetcher:
            self._rate_limit_fetcher.clear_cache()
            logger.info("Rate limit cache cleared")
        else:
            logger.warning("No rate limit fetcher available")
    
    def should_update_rate_limits(self) -> bool:
        """
        Check if rate limits should be updated based on cache age.
        
        Uses the same logic as model checking to determine if updates are needed.
        
        Returns:
            True if rate limits should be updated
        """
        if not self._rate_limit_fetcher:
            return False
        
        cache_status = self._rate_limit_fetcher.get_cache_status()
        
        if not cache_status.get("cached", False):
            return True
        
        cache_age_days = cache_status.get("cache_age_days", 0)
        
        # Update if cache is older than 30 days (same as model checking)
        if cache_age_days >= 30:
            logger.info(f"Rate limit cache is {cache_age_days:.1f} days old, updating")
            return True
        
        logger.debug(f"Rate limit cache is {cache_age_days:.1f} days old, no update needed")
        return False
    
    def update_rate_limits_if_needed(self) -> bool:
        """
        Update rate limits only if needed based on cache age.
        
        Returns:
            True if rate limits were updated
        """
        if self.should_update_rate_limits():
            return self.update_rate_limits(force_refresh=True)
        return False


# Global configuration manager instance
_config_manager: Optional[AIConfigManager] = None


def get_config_manager() -> AIConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = AIConfigManager()
    return _config_manager


def initialize_config_file(config_path: str = "config.ini") -> AIConfig:
    """
    Initialize configuration file with defaults if it doesn't exist.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded AIConfig instance
    """
    manager = AIConfigManager(config_path)
    
    if not Path(config_path).exists():
        # Create default configuration
        config = AIConfig()
        manager.save_config(config, config_path)
        logger.info(f"Created default configuration file at {config_path}")
        return config
    else:
        # Load existing configuration
        return manager.load_from_file(config_path)


def get_model_from_config(config_path: str = "config.ini", model: Optional[str] = None) -> Optional[object]:
    """
    Get AI model instance based on configuration.
    
    Args:
        config_path: Path to configuration file
        model: Optional model name override
        
    Returns:
        OpenAIModel instance or None if AI is disabled
    """
    # Load configuration
    manager = AIConfigManager(config_path)
    config = manager.load_from_file(config_path)
    
    if not config.use_ai:
        logger.info("AI usage is disabled in the configuration.")
        return None
    
    if config.ai_provider != 'openai':
        logger.error(f"Unsupported AI provider: {config.ai_provider}")
        raise ConfigError("Unsupported AI provider")
    
    # Get API key
    api_key = os.getenv(config.openai.api_key_env)
    if not api_key:
        raise ConfigError("API key missing")
    
    # Get model name
    model_name = model or config.openai.model
    if not model_name:
        raise ConfigError("Model name missing")
    
    # Create OpenAIModel (using existing implementation)
    # Convert Pydantic config to ConfigParser format for compatibility

    from .openai_model import OpenAIModel
    compat_config = configparser.ConfigParser()
    
    # Add sections needed by OpenAIModel
    compat_config.add_section('openai')
    compat_config.set('openai', 'model', model_name)
    
    # Add model-specific rate limits
    model_config = config.get_model_config(model_name)
    compat_config.add_section(model_name)
    compat_config.set(model_name, 'requests_per_minute', str(model_config.requests_per_minute))
    compat_config.set(model_name, 'tokens_per_minute', str(model_config.tokens_per_minute))
    compat_config.set(model_name, 'tokens_per_day', str(model_config.tokens_per_day))
    
    logger.debug(f"Initializing OpenAIModel with model: {model_name}")
    return OpenAIModel(api_key=api_key, model=model_name, config=compat_config, config_path=config_path)


def main() -> None:
    """
    Demonstrate Pydantic configuration management.
    """
    logging.basicConfig(level=logging.DEBUG)
    
    # Create configuration with environment variable support
    config = AIConfig()
    print(f"Default model: {config.openai.model}")
    print(f"AI enabled: {config.use_ai}")
    print(f"test-model-1 rate limits: {config.models['test-model-1'].requests_per_minute} RPM")
    
    # Save configuration
    manager = AIConfigManager("demo_config.ini")
    manager.save_config(config)
    print("Configuration saved to demo_config.ini")
    
    # Load configuration
    loaded_config = manager.load_from_file("demo_config.ini")
    print(f"Loaded model: {loaded_config.openai.model}")


if __name__ == "__main__":
    main()
