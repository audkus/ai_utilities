"""
config_models.py

Pydantic models for AI configuration with validation, type safety, and immutability.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union
from configparser import ConfigParser
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseModel):
    """
    Configuration for AI model rate limiting with validation.
    
    Developer can configure these through:
    1. Environment variables: AI_MODEL_RPM, AI_MODEL_TPM, AI_MODEL_TPD
    2. Config file settings per model
    3. Programmatic override
    """
    
    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        validate_assignment=True
    )
    
    requests_per_minute: int = Field(
        default=5000,
        ge=1,
        le=10000,
        description="Maximum requests per minute for this model"
    )
    
    tokens_per_minute: int = Field(
        default=450000,
        ge=1000,
        le=2000000,
        description="Maximum tokens per minute for this model"
    )
    
    tokens_per_day: int = Field(
        default=1350000,
        ge=10000,
        le=50000000,
        description="Maximum tokens per day for this model"
    )
    
    @field_validator('tokens_per_minute')
    @classmethod
    def validate_tokens_per_minute(cls, v, info):
        """Ensure tokens per minute is reasonable relative to requests per minute."""
        if 'requests_per_minute' in info.data:
            rpm = info.data['requests_per_minute']
            # Rough check: at least 10 tokens per request minimum
            if v < rpm * 10:
                raise ValueError(
                    f"tokens_per_minute ({v}) too low for requests_per_minute ({rpm}). "
                    f"Minimum recommended: {rpm * 10} tokens"
                )
        return v
    
    @field_validator('tokens_per_day')
    @classmethod
    def validate_tokens_per_day(cls, v, info):
        """Ensure tokens per day is reasonable relative to tokens per minute."""
        if 'tokens_per_minute' in info.data:
            tpm = info.data['tokens_per_minute']
            daily_max = tpm * 60 * 24  # Maximum possible if running at full capacity
            if v > daily_max:
                raise ValueError(
                    f"tokens_per_day ({v}) exceeds theoretical maximum ({daily_max}) "
                    f"based on tokens_per_minute ({tpm})"
                )
        return v


class OpenAIConfig(BaseModel):
    """
    OpenAI-specific configuration with validation.
    """
    
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )
    
    model: str = Field(
        default="gpt-3.5-turbo",
        description="Default OpenAI model to use"
    )
    
    api_key_env: str = Field(
        default="AI_API_KEY",
        description="Environment variable name for API key"
    )
    
    base_url: Optional[str] = Field(
        default=None,
        description="Custom OpenAI API base URL"
    )
    
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for requests"
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=100000,
        description="Default maximum tokens for responses"
    )
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate base URL format if provided."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v


class AIConfig(BaseModel):
    """
    Main AI configuration with environment variable support and validation.
    
    Configuration priority (highest to lowest):
    1. Direct parameter setting
    2. Environment variables
    3. Config file values
    4. Default values
    """
    
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra="forbid"  # Prevent unknown fields
    )
    
    use_ai: bool = Field(
        default=True,
        description="Whether AI features are enabled"
    )
    
    ai_provider: Literal["openai"] = Field(
        default="openai",
        description="AI provider to use"
    )
    
    waiting_message: str = Field(
        default="Waiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]",
        description="Message shown while waiting for AI response"
    )
    
    processing_message: str = Field(
        default="AI response received. Processing...",
        description="Message shown when AI response is being processed"
    )
    
    memory_threshold: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Memory usage threshold for AI operations"
    )
    
    openai: OpenAIConfig = Field(
        default_factory=OpenAIConfig,
        description="OpenAI-specific configuration"
    )
    
    models: Dict[str, ModelConfig] = Field(
        default_factory=lambda: {
            "gpt-3.5-turbo": ModelConfig(),
            "gpt-4": ModelConfig(
                requests_per_minute=5000,
                tokens_per_minute=2000000,
                tokens_per_day=20000000
            ),
            "gpt-4-turbo": ModelConfig(
                requests_per_minute=3000,
                tokens_per_minute=2000000,
                tokens_per_day=30000000
            ),
        },
        description="Model-specific rate limiting configurations"
    )
    
    def __init__(self, **data):
        """Initialize with environment variable isolation."""
        self._original_env = None
        super().__init__(**data)
    
    @classmethod
    def create_isolated(cls, env_vars: Optional[dict] = None, **data):
        """Create AIConfig with isolated environment variables."""
        from .env_utils import isolated_env_context
        
        with isolated_env_context(env_vars):
            config = cls(**data)
            return config
    
    def cleanup_env(self):
        """Restore original environment variables."""
        if self._original_env:
            import os
            os.environ.clear()
            os.environ.update(self._original_env)
            self._original_env = None
    
    @model_validator(mode='before')
    @classmethod
    def load_from_environment(cls, data):
        """Load configuration from environment variables with contextvar support."""
        from .env_overrides import get_env_overrides
        
        if isinstance(data, dict):
            # Check environment variables for overrides
            env_overrides = {}
            
            # Get both real environment and contextvar overrides
            real_env = dict(os.environ)
            context_overrides = get_env_overrides()
            
            # Contextvar overrides take precedence over real environment
            combined_env = {**real_env, **context_overrides}
            
            # Basic AI settings
            if 'AI_USE_AI' in combined_env:
                env_overrides['use_ai'] = combined_env['AI_USE_AI'].lower() in ('true', '1', 'yes')
            
            if 'AI_MEMORY_THRESHOLD' in combined_env:
                try:
                    env_overrides['memory_threshold'] = float(combined_env['AI_MEMORY_THRESHOLD'])
                except ValueError:
                    pass  # Keep default if invalid
            
            # OpenAI settings
            openai_overrides = {}
            if 'AI_MODEL' in combined_env:
                openai_overrides['model'] = combined_env['AI_MODEL']
            
            if 'AI_TEMPERATURE' in combined_env:
                try:
                    openai_overrides['temperature'] = float(combined_env['AI_TEMPERATURE'])
                except ValueError:
                    pass
            
            if 'AI_MAX_TOKENS' in combined_env:
                try:
                    openai_overrides['max_tokens'] = int(combined_env['AI_MAX_TOKENS'])
                except ValueError:
                    pass
            
            if 'AI_TIMEOUT' in combined_env:
                try:
                    openai_overrides['timeout'] = int(combined_env['AI_TIMEOUT'])
                except ValueError:
                    pass
            
            if openai_overrides:
                env_overrides['openai'] = openai_overrides
            
            # Model-specific rate limits
            models_overrides = data.get('models', {})
            
            # Ensure we have the default models if none provided
            if not models_overrides:
                models_overrides = {
                    "gpt-3.5-turbo": {},
                    "gpt-4": {
                        "requests_per_minute": 5000,
                        "tokens_per_minute": 2000000,
                        "tokens_per_day": 20000000
                    },
                    "gpt-4-turbo": {
                        "requests_per_minute": 3000,
                        "tokens_per_minute": 2000000,
                        "tokens_per_day": 30000000
                    },
                }
            
            # Global model rate limits
            global_rpm = None
            global_tpm = None
            global_tpd = None
            
            if 'AI_MODEL_RPM' in combined_env:
                try:
                    global_rpm = int(combined_env['AI_MODEL_RPM'])
                except ValueError:
                    pass
            
            if 'AI_MODEL_TPM' in combined_env:
                try:
                    global_tpm = int(combined_env['AI_MODEL_TPM'])
                except ValueError:
                    pass
            
            if 'AI_MODEL_TPD' in combined_env:
                try:
                    global_tpd = int(combined_env['AI_MODEL_TPD'])
                except ValueError:
                    pass
            
            # Apply global rate limits to all models
            for model_name in models_overrides:
                if global_rpm is not None:
                    models_overrides[model_name]['requests_per_minute'] = global_rpm
                if global_tpm is not None:
                    models_overrides[model_name]['tokens_per_minute'] = global_tpm
                if global_tpd is not None:
                    models_overrides[model_name]['tokens_per_day'] = global_tpd
            
            # Per-model rate limits
            for model_name in models_overrides:
                model_upper = model_name.upper().replace('-', '_').replace('.', '_')
                
                if f'AI_{model_upper}_RPM' in combined_env:
                    try:
                        models_overrides[model_name]['requests_per_minute'] = int(combined_env[f'AI_{model_upper}_RPM'])
                    except ValueError:
                        pass
                
                if f'AI_{model_upper}_TPM' in combined_env:
                    try:
                        models_overrides[model_name]['tokens_per_minute'] = int(combined_env[f'AI_{model_upper}_TPM'])
                    except ValueError:
                        pass
                
                if f'AI_{model_upper}_TPD' in combined_env:
                    try:
                        models_overrides[model_name]['tokens_per_day'] = int(combined_env[f'AI_{model_upper}_TPD'])
                    except ValueError:
                        pass
            
            if models_overrides:
                env_overrides['models'] = models_overrides
            
            # Merge environment overrides
            data = {**data, **env_overrides}
        
        return data
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model, with fallback to defaults."""
        if model_name in self.models:
            return self.models[model_name]
        
        # Return default config for unknown models
        return ModelConfig()
    
    def update_model_config(self, model_name: str, config: ModelConfig) -> "AIConfig":
        """Create a new AIConfig with updated model configuration."""
        # Since the model is frozen, we need to create a new instance
        new_models = {**self.models, model_name: config}
        return self.model_copy(update={'models': new_models})


class AiSettings(BaseSettings):
    """
    Configuration settings for AI client using pydantic-settings.
    
    This class manages all configuration for AI clients including API keys,
    model selection, provider selection, and behavior settings. It supports environment variables
    with the 'AI_' prefix and can be configured programmatically.
    
    Environment Variables:
        AI_API_KEY: API key (required for OpenAI, optional for local providers)
        AI_PROVIDER: Provider type ("openai" | "openai_compatible") (default: "openai")
        AI_MODEL: Model name (required, also accepts OPENAI_MODEL as legacy alias)
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
        case_sensitive=False
    )
    
    # Provider selection - expanded to support multiple providers
    provider: Optional[Literal["openai", "groq", "together", "openrouter", "ollama", "lmstudio", "text-generation-webui", "fastchat", "openai_compatible"]] = Field(
        default="openai", 
        description="AI provider to use (inferred from base_url if not specified)"
    )
    
    # Core settings
    api_key: Optional[str] = Field(default=None, description="Generic API key override (AI_API_KEY)")
    
    # Vendor-specific API keys (no prefix - read directly from env)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key (OPENAI_API_KEY)")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key (GROQ_API_KEY)")
    together_api_key: Optional[str] = Field(default=None, description="Together AI API key (TOGETHER_API_KEY)")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key (OPENROUTER_API_KEY)")
    fastchat_api_key: Optional[str] = Field(default=None, description="FastChat API key (FASTCHAT_API_KEY)")
    ollama_api_key: Optional[str] = Field(default=None, description="Ollama API key (OLLAMA_API_KEY)")
    lmstudio_api_key: Optional[str] = Field(default=None, description="LM Studio API key (LMSTUDIO_API_KEY)")
    
    model: Optional[str] = Field(
        default=None,
        description="Model to use (required)"
    )
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
    
    # Knowledge settings
    knowledge_enabled: bool = Field(default=False, description="Whether knowledge indexing and search is enabled")
    knowledge_db_path: Optional[str] = Field(default=None, description="Path to the SQLite knowledge database")
    knowledge_roots: Optional[str] = Field(default=None, description="Comma-separated list of root directories to index")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model for knowledge indexing")
    knowledge_chunk_size: Optional[int] = Field(default=None, ge=100, le=10000, description="Target size of text chunks in characters")
    knowledge_chunk_overlap: Optional[int] = Field(default=None, ge=0, le=1000, description="Number of characters to overlap between chunks")
    knowledge_min_chunk_size: Optional[int] = Field(default=None, ge=10, le=1000, description="Minimum size of a chunk to be considered valid")
    knowledge_max_file_size: Optional[int] = Field(default=None, ge=1024, le=100*1024*1024, description="Maximum file size to process for indexing")
    knowledge_use_sqlite_extension: bool = Field(default=True, description="Whether to try using SQLite vector extensions")
    
    # Caching settings (opt-in)
    cache_enabled: bool = Field(default=False, description="Enable response caching")
    cache_backend: Literal["null", "memory", "sqlite"] = Field(default="null", description="Cache backend to use")
    cache_ttl_s: Optional[int] = Field(default=None, ge=1, description="Cache TTL in seconds (None for no expiration)")
    cache_max_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Maximum temperature for caching (only cache when temp <= this)")
    
    # SQLite cache settings
    cache_sqlite_path: Optional[Path] = Field(default=None, description="Path to SQLite cache database file")
    cache_sqlite_table: str = Field(default="ai_cache", description="SQLite table name for cache")
    cache_sqlite_wal: bool = Field(default=True, description="Enable WAL mode for SQLite cache")
    cache_sqlite_busy_timeout_ms: int = Field(default=3000, ge=100, description="SQLite busy timeout in milliseconds")
    cache_sqlite_max_entries: Optional[int] = Field(default=None, ge=1, description="Maximum entries per namespace (LRU eviction)")
    cache_sqlite_prune_batch: int = Field(default=200, ge=1, description="Batch size for LRU pruning")
    
    # Cache namespace
    cache_namespace: Optional[str] = Field(default=None, description="Cache namespace for isolation (None for auto-detection)")
    
    @field_validator('provider', mode='before')
    @classmethod
    def get_provider(cls, v):
        """Get provider from environment with provider-specific base URL inference."""
        if v is not None:
            return v
        
        # Check explicit AI_PROVIDER first
        ai_provider = os.getenv('AI_PROVIDER')
        if ai_provider:
            return ai_provider
        
        # Then infer from provider-specific base URLs
        from .config_resolver import _infer_provider_from_env_base_urls
        try:
            env_provider = _infer_provider_from_env_base_urls()
            if env_provider:
                return env_provider
        except Exception:
            pass
        
        return "openai"  # Fallback to OpenAI
    
    @field_validator('base_url', mode='before')
    @classmethod  
    def get_base_url(cls, v):
        """Get base URL from environment with provider-specific support."""
        if v is not None:
            return v
        
        # First check AI_BASE_URL
        ai_base_url = os.getenv('AI_BASE_URL')
        if ai_base_url:
            return ai_base_url
        
        # Then check provider-specific base URLs
        from .config_resolver import _get_provider_specific_base_url
        
        # Get the resolved provider (this will include provider-specific inference)
        from .config_resolver import resolve_provider
        try:
            provider = resolve_provider()
            provider_base_url = _get_provider_specific_base_url(provider)
            if provider_base_url:
                return provider_base_url
        except Exception:
            pass
        
        return None

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
    
    @field_validator('fastchat_api_key', mode='before')
    @classmethod
    def get_fastchat_key(cls, v):
        """Get FastChat API key from environment."""
        if v is not None:
            return v
        return os.getenv('FASTCHAT_API_KEY')
    
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
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON for AI_EXTRA_HEADERS: {value}")
        else:
            return value
    
    @field_validator('model', mode='before')
    @classmethod
    def normalize_model(cls, v):
        """Normalize model value: treat empty/whitespace as None."""
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    @model_validator(mode='before')
    @classmethod
    def apply_contextvar_overrides(cls, data):
        """Apply contextvar overrides before pydantic-settings processing."""
        from .env_overrides import get_env_overrides
        
        if isinstance(data, dict):
            # Get both real environment and contextvar overrides
            real_env = dict(os.environ)
            context_overrides = get_env_overrides()
            
            # Contextvar overrides take precedence over real environment
            combined_env = {**real_env, **context_overrides}
            
            if combined_env:
                # Apply environment/contextvar overrides only if not already set in explicit kwargs
                # Explicit kwargs take precedence over environment and contextvar overrides
                env_data = {}
                
                # Only apply environment override if not already in explicit data
                if 'AI_MODEL' in combined_env and 'model' not in data:
                    env_data['model'] = combined_env['AI_MODEL']
                
                if 'AI_TEMPERATURE' in combined_env and 'temperature' not in data:
                    try:
                        env_data['temperature'] = float(combined_env['AI_TEMPERATURE'])
                    except ValueError:
                        pass
                
                if 'AI_MAX_TOKENS' in combined_env and 'max_tokens' not in data:
                    try:
                        env_data['max_tokens'] = int(combined_env['AI_MAX_TOKENS'])
                    except ValueError:
                        pass
                
                if 'AI_TIMEOUT' in combined_env and 'timeout' not in data:
                    try:
                        env_data['timeout'] = int(combined_env['AI_TIMEOUT'])
                    except ValueError:
                        pass
                
                if 'AI_API_KEY' in combined_env and 'api_key' not in data:
                    env_data['api_key'] = combined_env['AI_API_KEY']
                
                if 'AI_PROVIDER' in combined_env and 'provider' not in data:
                    env_data['provider'] = combined_env['AI_PROVIDER']
                
                if 'AI_BASE_URL' in combined_env and 'base_url' not in data:
                    env_data['base_url'] = combined_env['AI_BASE_URL']
                
                # Merge environment overrides with input data
                # Environment overrides come after explicit kwargs
                data = {**data, **env_data}
        
        return data
    
    @model_validator(mode='after')
    def set_model_default(self) -> 'AiSettings':
        """Set default model only if no model was explicitly provided."""
        # Only set default if model is truly None and no explicit value was provided
        # Don't override if model was set by environment or contextvar
        if self.model is None:
            self.model = "gpt-3.5-turbo"
        return self
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """API key is required unless explicitly set to None for testing."""
        return v
    
    @classmethod
    def from_dotenv(cls, env_file: Union[str, Path] = ".env", **data) -> "AiSettings":
        """
        Explicitly load settings from a dotenv file + environment variables.
        Uses pydantic-settings _env_file + _env_file_encoding.
        """
        return cls(_env_file=str(env_file), _env_file_encoding="utf-8", **data)
    
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
            max_tokens_raw = openai_section.get('max_tokens')
            settings_dict = {
                'api_key': openai_section.get('api_key'),
                'model': openai_section.get('model'),  # No default - require explicit model
                'temperature': float(openai_section.get('temperature', 0.7)),
                'max_tokens': int(max_tokens_raw) if max_tokens_raw and max_tokens_raw.strip() else None,
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
        # Import environment detection
        from .env_detection import is_interactive_environment, should_prompt_for_reconfigure, get_environment_type
        
        # Check if we should prompt at all
        if not is_interactive_environment():
            # Non-interactive environment - try to load from environment or .env
            print(f"Non-interactive environment detected ({get_environment_type()}) - skipping interactive setup")
            
            # Try to load from environment variables
            if os.getenv("AI_API_KEY"):
                print("Using existing environment variables for configuration")
                return cls()  # Constructor automatically loads from environment
            
            # Try to load from .env file
            if Path(".env").exists():
                print("Using .env file for configuration")
                return cls.from_dotenv(".env")
            
            # No configuration available - create minimal settings
            print("No existing configuration found - using minimal settings")
            return cls()
        
        print("=== AI Utilities Interactive Setup ===\n")
        
        # Detect operating system
        is_windows = os.name == 'nt'
        
        # Check current environment
        current_api_key = os.getenv("AI_API_KEY")
        current_model = os.getenv("AI_MODEL")  # No default - model is required
        current_temperature = os.getenv("AI_TEMPERATURE", "0.7")
        
        # Determine if setup is needed
        needs_setup = not current_api_key or force_reconfigure
        
        if not needs_setup and current_api_key:
            print(f"✓ API key is already configured (model: {current_model}, temperature: {current_temperature})")
            
            # Only prompt if we're in an environment where prompting is safe
            if should_prompt_for_reconfigure():
                try:
                    response = input("Do you want to reconfigure? (y/N): ").strip().lower()
                    needs_setup = response in ['y', 'yes']
                except (EOFError, KeyboardInterrupt):
                    print("\nNo input received - keeping existing configuration")
                    needs_setup = False
            else:
                print("Non-interactive or CI environment detected - keeping existing configuration")
                needs_setup = False
        
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
                    print("\nWARNING: Exiting application. Please restart after setting the environment variable.")
                    import sys
                    sys.exit(1)  # Exit with error code to indicate setup incomplete
                    
                elif choice == "2":
                    print("\nWARNING: API key will be visible in terminal history")
                    confirm = input("Continue anyway? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        api_key = input("OpenAI API key: ").strip()
                        if api_key:
                            os.environ["AI_API_KEY"] = api_key
                            print("OK: API key set for current session")
                    
                elif choice == "3":
                    api_key = input("OpenAI API key: ").strip()
                    if api_key:
                        os.environ["AI_API_KEY"] = api_key
                        cls._save_to_env_file("AI_API_KEY", api_key)
                        print("OK: API key saved to .env file")
                
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
                'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
                'gpt-3.5-turbo-instruct', 'gpt-4', 'gpt-4-turbo',
                'text-davinci-003',
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
                print(f"WARNING: Could not check for updates: {update_info['error']}")
            elif update_info['has_updates']:
                print(f"NEW: New OpenAI models detected!")
                print(f"INFO: Total models available: {update_info['total_models']}")
                
                if update_info['new_models']:
                    print(f"\nNEW MODELS ({len(update_info['new_models'])}):")
                    for model in update_info['new_models']:
                        print(f"   • {model}")
                
                # Show current models (truncated if too many)
                current_models = update_info['current_models']
                print(f"\nCURRENT MODELS ({len(current_models)}):")
                
                # Show first 10 models, then indicate if there are more
                display_models = current_models[:10]
                for model in display_models:
                    print(f"   • {model}")
                
                if len(current_models) > 10:
                    print(f"   ... and {len(current_models) - 10} more models")
                
                if update_info.get('cached'):
                    print(f"\nCACHED: Using cached results from {update_info['last_check']}")
                else:
                    print(f"\nFRESH: Check completed at {update_info['last_check']}")
                
                response = input("\nWould you like to review your configuration? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    return cls.interactive_setup(force_reconfigure=True)
            else:
                print(f"OK: Your configuration is up to date")
                print(f"INFO: Total models available: {update_info['total_models']}")
                if update_info.get('cached'):
                    print(f"CACHED: Using cached results from {update_info['last_check']}")
        
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
