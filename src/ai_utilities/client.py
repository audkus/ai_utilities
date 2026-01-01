"""
AI Client for v1 API surface.

This module provides the main AiClient class and AiSettings for explicit configuration
without import-time side effects.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union, TypeVar, Type
from configparser import ConfigParser
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta

from .providers.openai_provider import OpenAIProvider
from .providers.base_provider import BaseProvider
from .usage_tracker import UsageScope, create_usage_tracker
from .progress_indicator import ProgressIndicator
from .models import AskResult
from .json_parsing import parse_json_from_text, JsonParseError, create_repair_prompt
from .file_models import UploadedFile
from .providers.provider_exceptions import FileTransferError, ProviderCapabilityError
from pydantic import ValidationError

# Generic type for typed responses
T = TypeVar('T', bound=BaseModel)


class AiSettings(BaseSettings):
    """
    Configuration settings for AI client using pydantic-settings.
    
    This class manages all configuration for AI clients including API keys,
    model selection, provider selection, and behavior settings. It supports environment variables
    with the 'AI_' prefix and can be configured programmatically.
    
    Environment Variables:
        AI_API_KEY: API key (required for OpenAI, optional for local providers)
        AI_PROVIDER: Provider type ("openai" | "openai_compatible") (default: "openai")
        AI_MODEL: Model name (default: "test-model-1")
        AI_TEMPERATURE: Response temperature 0.0-2.0 (default: 0.7)
        AI_MAX_TOKENS: Maximum response tokens (optional)
        AI_BASE_URL: Custom API base URL (required for openai_compatible provider)
        AI_TIMEOUT: Request timeout in seconds (default: 30)
        AI_REQUEST_TIMEOUT_S: Request timeout in seconds as float (alias for timeout)
        AI_EXTRA_HEADERS: Extra headers as JSON string (optional)
        AI_UPDATE_CHECK_DAYS: Days between update checks (default: 30)
        AI_USAGE_SCOPE: Usage tracking scope (default: "per_client")
        AI_USAGE_CLIENT_ID: Custom client ID for usage tracking (optional)
    
    Example:
        # Using environment variables (OpenAI default)
        settings = AiSettings()
        
        # Using explicit parameters (OpenAI)
        settings = AiSettings(
            provider="openai",
            api_key="your-key",
            model="gpt-4",
            temperature=0.5
        )
        
        # Using local OpenAI-compatible server
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:11434/v1",  # Ollama
            api_key="dummy-key"  # Optional for local servers
        )
        
        # From configuration file
        settings = AiSettings.from_ini("config.ini")
    """
    
    model_config = SettingsConfigDict(
        env_prefix="AI_",
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    # Provider selection - expanded to support multiple providers
    provider: Optional[Literal["openai", "groq", "together", "openrouter", "ollama", "lmstudio", "text-generation-webui", "fastchat", "openai_compatible"]] = Field(
        default=None, 
        description="AI provider to use (inferred from base_url if not specified)"
    )
    
    # Core settings
    api_key: Optional[str] = Field(default=None, description="Generic API key override (AI_API_KEY)")
    
    # Vendor-specific API keys (no prefix - read directly from env)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key (OPENAI_API_KEY)")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key (GROQ_API_KEY)")
    together_api_key: Optional[str] = Field(default=None, description="Together AI API key (TOGETHER_API_KEY)")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key (OPENROUTER_API_KEY)")
    
    # Local provider keys (optional)
    ollama_api_key: Optional[str] = Field(default=None, description="Ollama API key (OLLAMA_API_KEY)")
    lmstudio_api_key: Optional[str] = Field(default=None, description="LM Studio API key (LMSTUDIO_API_KEY)")
    
    model: str = Field(default="test-model-1", description="Default model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for responses (0.0-2.0)")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Max tokens for responses")
    base_url: Optional[str] = Field(default=None, description="Custom base URL for API (required for openai_compatible)")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    request_timeout_s: Optional[float] = Field(default=None, ge=0.1, description="Request timeout in seconds (float, overrides timeout)")
    extra_headers: Optional[Dict[str, str]] = Field(default=None, description="Extra headers for requests")
    
    # Legacy settings
    update_check_days: int = Field(default=30, ge=1, description="Days between update checks")
    
    # Usage tracking settings
    usage_scope: str = Field(default="per_client", description="Usage tracking scope: per_client, per_process, global")
    usage_client_id: Optional[str] = Field(default=None, description="Custom client ID for usage tracking")
    
    @field_validator('openai_api_key', mode='before')
    @classmethod
    def get_openai_key(cls, v):
        """Get OpenAI API key from environment."""
        if v is not None:
            return v
        return os.getenv('OPENAI_API_KEY')
    
    @field_validator('groq_api_key', mode='before')
    @classmethod
    def get_groq_key(cls, v):
        """Get Groq API key from environment."""
        if v is not None:
            return v
        return os.getenv('GROQ_API_KEY')
    
    @field_validator('together_api_key', mode='before')
    @classmethod
    def get_together_key(cls, v):
        """Get Together API key from environment."""
        if v is not None:
            return v
        return os.getenv('TOGETHER_API_KEY')
    
    @field_validator('openrouter_api_key', mode='before')
    @classmethod
    def get_openrouter_key(cls, v):
        """Get OpenRouter API key from environment."""
        if v is not None:
            return v
        return os.getenv('OPENROUTER_API_KEY')
    
    @field_validator('ollama_api_key', mode='before')
    @classmethod
    def get_ollama_key(cls, v):
        """Get Ollama API key from environment."""
        if v is not None:
            return v
        return os.getenv('OLLAMA_API_KEY')
    
    @field_validator('lmstudio_api_key', mode='before')
    @classmethod
    def get_lmstudio_key(cls, v):
        """Get LM Studio API key from environment."""
        if v is not None:
            return v
        return os.getenv('LMSTUDIO_API_KEY')
    
    def __init__(self, **data):
        """Initialize settings with environment override support."""
        # Tests should be isolated from developer machine .env files.
        # Pytest sets PYTEST_CURRENT_TEST; when present, avoid implicit env_file loading
        # unless the caller explicitly provides _env_file.
        if "PYTEST_CURRENT_TEST" in os.environ and "_env_file" not in data:
            project_root = Path(__file__).resolve().parents[2]
            cwd = Path.cwd().resolve()
            if cwd == project_root:
                data["_env_file"] = None

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
        if field_name in ['temperature', 'request_timeout_s']:
            return float(value)
        elif field_name in ['max_tokens', 'timeout', 'update_check_days']:
            return int(value)
        elif field_name in ['use_ai']:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif field_name == 'extra_headers':
            # Parse JSON string for extra_headers
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON for AI_EXTRA_HEADERS: {value}")
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
    """
    Main AI client for making requests to AI models.
    
    This is the primary interface for interacting with AI models. It provides
    a simple, clean API for both single and batch requests with support for
    different response formats, usage tracking, and progress indication.
    
    The client follows a provider architecture, defaulting to OpenAI but
    supporting custom providers through the BaseProvider interface.
    
    Example:
        # Using environment variables
        client = AiClient()
        response = client.ask("What is the capital of France?")
        
        # Using explicit settings
        settings = AiSettings(api_key="your-key", model="gpt-4")
        client = AiClient(settings)
        
        # Batch requests
        prompts = ["Q1", "Q2", "Q3"]
        results = client.ask_many(prompts)
        
        # JSON responses
        data = client.ask_json("List 5 AI trends as JSON")
    
    Features:
        - Single and batch AI requests
        - Text and JSON response formats
        - Optional usage tracking
        - Progress indication
        - Provider abstraction
        - Environment-based configuration
        - Interactive setup for missing API keys
    """
    
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
        
        # Create provider using factory
        from .providers.provider_factory import create_provider
        self.provider = create_provider(settings, provider)
        
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
        """
        Ask a question or multiple questions to the AI.
        
        This is the primary method for making AI requests. It supports both single
        prompts and batch prompts, with options for text or JSON response formats.
        
        Args:
            prompt: Single prompt string or list of prompts. If a list is provided,
                   returns a list of responses in the same order.
            return_format: Format for response:
                          - "text": Returns plain text responses (default)
                          - "json": Returns parsed JSON as dict/list
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens
                     - timeout: Override request timeout
        
        Returns:
            Union[str, List[str], dict, list]: Response in requested format.
                                              Single prompt returns single response,
                                              list of prompts returns list of responses.
        
        Example:
            client = AiClient()
            
            # Single question
            answer = client.ask("What is the capital of France?")
            
            # JSON response
            data = client.ask("List 5 colors", return_format="json")
            
            # Multiple questions
            questions = ["Q1", "Q2", "Q3"]
            answers = client.ask(questions)
            
            # With custom parameters
            response = client.ask("Explain AI", temperature=0.3, model="gpt-4")
        """
        # Merge kwargs with settings, excluding internal fields
        request_params = self.settings.model_dump(
            exclude_none=True,
            exclude={
                'api_key',  # Providers already have this from initialization
                'provider',  # Not a per-request param
                'base_url',  # Not a per-request param
                'timeout',  # Provider init config, not a per-request param
                'request_timeout_s',  # Provider init config, not a per-request param
                'extra_headers',  # Provider init config, not a per-request param
                'usage_scope',  # Internal usage tracking field
                'usage_client_id',  # Internal usage tracking field
                'update_check_days'  # Internal configuration field
            }
        )
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
        """
        Ask multiple questions with optional concurrency control.
        
        Processes multiple prompts efficiently with support for concurrent execution
        and detailed result information including timing and error handling.
        
        Args:
            prompts: List of prompts to process
            return_format: Format for responses:
                          - "text": Returns plain text responses (default)
                          - "json": Returns parsed JSON as dict/list
            concurrency: Number of concurrent requests (must be >= 1).
                        Higher values can improve performance but use more API quota.
            fail_fast: If True, stops processing after first failure.
                      If False, continues processing all prompts.
            **kwargs: Additional parameters to override settings for all requests
        
        Returns:
            List[AskResult]: List of results containing:
                           - response: The AI response (or None if error)
                           - error: Error message if request failed (or None)
                           - duration_s: Request duration in seconds
                           - prompt: Original prompt (for reference)
        
        Example:
            client = AiClient()
            
            # Sequential processing
            prompts = ["What is 2+2?", "What is 3+3?", "What is 4+4?"]
            results = client.ask_many(prompts)
            
            # Concurrent processing (faster for many requests)
            results = client.ask_many(prompts, concurrency=3)
            
            # Process results
            for result in results:
                if result.error:
                    print(f"Error: {result.error}")
                else:
                    print(f"Answer: {result.response}")
                    print(f" took {result.duration_s:.2f}s")
            
            # Fail fast on first error
            results = client.ask_many(prompts, fail_fast=True)
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
                    # Merge kwargs with settings, excluding internal fields (same as ask method)
                    request_params = self.settings.model_dump(
                        exclude_none=True,
                        exclude={
                            'api_key',  # Providers already have this from initialization
                            'usage_scope',  # Internal usage tracking field
                            'usage_client_id',  # Internal usage tracking field
                            'update_check_days'  # Internal configuration field
                        }
                    )
                    request_params.update(kwargs)
                    
                    response = self.provider.ask(prompt, return_format=return_format, **request_params)
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
            # Initialize error tracking (currently not used but kept for potential debugging)
            _ = None  # Placeholder for last_error
            
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
                    # Store last error for potential debugging (though not currently used)
                    _ = e  # Mark as intentionally unused
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
    
    def ask_json(self, prompt: str, *, max_repairs: int = 1, **kwargs) -> Union[dict, list]:
        """
        Ask a question and return JSON format response with robust parsing.
        
        This method requests text responses and parses JSON from them, with automatic
        repair attempts if parsing fails. It handles common issues like code fences,
        extra prose, and minor syntax errors.
        
        Args:
            prompt: Prompt to process. Should ask for structured/JSON data.
            max_repairs: Maximum number of repair attempts if JSON parsing fails (default: 1)
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens
        
        Returns:
            Union[dict, list]: Parsed JSON response. For simple JSON objects
                              returns dict, for arrays returns list.
        
        Raises:
            JsonParseError: If valid JSON cannot be parsed after all repair attempts.
        
        Example:
            client = AiClient()
            
            # Get structured data
            colors = client.ask_json("List 5 primary colors as JSON array")
            # Returns: ["red", "blue", "green", "yellow", "orange"]
            
            # Get structured object
            info = client.ask_json("Information about Python as JSON with keys: name, creator, year")
            # Returns: {"name": "Python", "creator": "Guido van Rossum", "year": 1991}
            
            # With custom parameters
            data = client.ask_json("API endpoints as JSON", temperature=0.1, max_repairs=2)
        """
        # Get request params (excluding internal fields)
        request_params = self.settings.model_dump(
            exclude_none=True,
            exclude={
                'api_key',
                'provider',
                'base_url',
                'timeout',
                'request_timeout_s',
                'extra_headers',
                'usage_scope', 
                'usage_client_id',
                'update_check_days'
            }
        )
        request_params.update(kwargs)
        
        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)
        
        with progress:
            # First attempt
            try:
                response_text = self.provider.ask_text(prompt, **request_params)
                return parse_json_from_text(response_text)
            except JsonParseError as e:
                if max_repairs <= 0:
                    raise e
                
                # Repair attempts
                last_response = response_text
                last_error = str(e)
                
                for attempt in range(max_repairs):
                    try:
                        repair_prompt = create_repair_prompt(prompt, last_response, last_error)
                        response_text = self.provider.ask_text(repair_prompt, **request_params)
                        return parse_json_from_text(response_text)
                    except JsonParseError as repair_error:
                        last_response = response_text
                        last_error = str(repair_error)
                        continue
                
                # All repair attempts failed
                raise JsonParseError(
                    f"Failed to parse JSON after {max_repairs + 1} attempts. Last error: {last_error}",
                    last_response,
                    original_error=e.original_error
                )
    
    def ask_typed(self, prompt: str, response_model: Type[T], *, max_repairs: int = 1, **kwargs) -> T:
        """
        Ask a question and return a typed Pydantic model instance.
        
        This method combines JSON parsing with Pydantic validation to return
        strongly-typed responses. It handles JSON parsing errors and schema
        validation errors appropriately.
        
        Args:
            prompt: Prompt to process. Should ask for data matching the response_model schema.
            response_model: Pydantic model class to validate and parse the response into.
            max_repairs: Maximum number of repair attempts if JSON parsing fails (default: 1)
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens
        
        Returns:
            T: Instance of the response_model with validated data.
        
        Raises:
            JsonParseError: If valid JSON cannot be parsed after all repair attempts.
            ValidationError: If JSON parses successfully but doesn't match the response_model schema.
        
        Example:
            from pydantic import BaseModel
            
            class Person(BaseModel):
                name: str
                age: int
                email: Optional[str] = None
            
            client = AiClient()
            person = client.ask_typed(
                "Create a person named Alice, age 30", 
                response_model=Person
            )
            # Returns: Person(name="Alice", age=30, email=None)
            
            # With custom parameters
            person = client.ask_typed(
                "Create a person named Bob", 
                response_model=Person,
                max_repairs=2,
                temperature=0.1
            )
        """
        # Get JSON data using ask_json
        json_data = self.ask_json(prompt, max_repairs=max_repairs, **kwargs)
        
        # Validate with Pydantic model
        try:
            return response_model.model_validate(json_data)
        except ValidationError as e:
            # Re-raise ValidationError without swallowing it
            raise e
    
    def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> UploadedFile:
        """Upload a file to the AI provider.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
            
        Raises:
            ValueError: If file path is invalid
            FileTransferError: If upload fails
            ProviderCapabilityError: If provider doesn't support file uploads
            
        Example:
            >>> file = client.upload_file("document.pdf", purpose="assistants")
            >>> print(f"Uploaded: {file.file_id}")
        """
        # Validate input
        if not isinstance(path, Path):
            path = Path(path)
        
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Delegate to provider
        try:
            return self.provider.upload_file(path, purpose=purpose, filename=filename, mime_type=mime_type)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("upload", self.provider.__class__.__name__, e) from e
    
    def download_file(self, file_id: str, *, to_path: Optional[Path] = None) -> Union[bytes, Path]:
        """Download file content from the AI provider.
        
        Args:
            file_id: ID of the file to download
            to_path: Optional path to save the file (returns bytes if None)
            
        Returns:
            File content as bytes if to_path is None, or Path to saved file
            
        Raises:
            ValueError: If file_id is invalid
            FileTransferError: If download fails
            ProviderCapabilityError: If provider doesn't support file downloads
            
        Example:
            >>> # Download as bytes
            >>> content = client.download_file("file-123")
            >>> 
            >>> # Download to file
            >>> path = client.download_file("file-123", to_path="downloaded.pdf")
        """
        if not file_id:
            raise ValueError("file_id cannot be empty")
        
        # Delegate to provider
        try:
            content = self.provider.download_file(file_id)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("download", self.provider.__class__.__name__, e) from e
        
        # Handle saving to file if requested
        if to_path is not None:
            if not isinstance(to_path, Path):
                to_path = Path(to_path)
            
            # Create parent directories if needed
            to_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(to_path, "wb") as f:
                f.write(content)
            
            return to_path
        
        # Return raw bytes
        return content
    
    def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Generate images using AI.
        
        Args:
            prompt: Description of the image to generate
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")
            n: Number of images to generate (1-10)
            
        Returns:
            List of image URLs
            
        Raises:
            ValueError: If prompt is invalid
            FileTransferError: If image generation fails
            ProviderCapabilityError: If provider doesn't support image generation
            
        Example:
            >>> # Generate a single image
            >>> urls = client.generate_image("A cute dog playing fetch")
            >>> 
            >>> # Generate multiple high-quality images
            >>> urls = client.generate_image(
            ...     "A majestic lion in the savanna", 
            ...     size="1792x1024", 
            ...     quality="hd", 
            ...     n=3
            ... )
        """
        if not prompt:
            raise ValueError("prompt cannot be empty")
        
        if n < 1 or n > 10:
            raise ValueError("n must be between 1 and 10")
        
        # Delegate to provider
        try:
            return self.provider.generate_image(prompt, size=size, quality=quality, n=n)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("image generation", self.provider.__class__.__name__, e) from e

    def transcribe_audio(
        self,
        audio_file: Union[str, Path],
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text using AI models.
        
        Args:
            audio_file: Path to audio file to transcribe
            language: Optional language code (e.g., 'en', 'es')
            model: Transcription model to use (default: 'whisper-1')
            prompt: Optional prompt to guide transcription
            temperature: Sampling temperature (0.0 to 1.0)
            response_format: Response format ('json', 'text', 'srt', 'verbose_json', 'vtt')
            
        Returns:
            Dictionary containing transcription results
            
        Raises:
            FileTransferError: If transcription fails
            
        Example:
            result = client.transcribe_audio("recording.wav")
            print(result["text"])
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor
            
            # Create audio processor with this client
            processor = AudioProcessor(client=self)
            
            # Perform transcription
            result = processor.transcribe_audio(
                audio_file=audio_file,
                language=language,
                model=model,
                prompt=prompt,
                temperature=temperature,
                response_format=response_format
            )
            
            # Convert to dictionary for API consistency
            return {
                "text": result.text,
                "language": result.language,
                "duration_seconds": result.duration_seconds,
                "model_used": result.model_used,
                "processing_time_seconds": result.processing_time_seconds,
                "word_count": result.word_count,
                "character_count": result.character_count,
                "segments": [
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                        "confidence": seg.confidence
                    }
                    for seg in (result.segments or [])
                ],
                "metadata": result.metadata
            }
            
        except Exception as e:
            raise FileTransferError("audio transcription", self.provider.__class__.__name__, e) from e

    def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0,
        response_format: str = "mp3"
    ) -> bytes:
        """
        Generate audio from text using text-to-speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for generation (default: 'alloy')
            model: Text-to-speech model (default: 'tts-1')
            speed: Speech speed factor (0.25 to 4.0)
            response_format: Output audio format ('mp3', 'wav', 'flac', 'ogg', 'webm')
            
        Returns:
            Generated audio data as bytes
            
        Raises:
            FileTransferError: If audio generation fails
            
        Example:
            audio_data = client.generate_audio("Hello, world!", voice="nova")
            with open("output.mp3", "wb") as f:
                f.write(audio_data)
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor
            from .audio.audio_models import AudioFormat
            
            # Create audio processor with this client
            processor = AudioProcessor(client=self)
            
            # Convert string format to enum
            format_map = {
                "mp3": AudioFormat.MP3,
                "wav": AudioFormat.WAV,
                "flac": AudioFormat.FLAC,
                "ogg": AudioFormat.OGG,
                "webm": AudioFormat.WEBM
            }
            
            if response_format not in format_map:
                raise ValueError(f"Invalid audio format: {response_format}")
            
            # Perform generation
            result = processor.generate_audio(
                text=text,
                voice=voice,
                model=model,
                speed=speed,
                response_format=format_map[response_format]
            )
            
            return result.audio_data
            
        except Exception as e:
            raise FileTransferError("audio generation", self.provider.__class__.__name__, e) from e

    def get_audio_voices(self) -> List[Dict[str, str]]:
        """
        Get list of available voices for audio generation.
        
        Returns:
            List of voice information dictionaries
            
        Raises:
            FileTransferError: If voice retrieval fails
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor
            
            processor = AudioProcessor(client=self)
            voices_info = processor.get_supported_voices()
            
            return voices_info.get("voices", [])
            
        except Exception as e:
            raise FileTransferError("audio voices", self.provider.__class__.__name__, e) from e

    def validate_audio_file(self, audio_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate audio file for transcription requirements.
        
        Args:
            audio_file: Path to audio file to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            FileTransferError: If validation fails
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor
            
            processor = AudioProcessor(client=self)
            return processor.validate_audio_for_transcription(audio_file)
            
        except Exception as e:
            raise FileTransferError("audio validation", self.provider.__class__.__name__, e) from e


# Convenience function for backward compatibility
def create_client(api_key: Optional[str] = None, model: str = "test-model-1", show_progress: bool = True, **kwargs) -> AiClient:
    """
    Create an AI client with common parameters.
    
    This is a convenience function for quickly creating an AiClient with the most
    commonly used parameters. It's useful for simple use cases and backward
    compatibility.
    
    Args:
        api_key: OpenAI API key. If provided, takes highest precedence.
                 If None, will resolve from environment/.env automatically.
        model: Model name to use (default: "test-model-1")
        show_progress: Whether to show progress indicator during requests
        **kwargs: Additional settings passed to AiSettings:
                 - temperature: Response temperature 0.0-2.0
                 - max_tokens: Maximum response tokens
                 - timeout: Request timeout in seconds
                 - base_url: Custom API base URL
    
    Returns:
        AiClient: Configured AI client ready for use
    
    Example:
        # Quick client with API key
        client = create_client(api_key="your-key", model="gpt-4")
        
        # Using environment variables or .env file
        client = create_client()
        
        # With custom settings
        client = create_client(
            api_key="your-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000
        )
        
        # Use the client
        response = client.ask("What is AI?")
    """
    # Create settings first
    settings = AiSettings(model=model, **kwargs)
    
    # If explicit API key is provided, use it
    if api_key is not None:
        settings.api_key = api_key
    
    # Create client - the provider factory will handle API key resolution if needed
    return AiClient(settings, show_progress=show_progress)
