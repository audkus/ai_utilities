"""
test_config_models.py

Tests for Pydantic configuration models with validation, type safety, and immutability.
"""

import os
import sys

import pytest
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.config_models import AIConfig, ModelConfig, OpenAIConfig


class TestModelConfig:
    """Test ModelConfig validation and constraints."""
    
    def test_default_model_config(self):
        """Test default ModelConfig creation."""
        config = ModelConfig()
        assert config.requests_per_minute == 5000
        assert config.tokens_per_minute == 450000
        assert config.tokens_per_day == 1350000
    
    def test_valid_custom_model_config(self):
        """Test ModelConfig with valid custom values."""
        config = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=100000,
            tokens_per_day=1000000
        )
        assert config.requests_per_minute == 1000
        assert config.tokens_per_minute == 100000
        assert config.tokens_per_day == 1000000
    
    def test_invalid_tokens_per_minute_too_low(self):
        """Test validation fails when tokens_per_minute is too low."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(requests_per_minute=5000, tokens_per_minute=1000)
        assert "too low for requests_per_minute" in str(exc_info.value)
    
    def test_invalid_tokens_per_day_too_high(self):
        """Test validation fails when tokens_per_day exceeds theoretical maximum."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                requests_per_minute=5000,
                tokens_per_minute=450000,
                tokens_per_day=100000000  # Way too high
            )
        assert "less than or equal to" in str(exc_info.value)
    
    def test_boundary_values(self):
        """Test boundary values for validation."""
        # Minimum valid values
        config = ModelConfig(
            requests_per_minute=1,
            tokens_per_minute=1000,
            tokens_per_day=10000
        )
        assert config.requests_per_minute == 1
        assert config.tokens_per_minute == 1000
        assert config.tokens_per_day == 10000
        
        # Maximum valid values
        config = ModelConfig(
            requests_per_minute=10000,
            tokens_per_minute=2000000,
            tokens_per_day=50000000
        )
        assert config.requests_per_minute == 10000
        assert config.tokens_per_minute == 2000000
        assert config.tokens_per_day == 50000000
    
    def test_immutability(self):
        """Test that ModelConfig is immutable."""
        config = ModelConfig()
        
        # Should raise exception when trying to modify
        with pytest.raises(Exception):  # TypeError for frozen Pydantic models
            config.requests_per_minute = 6000


class TestOpenAIConfig:
    """Test OpenAIConfig validation and constraints."""
    
    def test_default_openai_config(self):
        """Test default OpenAIConfig creation."""
        config = OpenAIConfig()
        assert config.model == "test-model-1"
        assert config.api_key_env == "AI_API_KEY"
        assert config.base_url is None
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens is None
    
    def test_valid_custom_openai_config(self):
        """Test OpenAIConfig with valid custom values."""
        config = OpenAIConfig(
            model="test-model-2",
            api_key_env="MY_API_KEY",
            base_url="https://api.openai.com/v1",
            timeout=60,
            temperature=0.5,
            max_tokens=1000
        )
        assert config.model == "test-model-2"
        assert config.api_key_env == "MY_API_KEY"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.timeout == 60
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
    
    def test_invalid_base_url(self):
        """Test validation fails for invalid base URL."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIConfig(base_url="invalid-url")
        assert "must start with http:// or https://" in str(exc_info.value)
    
    def test_temperature_bounds(self):
        """Test temperature validation bounds."""
        # Valid bounds
        OpenAIConfig(temperature=0.0)
        OpenAIConfig(temperature=2.0)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            OpenAIConfig(temperature=-0.1)
        
        with pytest.raises(ValidationError):
            OpenAIConfig(temperature=2.1)
    
    def test_immutability(self):
        """Test that OpenAIConfig is immutable."""
        config = OpenAIConfig()
        
        with pytest.raises(Exception):
            config.model = "test-model-2"


class TestAIConfig:
    """Test AIConfig validation and environment variable integration."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Clear relevant environment variables
        env_vars_to_clear = [
            'AI_USE_AI', 'AI_MEMORY_THRESHOLD', 'AI_MODEL', 'AI_TEMPERATURE',
            'AI_MAX_TOKENS', 'AI_TIMEOUT', 'AI_MODEL_RPM', 'AI_MODEL_TPM', 'AI_MODEL_TPD',
            'AI_TEST_MODEL_1_RPM', 'AI_TEST_MODEL_1_TPM', 'AI_TEST_MODEL_1_TPD',
            'AI_TEST_MODEL_2_RPM', 'AI_TEST_MODEL_2_TPM', 'AI_TEST_MODEL_2_TPD'
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
    
    def test_default_ai_config(self):
        """Test default AIConfig creation."""
        config = AIConfig()
        assert config.use_ai is True
        assert config.ai_provider == "openai"
        assert config.openai.model == "test-model-1"
        assert len(config.models) >= 3  # Should have default models
        assert "test-model-1" in config.models
        assert "test-model-2" in config.models
    
    def test_environment_variable_integration(self):
        """Test environment variable integration."""
        from ai_utilities.env_overrides import override_env
        
        # Test with environment variable overrides
        with override_env({
            'AI_USE_AI': 'false',
            'AI_MEMORY_THRESHOLD': '0.9',
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '0.3',
            'AI_MAX_TOKENS': '500',
            'AI_TIMEOUT': '60'
        }):
            config = AIConfig()
            
            assert config.use_ai is False
            assert config.memory_threshold == 0.9
            assert config.openai.model == 'test-model-2'
            assert config.openai.temperature == 0.3
            assert config.openai.max_tokens == 500
            assert config.openai.timeout == 60
    
    def test_global_model_rate_limits_env_vars(self):
        """Test global model rate limit environment variables."""
        from ai_utilities.env_overrides import override_env
        
        with override_env({
            'AI_MODEL_RPM': '1000',
            'AI_MODEL_TPM': '100000',
            'AI_MODEL_TPD': '1000000'
        }):
            config = AIConfig()
            
            # All models should have the updated limits
            for model_config in config.models.values():
                assert model_config.requests_per_minute == 1000
                assert model_config.tokens_per_minute == 100000
                assert model_config.tokens_per_day == 1000000
    
    def test_per_model_rate_limits_env_vars(self):
        """Test per-model rate limit environment variables."""
        from ai_utilities.env_overrides import override_env
        
        with override_env({
            'AI_TEST_MODEL_1_RPM': '2000',
            'AI_TEST_MODEL_1_TPM': '200000',
            'AI_TEST_MODEL_1_TPD': '2000000'
        }):
            config = AIConfig()
            
            gpt4_config = config.models['test-model-1']
            assert gpt4_config.requests_per_minute == 2000
            assert gpt4_config.tokens_per_minute == 200000
            assert gpt4_config.tokens_per_day == 2000000
            
            # Other models should have default values
            gpt35_config = config.models['test-model-2']
            assert gpt35_config.requests_per_minute == 5000  # Default
    
    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variables."""
        from ai_utilities.env_overrides import override_env
        
        with override_env({
            'AI_MEMORY_THRESHOLD': 'invalid',
            'AI_TEMPERATURE': 'invalid',
            'AI_MAX_TOKENS': 'invalid'
        }):
            # Should fall back to defaults for invalid values
            config = AIConfig()
            assert config.memory_threshold == 0.8  # Default
            assert config.openai.temperature == 0.7  # Default
            assert config.openai.max_tokens is None  # Default
    
    def test_get_model_config(self):
        """Test getting model configuration."""
        config = AIConfig()
        
        # Existing model
        gpt4_config = config.get_model_config('test-model-1')
        assert isinstance(gpt4_config, ModelConfig)
        assert gpt4_config.requests_per_minute == 5000
        
        # Non-existent model (should return default)
        unknown_config = config.get_model_config('unknown-model')
        assert isinstance(unknown_config, ModelConfig)
        assert unknown_config.requests_per_minute == 5000  # Default
    
    def test_update_model_config(self):
        """Test updating model configuration."""
        config = AIConfig()
        
        custom_model = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=100000,
            tokens_per_day=1000000
        )
        
        updated_config = config.update_model_config('custom-model', custom_model)
        
        # Should create new config with updated model
        assert 'custom-model' in updated_config.models
        assert updated_config.models['custom-model'].requests_per_minute == 1000
        
        # Original config should be unchanged (immutability)
        assert 'custom-model' not in config.models
    
    def test_immutability(self):
        """Test that AIConfig is immutable."""
        config = AIConfig()
        
        with pytest.raises(Exception):
            config.use_ai = False
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(extra_field="should_fail")
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestConfigIntegration:
    """Test integration between configuration components."""
    
    def test_full_configuration_workflow(self):
        """Test complete configuration workflow."""
        from ai_utilities.env_overrides import override_env
        
        # Test with environment variable overrides
        with override_env({
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '0.5',
            'AI_TEST_MODEL_2_RPM': '3000'
        }):
            # Create configuration
            config = AIConfig()
            
            # Verify all settings applied
            assert config.openai.model == 'test-model-2'
            assert config.openai.temperature == 0.5
            assert config.models['test-model-2'].requests_per_minute == 3000
            
            # Get specific model config
            model_config = config.get_model_config('test-model-2')
            assert model_config.requests_per_minute == 3000
    
    def test_configuration_validation_chain(self):
        """Test that validation works across the configuration chain."""
        from ai_utilities.env_overrides import override_env
        
        with override_env({'AI_TEMPERATURE': '3.0'}):  # Invalid (> 2.0)
            with pytest.raises(ValidationError):
                AIConfig()
    
    def test_environment_variable_precedence(self):
        """Test environment variable precedence over defaults."""
        from ai_utilities.env_overrides import override_env
        from ai_utilities.env_utils import cleanup_ai_env_vars
        
        # Clean up any existing environment variables
        cleanup_ai_env_vars()
        
        with override_env({
            'AI_MODEL_RPM': '1000',  # Global
            'AI_TEST_MODEL_1_RPM': '2000'   # Specific
        }):
            config = AIConfig()
            
            # Specific should override global for test-model-1
            assert config.models['test-model-1'].requests_per_minute == 2000
            
            # test-model-2 uses global AI_MODEL_RPM when no specific override
            assert config.models['test-model-2'].requests_per_minute == 1000
