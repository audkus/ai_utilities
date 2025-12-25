"""
AI Client for v1 API surface.

This module provides the main AiClient class and AiSettings for explicit configuration
without import-time side effects.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
from configparser import ConfigParser
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta

from .providers.openai_provider import OpenAIProvider
from .providers.base_provider import BaseProvider
from .usage_tracker import UsageTracker, ThreadSafeUsageTracker, UsageScope, create_usage_tracker
from .progress_indicator import ProgressIndicator
from .models import AskResult


class AiSettings(BaseSettings):
    """Configuration settings for AI client using pydantic-settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="AI_",
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8'
    )
    
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="test-model-1", description="Default model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for responses (0.0-2.0)")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Max tokens for responses")
    base_url: Optional[str] = Field(default=None, description="Custom base URL for API")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    update_check_days: int = Field(default=30, ge=1, description="Days between update checks")
    
    # Usage tracking settings
    usage_scope: str = Field(default="per_client", description="Usage tracking scope: per_client, per_process, global")
    usage_client_id: Optional[str] = Field(default=None, description="Custom client ID for usage tracking")
    
    def __init__(self, **data):
        """Initialize settings with environment override support."""
        # Check for contextvar overrides and merge with data
        from .env_overrides import get_env_overrides
        
        overrides = get_env_overrides()
        if overrides:
            # Map AI_ environment variables to field names
            for key, value in overrides.items():
                if key.startswith('AI_'):
                    field_name = key[3:].lower()  # Remove AI_ prefix and lowercase
                    # Only use override if not explicitly provided in data
                    if field_name not in data:
                        # Convert string values to appropriate types
                        data[field_name] = self._convert_env_value(field_name, value)
        
        super().__init__(**data)
    
    def _convert_env_value(self, field_name: str, value: str) -> Any:
        """Convert environment variable value to appropriate type for the field."""
        if field_name in ['temperature']:
            return float(value)
        elif field_name in ['max_tokens', 'timeout', 'update_check_days']:
            return int(value)
        elif field_name in ['use_ai']:
            return value.lower() in ('true', '1', 'yes', 'on')
        else:
            return value
    
    @classmethod
    def create_isolated(cls, env_vars: dict = None, **data):
        """Create AiSettings with isolated environment variables (deprecated - use override_env)."""
        from .env_overrides import override_env
        
        with override_env(env_vars):
            settings = cls(**data)
            return settings
    
    def cleanup_env(self):
        """Restore original environment variables (deprecated - no longer needed)."""
        pass  # No-op since we no longer mutate os.environ
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        """Validate that model is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Model cannot be empty")
        return v.strip()
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """API key is required unless explicitly set to None for testing."""
        return v
    
    @classmethod
    def from_ini(cls, path: Union[str, Path]) -> "AiSettings":
        """Load settings from an INI file (explicit loader, not automatic).
        
        Args:
            path: Path to the INI configuration file
            
        Returns:
            AiSettings instance with values from the file
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the config file is malformed
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        config = ConfigParser()
        config.read(config_path)
        
        # Extract values from config
        settings_dict = {}
        if 'openai' in config:
            openai_section = config['openai']
            settings_dict = {
                'api_key': openai_section.get('api_key'),
                'model': openai_section.get('model', 'test-model-1'),
                'temperature': float(openai_section.get('temperature', 0.7)),
                'max_tokens': int(openai_section.get('max_tokens')) if openai_section.get('max_tokens') else None,
                'base_url': openai_section.get('base_url'),
                'timeout': int(openai_section.get('timeout', 30))
            }
        
        return cls(**settings_dict)
    
    @classmethod
    def interactive_setup(cls, force_reconfigure: bool = False) -> "AiSettings":
        """Interactive setup that prompts for missing or reconfigures settings.
        
        Args:
            force_reconfigure: If True, prompts to reconfigure even if API key exists
            
        Returns:
            AiSettings instance with configured values
        """
        print("=== AI Utilities Interactive Setup ===\n")
        
        # Detect operating system
        is_windows = os.name == 'nt'
        
        # Check current environment
        current_api_key = os.getenv("AI_API_KEY")
        current_model = os.getenv("AI_MODEL", "test-model-1")
        current_temperature = os.getenv("AI_TEMPERATURE", "0.7")
        
        # Determine if setup is needed
        needs_setup = not current_api_key or force_reconfigure
        
        if not needs_setup and current_api_key:
            print(f"✓ API key is already configured (model: {current_model}, temperature: {current_temperature})")
            response = input("Do you want to reconfigure? (y/N): ").strip().lower()
            needs_setup = response in ['y', 'yes']
        
        if needs_setup:
            print("\nPlease enter your OpenAI configuration:")
            
            # Prompt for API key with security options
            if not current_api_key or force_reconfigure:
                print("\nFor security, you have several options to provide your API key:")
                print("1. Set environment variable and restart (recommended)")
                print("2. Type directly (less secure - visible in terminal history)")
                print("3. Save to .env file")
                
                choice = input("Choose option (1/2/3): ").strip()
                
                if choice == "1":
                    print(f"\nPlease set your environment variable:")
                    if is_windows:
                        print("  For Windows PowerShell: $env:AI_API_KEY='your-key-here'")
                        print("  For Windows CMD: set AI_API_KEY=your-key-here")
                        print("  (Use only the command that matches your terminal)")
                    else:
                        print("  Linux/Mac: export AI_API_KEY='your-key-here'")
                    print("  Then restart your application")
                    print("\n⚠️  Exiting application. Please restart after setting the environment variable.")
                    import sys
                    sys.exit(1)  # Exit with error code to indicate setup incomplete
                    
                elif choice == "2":
                    print("\n⚠️  Warning: API key will be visible in terminal history")
                    confirm = input("Continue anyway? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        api_key = input("OpenAI API key: ").strip()
                        if api_key:
                            os.environ["AI_API_KEY"] = api_key
                            print("✓ API key set for current session")
                    
                elif choice == "3":
                    api_key = input("OpenAI API key: ").strip()
                    if api_key:
                        os.environ["AI_API_KEY"] = api_key
                        cls._save_to_env_file("AI_API_KEY", api_key)
                        print("✓ API key saved to .env file")
                
                else:
                    print("Invalid choice. Skipping API key configuration.")
            
            # Prompt for model (safe - no security concerns)
            model = input(f"Model [{current_model}]: ").strip() or current_model
            if model != current_model:
                os.environ["AI_MODEL"] = model
                cls._save_to_env_file("AI_MODEL", model)
            
            # Prompt for temperature (safe - no security concerns)
            temp_input = input(f"Temperature [{current_temperature}]: ").strip()
            if temp_input:
                try:
                    temperature = float(temp_input)
                    if 0.0 <= temperature <= 2.0:
                        os.environ["AI_TEMPERATURE"] = str(temperature)
                        cls._save_to_env_file("AI_TEMPERATURE", str(temperature))
                    else:
                        print("⚠ Temperature must be between 0.0 and 2.0, using default")
                except ValueError:
                    print("⚠ Invalid temperature format, using default")
            
            print("\n✓ Configuration complete!")
        
        # Create and return settings
        settings = cls()
        
        # Validate that we have an API key after setup
        if not settings.api_key:
            raise ValueError("API key is required but not configured. Please set AI_API_KEY environment variable or run interactive setup again.")
        
        return settings
    
    @staticmethod
    def _save_to_env_file(key: str, value: str) -> None:
        """Save a key-value pair to .env file."""
        env_file = Path(".env")
        
        # Read existing content
        existing_lines = []
        if env_file.exists():
            existing_lines = env_file.read_text().splitlines()
        
        # Update or add the key
        updated = False
        for i, line in enumerate(existing_lines):
            if line.startswith(f"{key}="):
                existing_lines[i] = f"{key}={value}"
                updated = True
                break
        
        if not updated:
            existing_lines.append(f"{key}={value}")
        
        # Write back to file
        env_file.write_text("\n".join(existing_lines) + "\n")
        print(f"✓ Saved {key} to .env file")
    
    @classmethod
    def reconfigure(cls) -> "AiSettings":
        """Force reconfiguration of settings."""
        return cls.interactive_setup(force_reconfigure=True)
    
    @classmethod
    def validate_model_availability(cls, api_key: str, model: str) -> bool:
        """Check if a model is available in the OpenAI API.
        
        Args:
            api_key: OpenAI API key
            model: Model name to validate
            
        Returns:
            True if model is available, False otherwise
        """
        if not api_key or not model:
            return False
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            models = client.models.list()
            available_models = {model.id for model in models.data}
            return model in available_models
        except Exception:
            # If we can't validate, assume it might work
            # This prevents breaking during network issues
            return True

    @classmethod
    def check_for_updates(cls, api_key: str, check_interval_days: int = 30) -> Dict[str, Any]:
        """Check for new OpenAI models with configurable interval.
        
        Args:
            api_key: OpenAI API key for making the request
            check_interval_days: Days to wait between checks (default from settings)
            
        Returns:
            Dictionary with update information including new models and current models
        """
        cache_file = Path.home() / ".ai_utilities_model_cache.json"
        
        # Check if we've checked recently within the configured interval
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                last_check = datetime.fromisoformat(cache_data.get('last_check', '1970-01-01'))
                if datetime.now() - last_check < timedelta(days=check_interval_days):
                    # We checked recently, return cached result
                    return {
                        'has_updates': cache_data.get('has_updates', False),
                        'new_models': cache_data.get('new_models', []),
                        'current_models': cache_data.get('current_models', []),
                        'total_models': cache_data.get('total_models', 0),
                        'last_check': cache_data.get('last_check'),
                        'cached': True
                    }
            except (json.JSONDecodeError, ValueError, KeyError):
                pass  # Cache corrupted, will check again
        
        # Perform actual model check (costs tokens!)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Get available models
            models = client.models.list()
            model_names = {model.id for model in models.data}
            
            # Use historical models as baseline for comparison
            # This list only needs to include models that existed at time of implementation
            baseline_models = {
                'test-model-1', 'test-model-3', 'test-model-5',
                'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
                'gpt-3.5-turbo-instruct', 'text-davinci-003',
                'text-curie-001', 'text-babbage-001', 'text-ada-001'
            }
            
            # Check for new models (models not in baseline)
            new_models = sorted(list(model_names - baseline_models))
            current_models = sorted(list(model_names))
            has_updates = len(new_models) > 0
            
            # Cache the result
            cache_data = {
                'last_check': datetime.now().isoformat(),
                'has_updates': has_updates,
                'new_models': new_models,
                'current_models': current_models,
                'total_models': len(model_names)
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return {
                'has_updates': has_updates,
                'new_models': new_models,
                'current_models': current_models,
                'total_models': len(model_names),
                'last_check': cache_data['last_check'],
                'cached': False
            }
            
        except Exception as e:
            # If API call fails, don't cache and return error info
            return {
                'has_updates': False,
                'new_models': [],
                'current_models': [],
                'total_models': 0,
                'error': str(e),
                'cached': False
            }
    
    @classmethod
    def smart_setup(cls, api_key: Optional[str] = None, force_check: bool = False, 
                   check_interval_days: Optional[int] = None) -> "AiSettings":
        """Smart setup that checks for missing API key or new models.
        
        Args:
            api_key: Optional API key to use for model checking
            force_check: Force check for new models even if recently checked
            check_interval_days: Override default check interval
            
        Returns:
            AiSettings instance with configured values
        """
        current_api_key = api_key or os.getenv("AI_API_KEY")
        
        # Always prompt if API key is missing
        if not current_api_key:
            return cls.interactive_setup()
        
        # Get check interval from settings or parameter
        settings = cls()
        interval = check_interval_days or settings.update_check_days
        
        # Check for new models if we have an API key
        if force_check or cls._should_check_for_updates(interval):
            print("=== Checking for OpenAI Updates ===")
            
            update_info = cls.check_for_updates(current_api_key, interval)
            
            if 'error' in update_info:
                print(f"⚠️ Could not check for updates: {update_info['error']}")
            elif update_info['has_updates']:
                print(f"🆕 New OpenAI models detected!")
                print(f"📊 Total models available: {update_info['total_models']}")
                
                if update_info['new_models']:
                    print(f"\n🆕 NEW MODELS ({len(update_info['new_models'])}):")
                    for model in update_info['new_models']:
                        print(f"   • {model}")
                
                # Show current models (truncated if too many)
                current_models = update_info['current_models']
                print(f"\n📋 CURRENT MODELS ({len(current_models)}):")
                
                # Show first 10 models, then indicate if there are more
                display_models = current_models[:10]
                for model in display_models:
                    print(f"   • {model}")
                
                if len(current_models) > 10:
                    print(f"   ... and {len(current_models) - 10} more models")
                
                if update_info.get('cached'):
                    print(f"\n💾 Using cached results from {update_info['last_check']}")
                else:
                    print(f"\n🔄 Fresh check completed at {update_info['last_check']}")
                
                response = input("\nWould you like to review your configuration? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    return cls.interactive_setup(force_reconfigure=True)
            else:
                print(f"✓ Your configuration is up to date")
                print(f"📊 Total models available: {update_info['total_models']}")
                if update_info.get('cached'):
                    print(f"💾 Using cached results from {update_info['last_check']}")
        
        # Return settings without prompting
        return cls()
    
    @staticmethod
    def _should_check_for_updates(check_interval_days: int = 30) -> bool:
        """Check if enough time has passed to check for updates.
        
        Args:
            check_interval_days: Days to wait between checks
            
        Returns:
            True if should check for updates
        """
        cache_file = Path.home() / ".ai_utilities_model_cache.json"
        
        if not cache_file.exists():
            return True
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            last_check = datetime.fromisoformat(cache_data.get('last_check', '1970-01-01'))
            return datetime.now() - last_check >= timedelta(days=check_interval_days)
        except (json.JSONDecodeError, ValueError, KeyError):
            return True


class AiClient:
    """Main AI client for making requests to AI models."""
    
    def __init__(self, settings: Optional[AiSettings] = None, provider: Optional[BaseProvider] = None, 
                 track_usage: bool = False, usage_file: Optional[Path] = None, 
                 show_progress: bool = True, auto_setup: bool = True, smart_setup: bool = False):
        """Initialize AI client with explicit settings.
        
        Args:
            settings: AI settings containing api_key, model, temperature, etc.
            provider: Custom AI provider (defaults to OpenAI)
            track_usage: Whether to track usage statistics
            usage_file: Custom file for usage tracking
            show_progress: Whether to show progress indicator during requests
            auto_setup: Whether to automatically prompt for setup if API key is missing
            smart_setup: Whether to use smart setup (checks for new models daily)
        """
        if settings is None:
            if smart_setup:
                # Use smart setup (checks for missing API key + new models)
                settings = AiSettings.smart_setup()
            elif auto_setup:
                # Use basic interactive setup (only if API key missing)
                settings = AiSettings.interactive_setup()
            else:
                settings = AiSettings()
        
        self.settings = settings
        self.provider = provider or OpenAIProvider(settings)
        
        # Initialize thread-safe usage tracker with configurable scope
        if track_usage:
            scope = UsageScope(settings.usage_scope)
            self.usage_tracker = create_usage_tracker(
                scope=scope,
                stats_file=usage_file,
                client_id=settings.usage_client_id
            )
        else:
            self.usage_tracker = None
            
        self.show_progress = show_progress
    
    def check_for_updates(self, force_check: bool = False) -> Dict[str, Any]:
        """Manually check for OpenAI model updates with detailed information.
        
        Args:
            force_check: Force check even if recently checked
            
        Returns:
            Dictionary with detailed update information
        """
        if not self.settings.api_key:
            print("⚠️ Cannot check for updates: API key not configured")
            return {'error': 'API key not configured'}
        
        print("=== Checking for OpenAI Updates ===")
        
        # Use force_check to bypass caching
        if force_check:
            return AiSettings.check_for_updates(self.settings.api_key, check_interval_days=0)
        else:
            return AiSettings.check_for_updates(self.settings.api_key, self.settings.update_check_days)
    
    def reconfigure(self) -> None:
        """Manually trigger reconfiguration of settings."""
        print("=== Reconfiguring AI Settings ===")
        self.settings = AiSettings.interactive_setup(force_reconfigure=True)
        # Update provider with new settings
        self.provider = OpenAIProvider(self.settings)
    
    def ask(self, prompt: Union[str, List[str]], *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, List[str]]:
        """Ask a question or multiple questions to the AI.
        
        Args:
            prompt: Single prompt string or list of prompts
            return_format: Format for response ("text" or "json")
            **kwargs: Additional parameters to override settings
            
        Returns:
            Response string or list of strings
        """
        # Merge kwargs with settings
        request_params = self.settings.model_dump(exclude_none=True)
        request_params.update(kwargs)
        
        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)
        
        with progress:
            # Use new provider interface
            if isinstance(prompt, list):
                response = self.provider.ask_many(prompt, return_format=return_format, **request_params)
            else:
                response = self.provider.ask(prompt, return_format=return_format, **request_params)
        
        # Track usage if enabled (basic estimation - provider could return actual counts)
        if self.usage_tracker:
            # This is a rough estimate - actual token counting would need provider support
            estimated_tokens = len(str(response)) // 4  # Rough estimate
            self.usage_tracker.record_usage(estimated_tokens)
        
        return response
    
    def get_usage_stats(self):
        """Get current usage statistics if tracking is enabled.
        
        Returns:
            UsageStats object if tracking enabled, None otherwise
        """
        if self.usage_tracker:
            return self.usage_tracker.get_stats()
        return None
    
    def print_usage_summary(self):
        """Print usage summary if tracking is enabled."""
        if self.usage_tracker:
            self.usage_tracker.print_summary()
        else:
            print("Usage tracking is not enabled.")
    
    def ask_many(
        self,
        prompts: Sequence[str],
        *,
        return_format: Literal["text", "json"] = "text",
        concurrency: int = 1,
        fail_fast: bool = False,
        **kwargs
    ) -> List[AskResult]:
        """Ask multiple questions sequentially.
        
        Args:
            prompts: List of prompts to process
            return_format: Format for responses ("text" or "json")
            concurrency: Number of concurrent requests (must be >= 1)
            fail_fast: If True, stop processing after first failure
            **kwargs: Additional parameters
            
        Returns:
            List of AskResult objects
        """
        from .models import AskResult
        
        # Validate concurrency
        if concurrency <= 0:
            raise ValueError("concurrency must be >= 1")
        
        results = []
        
        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)
        
        with progress:
            for i, prompt in enumerate(prompts):
                start_time = time.time()
                
                try:
                    response = self.provider.ask(prompt, return_format=return_format, **kwargs)
                    duration = time.time() - start_time
                    
                    result = AskResult(
                        prompt=prompt,
                        response=response,
                        error=None,
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None  # Would need provider support
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    result = AskResult(
                        prompt=prompt,
                        response=None,
                        error=str(e),
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None
                    )
                    
                    results.append(result)  # Add the failed result first
                    
                    # If fail_fast is enabled, mark remaining prompts as failed
                    if fail_fast:
                        # Mark remaining prompts as cancelled/failed
                        for remaining_prompt in prompts[i+1:]:
                            cancelled_result = AskResult(
                                prompt=remaining_prompt,
                                response=None,
                                error="Cancelled due to fail_fast mode",
                                duration_s=0.0,
                                model=self.settings.model,
                                tokens_used=None
                            )
                            results.append(cancelled_result)
                        break
        
        return results
    
    def ask_many_with_retry(
        self,
        prompts: Sequence[str],
        *,
        return_format: Literal["text", "json"] = "text",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> List[AskResult]:
        """Ask multiple questions with retry logic.
        
        Args:
            prompts: List of prompts to process
            return_format: Format for responses ("text" or "json")
            max_retries: Maximum number of retries per prompt
            retry_delay: Delay between retries in seconds
            **kwargs: Additional parameters
            
        Returns:
            List of AskResult objects
        """
        from .models import AskResult
        import time
        
        results = []
        
        for prompt in prompts:
            start_time = time.time()
            last_error = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    response = self.provider.ask(prompt, return_format=return_format, **kwargs)
                    duration = time.time() - start_time
                    
                    result = AskResult(
                        prompt=prompt,
                        response=response,
                        error=None,
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None
                    )
                    break
                    
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    else:
                        duration = time.time() - start_time
                        result = AskResult(
                            prompt=prompt,
                            response=None,
                            error=str(e),
                            duration_s=duration,
                            model=self.settings.model,
                            tokens_used=None
                        )
            
            results.append(result)
        
        return results
    
    def ask_json(self, prompt: str, **kwargs) -> str:
        """Ask a question and return JSON format response.
        
        Args:
            prompt: Prompt to process
            **kwargs: Additional parameters to override settings
            
        Returns:
            JSON format response string
        """
        return self.ask(prompt, return_format="json", **kwargs)


# Convenience function for backward compatibility
def create_client(api_key: Optional[str] = None, model: str = "test-model-1", **kwargs) -> AiClient:
    """Create an AI client with common parameters.
    
    Args:
        api_key: OpenAI API key
        model: Model to use
        **kwargs: Additional settings
        
    Returns:
        Configured AiClient instance
    """
    settings = AiSettings(api_key=api_key, model=model, **kwargs)
    return AiClient(settings)
