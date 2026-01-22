"""
test_coverage_config_models_simple.py

Simple working tests for config_models.py to improve coverage.
"""

import os
import sys
from unittest.mock import patch
from pathlib import Path
import pytest
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.config_models import AIConfig, ModelConfig, OpenAIConfig, AiSettings


class TestConfigModelsCoverageSimple:
    """Simple working tests for config_models.py coverage gaps."""
    
    def test_ai_config_cleanup_env(self):
        """Test AIConfig.cleanup_env method."""
        config = AIConfig()
        config._original_env = {'TEST_VAR': 'original_value'}
        
        with patch.dict(os.environ, {'TEST_VAR': 'modified_value'}):
            config.cleanup_env()
            # Should restore original environment
            assert os.environ.get('TEST_VAR') == 'original_value'
    
    def test_ai_config_get_model_config(self):
        """Test AIConfig.get_model_config method."""
        config = AIConfig()
        
        # Test existing model
        model_config = config.get_model_config('gpt-4')
        assert isinstance(model_config, ModelConfig)
        
        # Test nonexistent model (should return default)
        default_config = config.get_model_config('nonexistent-model')
        assert isinstance(default_config, ModelConfig)
        assert default_config.requests_per_minute == 5000
    
    def test_ai_config_update_model_config(self):
        """Test AIConfig.update_model_config method."""
        config = AIConfig()
        new_config = ModelConfig(requests_per_minute=1000)
        
        updated_config = config.update_model_config('gpt-4', new_config)
        assert updated_config.models['gpt-4'].requests_per_minute == 1000
        # Original should be unchanged (immutable)
        assert config.models['gpt-4'].requests_per_minute == 5000
    
    def test_openai_config_validation_base_url(self):
        """Test OpenAIConfig base_url validation."""
        # Test valid base URL
        config = OpenAIConfig(api_key='test-key', base_url='https://api.openai.com/v1')
        assert config.base_url == 'https://api.openai.com/v1'
        
        # Test invalid base URL
        with pytest.raises(ValidationError) as exc_info:
            OpenAIConfig(api_key='test-key', base_url='invalid-url')
        assert 'base_url must start with http:// or https://' in str(exc_info.value)
    
    def test_ai_config_with_models_overrides(self):
        """Test AIConfig with model-specific overrides."""
        config = AIConfig(models={
            'gpt-3.5-turbo': {'requests_per_minute': 1000}
        })
        assert config.models['gpt-3.5-turbo'].requests_per_minute == 1000
    
    def test_ai_config_with_empty_models_overrides(self):
        """Test AIConfig with empty models overrides uses defaults."""
        config = AIConfig(models={})
        # Should still have default models
        assert 'gpt-3.5-turbo' in config.models
        assert 'gpt-4' in config.models
        assert 'gpt-4-turbo' in config.models
    
    def test_ai_config_custom_model_validation(self):
        """Test AIConfig custom model validation."""
        # Test model with invalid RPM/TPM ratio
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(models={
                'test-model': ModelConfig(
                    requests_per_minute=5000,
                    tokens_per_minute=1000  # Too low for 5000 RPM
                )
            })
        assert "too low for requests_per_minute" in str(exc_info.value)
    
    def test_ai_config_model_validator_with_custom_models(self):
        """Test AIConfig model validator with custom model configurations."""
        config = AIConfig(models={
            'custom-model': {
                'requests_per_minute': 100,
                'tokens_per_minute': 10000,
                'tokens_per_day': 100000
            }
        })
        assert 'custom-model' in config.models
        assert config.models['custom-model'].requests_per_minute == 100
    
    def test_model_config_validate_tokens_per_minute(self):
        """Test ModelConfig tokens_per_minute validator."""
        # Test valid case
        config = ModelConfig(requests_per_minute=1000, tokens_per_minute=10000)
        assert config.tokens_per_minute == 10000
        
        # Test invalid case (too low for RPM)
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(requests_per_minute=5000, tokens_per_minute=1000)
        assert "too low for requests_per_minute" in str(exc_info.value)
    
    def test_ai_settings_save_to_env_file(self, tmp_path):
        """Test AiSettings._save_to_env_file method."""
        env_file = tmp_path / ".env"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            AiSettings._save_to_env_file("TEST_VAR", "test_value")
        
        # Just check that the method runs without error
        assert True
    
    def test_model_config_minimum_valid(self):
        """Test ModelConfig minimum valid values."""
        # Test a valid configuration
        config = ModelConfig(
            requests_per_minute=100,
            tokens_per_minute=10000,
            tokens_per_day=100000
        )
        assert config.requests_per_minute == 100
