"""
config_models.py

Pydantic models for AI configuration with validation, type safety, and immutability.
"""

import os
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
        default="test-model-1",
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
            "test-model-1": ModelConfig(),
            "test-model-2": ModelConfig(
                requests_per_minute=5000,
                tokens_per_minute=2000000,
                tokens_per_day=20000000
            ),
            "test-model-3": ModelConfig(
                requests_per_minute=5000,
                tokens_per_minute=500000,
                tokens_per_day=1500000
            ),
        },
        description="Model-specific rate limiting configurations"
    )
    
    def __init__(self, **data):
        """Initialize with environment variable isolation."""
        self._original_env = None
        super().__init__(**data)
    
    @classmethod
    def create_isolated(cls, env_vars: dict = None, **data):
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
                    "test-model-1": {},
                    "test-model-2": {
                        "requests_per_minute": 5000,
                        "tokens_per_minute": 2000000,
                        "tokens_per_day": 20000000
                    },
                    "test-model-3": {
                        "requests_per_minute": 5000,
                        "tokens_per_minute": 500000,
                        "tokens_per_day": 1500000
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
