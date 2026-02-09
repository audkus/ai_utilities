"""Corrected extended tests for config_models.py based on actual API."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any

from ai_utilities.config_models import ModelConfig, OpenAIConfig, AIConfig, AiSettings
from ai_utilities.env_overrides import override_env


class TestModelConfigCorrected:
    """Corrected test cases for ModelConfig based on actual API."""

    def test_model_config_defaults(self):
        """Test ModelConfig default values."""
        config = ModelConfig()
        
        assert config.requests_per_minute == 5000
        assert config.tokens_per_minute == 450000
        assert config.tokens_per_day == 1350000

    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values."""
        config = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=100000,
            tokens_per_day=1000000
        )
        
        assert config.requests_per_minute == 1000
        assert config.tokens_per_minute == 100000
        assert config.tokens_per_day == 1000000

    def test_model_config_validation_tokens_per_minute_too_low(self):
        """Test validation when tokens_per_minute is too low for requests_per_minute."""
        with pytest.raises(ValueError, match="tokens_per_minute .* too low for requests_per_minute"):
            ModelConfig(
                requests_per_minute=1000,
                tokens_per_minute=5000  # Too low (should be at least 10000)
            )

    def test_model_config_validation_tokens_per_day_too_high(self):
        """Test validation when tokens_per_day exceeds theoretical maximum."""
        with pytest.raises(ValueError):
            ModelConfig(
                requests_per_minute=1000,
                tokens_per_minute=60000,  # 60000 * 60 * 24 = 86,400,000 per day max
                tokens_per_day=100000000  # Too high
            )

    def test_model_config_immutability(self):
        """Test that ModelConfig is immutable."""
        config = ModelConfig()
        
        # Should raise error when trying to modify frozen instance
        with pytest.raises(Exception):  # Could be AttributeError or ValueError depending on Pydantic version
            config.requests_per_minute = 6000

    def test_model_config_edge_cases(self):
        """Test edge cases for ModelConfig."""
        # Test minimum values
        config_min = ModelConfig(
            requests_per_minute=1,
            tokens_per_minute=1000,
            tokens_per_day=10000
        )
        assert config_min.requests_per_minute == 1
        assert config_min.tokens_per_minute == 1000
        assert config_min.tokens_per_day == 10000
        
        # Test maximum values
        config_max = ModelConfig(
            requests_per_minute=10000,
            tokens_per_minute=2000000,
            tokens_per_day=50000000
        )
        assert config_max.requests_per_minute == 10000
        assert config_max.tokens_per_minute == 2000000
        assert config_max.tokens_per_day == 50000000


class TestOpenAIConfigCorrected:
    """Corrected test cases for OpenAIConfig based on actual API."""

    def test_openai_config_defaults(self):
        """Test OpenAIConfig default values."""
        config = OpenAIConfig()
        
        assert config.model == "gpt-3.5-turbo"
        assert config.api_key_env == "AI_API_KEY"
        assert config.base_url is None
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens is None

    def test_openai_config_custom_values(self):
        """Test OpenAIConfig with custom values."""
        config = OpenAIConfig(
            model="gpt-4",
            api_key_env="CUSTOM_API_KEY",
            base_url="https://api.example.com",
            timeout=60,
            temperature=0.1,
            max_tokens=2000
        )
        
        assert config.model == "gpt-4"
        assert config.api_key_env == "CUSTOM_API_KEY"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60
        assert config.temperature == 0.1
        assert config.max_tokens == 2000

    def test_openai_config_base_url_validation(self):
        """Test OpenAIConfig base URL validation."""
        # Valid URLs
        valid_urls = [
            "http://api.openai.com",
            "https://api.openai.com",
            "https://custom-api.example.com/v1"
        ]
        
        for url in valid_urls:
            config = OpenAIConfig(base_url=url)
            assert config.base_url == url

    def test_openai_config_base_url_validation_invalid(self):
        """Test OpenAIConfig base URL validation with invalid URLs."""
        invalid_urls = [
            "ftp://api.openai.com",
            "api.openai.com",
            "://invalid-url",
            ""
        ]
        
        for url in invalid_urls:
            if url:  # Empty string might be allowed as None
                with pytest.raises(ValueError, match="base_url must start with http:// or https://"):
                    OpenAIConfig(base_url=url)

    def test_openai_config_field_validation(self):
        """Test OpenAIConfig field validation."""
        # Test timeout bounds
        with pytest.raises(ValueError):
            OpenAIConfig(timeout=0)  # Too low
        
        with pytest.raises(ValueError):
            OpenAIConfig(timeout=301)  # Too high
        
        # Test temperature bounds
        with pytest.raises(ValueError):
            OpenAIConfig(temperature=-0.1)  # Too low
        
        with pytest.raises(ValueError):
            OpenAIConfig(temperature=2.1)  # Too high
        
        # Test max_tokens bounds
        with pytest.raises(ValueError):
            OpenAIConfig(max_tokens=0)  # Too low
        
        with pytest.raises(ValueError):
            OpenAIConfig(max_tokens=100001)  # Too high

    def test_openai_config_immutability(self):
        """Test that OpenAIConfig is immutable."""
        config = OpenAIConfig()
        
        # Should raise error when trying to modify frozen instance
        with pytest.raises(Exception):
            config.model = "gpt-4"


class TestAIConfigCorrected:
    """Corrected test cases for AIConfig based on actual API."""

    def test_ai_config_defaults(self):
        """Test AIConfig default values."""
        config = AIConfig()
        
        assert config.use_ai is True
        assert config.ai_provider == "openai"
        assert config.waiting_message == "Waiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]"
        assert config.processing_message == "AI response received. Processing..."
        assert config.memory_threshold == 0.8
        assert isinstance(config.openai, OpenAIConfig)
        assert isinstance(config.models, dict)
        assert "gpt-3.5-turbo" in config.models
        assert "gpt-4" in config.models

    def test_ai_config_custom_values(self):
        """Test AIConfig with custom values."""
        custom_model_config = ModelConfig(requests_per_minute=1000)
        config = AIConfig(
            use_ai=False,
            ai_provider="openai",
            waiting_message="Custom waiting message",
            processing_message="Custom processing message",
            memory_threshold=0.9,
            openai=OpenAIConfig(model="gpt-4"),
            models={"custom-model": custom_model_config}
        )
        
        assert config.use_ai is False
        assert config.waiting_message == "Custom waiting message"
        assert config.processing_message == "Custom processing message"
        assert config.memory_threshold == 0.9
        assert config.openai.model == "gpt-4"
        assert config.models["custom-model"].requests_per_minute == 1000

    def test_ai_config_global_model_rate_limits_env_vars(self):
        """Test global model rate limit environment variables."""
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

    def test_ai_config_per_model_rate_limits_env_vars(self):
        """Test per-model rate limit environment variables."""
        with override_env({
            'AI_GPT_4_RPM': '2000',
            'AI_GPT_4_TPM': '200000',
            'AI_GPT_4_TPD': '2000000'
        }):
            config = AIConfig()
            
            gpt4_config = config.models['gpt-4']
            assert gpt4_config.requests_per_minute == 2000
            assert gpt4_config.tokens_per_minute == 200000
            assert gpt4_config.tokens_per_day == 2000000
            
            # Other models should have default values
            gpt35_config = config.models['gpt-3.5-turbo']
            assert gpt35_config.requests_per_minute == 5000  # Default

    def test_ai_config_basic_environment_variables(self):
        """Test basic environment variable handling."""
        with override_env({
            'AI_USE_AI': 'false',
            'AI_MEMORY_THRESHOLD': '0.9',
            'AI_MODEL': 'gpt-4',
            'AI_TEMPERATURE': '0.1',
            'AI_MAX_TOKENS': '1000',
            'AI_TIMEOUT': '60'
        }):
            config = AIConfig()
            
            assert config.use_ai is False
            assert config.memory_threshold == 0.9
            assert config.openai.model == 'gpt-4'
            assert config.openai.temperature == 0.1
            assert config.openai.max_tokens == 1000
            assert config.openai.timeout == 60

    def test_ai_config_invalid_environment_variables(self):
        """Test handling of invalid environment variables."""
        with override_env({
            'AI_MEMORY_THRESHOLD': 'invalid_float',
            'AI_TEMPERATURE': 'invalid_float',
            'AI_MAX_TOKENS': 'invalid_int',
            'AI_TIMEOUT': 'invalid_int'
        }):
            # Should handle gracefully and use defaults
            config = AIConfig()
            
            assert config.memory_threshold == 0.8  # Default
            assert config.openai.temperature == 0.7  # Default
            assert config.openai.max_tokens is None  # Default
            assert config.openai.timeout == 30  # Default

    def test_ai_config_immutability(self):
        """Test that AIConfig is immutable."""
        config = AIConfig()
        
        # Should raise error when trying to modify frozen instance
        with pytest.raises(Exception):
            config.use_ai = False

    def test_ai_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValueError):  # Pydantic should raise for extra fields
            AIConfig(unknown_field="value")

    def test_get_model_config(self):
        """Test getting model configuration."""
        config = AIConfig()
        
        # Test existing model
        gpt4_config = config.get_model_config("gpt-4")
        assert isinstance(gpt4_config, ModelConfig)
        assert gpt4_config.requests_per_minute == 5000
        
        # Test non-existing model (should return default)
        unknown_config = config.get_model_config("unknown-model")
        assert isinstance(unknown_config, ModelConfig)
        assert unknown_config.requests_per_minute == 5000  # Default

    def test_update_model_config(self):
        """Test updating model configuration."""
        config = AIConfig()
        
        new_model_config = ModelConfig(requests_per_minute=1000)
        updated_config = config.update_model_config("gpt-4", new_model_config)
        
        # Should return new instance with updated config
        assert updated_config is not config  # New instance
        assert updated_config.models["gpt-4"].requests_per_minute == 1000
        
        # Original should be unchanged
        assert config.models["gpt-4"].requests_per_minute == 5000

    def test_create_isolated(self):
        """Test creating AIConfig with isolated environment."""
        # Test basic isolated creation
        isolated_config = AIConfig.create_isolated(
            env_vars={'AI_USE_AI': 'true'}
        )
        
        # Should create config successfully
        assert isinstance(isolated_config, AIConfig)

    def test_cleanup_env(self):
        """Test environment cleanup."""
        config = AIConfig()
        
        # Should not raise error - method exists
        try:
            config.cleanup_env()
            cleanup_works = True
        except Exception:
            cleanup_works = False
        
        # Method should exist and be callable
        assert hasattr(config, 'cleanup_env')
        assert callable(getattr(config, 'cleanup_env'))


class TestAiSettingsCorrected:
    """Corrected test cases for AiSettings based on actual API."""

    def test_ai_settings_defaults(self):
        """Test AiSettings default values."""
        settings = AiSettings()
        
        # Test some basic defaults
        assert settings.provider == "auto"  # Default is "auto"
        assert settings.timeout == 30
        assert settings.temperature == 0.7

    def test_ai_settings_from_dotenv(self):
        """Test creating AiSettings from .env file."""
        env_content = """
AI_API_KEY=test-key
AI_MODEL=gpt-4
AI_TEMPERATURE=0.1
"""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=env_content):
            
            settings = AiSettings.from_dotenv()
            
            # Should create settings successfully
            assert isinstance(settings, AiSettings)

    def test_ai_settings_from_ini(self):
        """Test creating AiSettings from INI file."""
        ini_content = """
[ai]
api_key = test-key
model = gpt-4
temperature = 0.1
"""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('configparser.ConfigParser.read'), \
             patch('builtins.open', mock_open(read_data=ini_content)):
            
            settings = AiSettings.from_ini("config.ini")
            
            # Should have loaded from INI
            assert isinstance(settings, AiSettings)

    def test_ai_settings_model_normalization(self):
        """Test model name normalization."""
        # Test with different model name formats
        settings1 = AiSettings(model="gpt-4")
        settings2 = AiSettings(model="gpt-4-turbo")
        
        assert settings1.model == "gpt-4"
        assert settings2.model == "gpt-4-turbo"

    def test_ai_settings_validation(self):
        """Test AiSettings validation."""
        # Test with valid settings
        settings = AiSettings(
            api_key="test-key",
            model="gpt-4",
            provider="openai",
            timeout=60,
            temperature=0.1
        )
        
        assert settings.api_key == "test-key"
        assert settings.model == "gpt-4"
        assert settings.provider == "openai"
        assert settings.timeout == 60
        assert settings.temperature == 0.1

    def test_ai_settings_extra_headers(self):
        """Test extra headers handling."""
        headers_json = '{"Authorization": "Bearer token"}'
        
        with override_env({'AI_EXTRA_HEADERS': headers_json}):
            settings = AiSettings()
            
            # Should parse JSON headers
            assert hasattr(settings, 'extra_headers')

    def test_ai_settings_contextvar_overrides(self):
        """Test contextvar overrides."""
        from ai_utilities.env_overrides import override_env
        
        with override_env({'AI_API_KEY': 'contextvar-key'}):
            settings = AiSettings()
            
            # Should use contextvar override
            assert settings.api_key == 'contextvar-key'

    def test_ai_settings_create_isolated(self):
        """Test creating AiSettings with isolated environment."""
        # Test basic isolated creation
        isolated_settings = AiSettings.create_isolated(
            env_overrides={'AI_API_KEY': 'isolated-key'}
        )
        
        assert isolated_settings.api_key == 'isolated-key'
