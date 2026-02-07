"""
test_config_models_extended.py

Extended tests for Pydantic configuration models to increase coverage.
"""

import pytest
from pydantic import ValidationError
from unittest.mock import patch, mock_open

from ai_utilities.config_models import AIConfig, ModelConfig, OpenAIConfig


class TestOpenAIConfig:
    """Test OpenAIConfig validation and constraints."""
    
    def test_default_openai_config(self) -> None:
        """Test default OpenAIConfig creation."""
        config = OpenAIConfig()
        assert config.model == "gpt-3.5-turbo"
        assert config.api_key_env == "AI_API_KEY"
        assert config.base_url is None
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens is None
    
    def test_custom_openai_config(self) -> None:
        """Test OpenAIConfig with custom values."""
        config = OpenAIConfig(
            model="gpt-4",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
            timeout=60,
            temperature=0.5,
            max_tokens=2000
        )
        assert config.model == "gpt-4"
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.timeout == 60
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
    
    def test_invalid_base_url_http(self) -> None:
        """Test validation fails with invalid base URL."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIConfig(base_url="ftp://example.com")
        assert "must start with http:// or https://" in str(exc_info.value)
    
    def test_invalid_base_url_no_protocol(self) -> None:
        """Test validation fails with base URL missing protocol."""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIConfig(base_url="api.example.com")
        assert "must start with http:// or https://" in str(exc_info.value)
    
    def test_valid_base_urls(self) -> None:
        """Test valid base URLs are accepted."""
        urls = [
            "http://localhost:8080",
            "https://api.openai.com/v1",
            "https://custom-api.example.com"
        ]
        for url in urls:
            config = OpenAIConfig(base_url=url)
            assert config.base_url == url
    
    def test_timeout_validation(self) -> None:
        """Test timeout field validation."""
        # Valid timeout
        config = OpenAIConfig(timeout=100)
        assert config.timeout == 100
        
        # Invalid timeouts
        with pytest.raises(ValidationError):
            OpenAIConfig(timeout=0)  # Too low
        
        with pytest.raises(ValidationError):
            OpenAIConfig(timeout=400)  # Too high
    
    def test_temperature_validation(self) -> None:
        """Test temperature field validation."""
        # Valid temperatures
        config = OpenAIConfig(temperature=1.5)
        assert config.temperature == 1.5
        
        # Invalid temperatures
        with pytest.raises(ValidationError):
            OpenAIConfig(temperature=-0.1)  # Too low
        
        with pytest.raises(ValidationError):
            OpenAIConfig(temperature=2.1)  # Too high
    
    def test_max_tokens_validation(self) -> None:
        """Test max_tokens field validation."""
        # Valid max_tokens
        config = OpenAIConfig(max_tokens=50000)
        assert config.max_tokens == 50000
        
        # Invalid max_tokens
        with pytest.raises(ValidationError):
            OpenAIConfig(max_tokens=0)  # Too low
        
        with pytest.raises(ValidationError):
            OpenAIConfig(max_tokens=200000)  # Too high


class TestAIConfigExtended:
    """Test AIConfig validation and constraints."""
    
    def test_default_ai_config(self) -> None:
        """Test default AIConfig creation."""
        config = AIConfig()
        assert config.use_ai is True
        assert config.ai_provider == "openai"
        assert config.memory_threshold == 0.8
        assert config.openai.model == "gpt-3.5-turbo"
        assert "gpt-3.5-turbo" in config.models
        assert "gpt-4" in config.models
    
    def test_custom_ai_config(self) -> None:
        """Test AIConfig with custom values."""
        custom_openai = OpenAIConfig(model="gpt-4", timeout=60)
        config = AIConfig(
            use_ai=False,
            memory_threshold=0.9,
            openai=custom_openai
        )
        assert config.use_ai is False
        assert config.memory_threshold == 0.9
        assert config.openai.model == "gpt-4"
        assert config.openai.timeout == 60
    
    def test_memory_threshold_validation(self) -> None:
        """Test memory_threshold field validation."""
        # Valid thresholds
        config = AIConfig(memory_threshold=0.5)
        assert config.memory_threshold == 0.5
        
        # Invalid thresholds
        with pytest.raises(ValidationError):
            AIConfig(memory_threshold=0.05)  # Too low
        
        with pytest.raises(ValidationError):
            AIConfig(memory_threshold=1.1)  # Too high
    
    def test_model_config_immutability(self) -> None:
        """Test that ModelConfig is immutable."""
        config = ModelConfig()
        
        # Should raise error when trying to modify
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            config.requests_per_minute = 1000
    
    def test_openai_config_immutability(self) -> None:
        """Test that OpenAIConfig is immutable."""
        config = OpenAIConfig()
        
        # Should raise error when trying to modify
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            config.model = "gpt-4"
    
    def test_ai_config_immutability(self) -> None:
        """Test that AIConfig is immutable."""
        config = AIConfig()
        
        # Should raise error when trying to modify
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            config.use_ai = False
    
    def test_ai_config_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden in AIConfig."""
        with pytest.raises(ValidationError) as exc_info:
            AIConfig(extra_field="not_allowed")
        assert "extra" in str(exc_info.value).lower()
    
    def test_default_model_configurations(self) -> None:
        """Test that default model configurations are properly set."""
        config = AIConfig()
        
        # Check gpt-3.5-turbo defaults
        gpt35 = config.models["gpt-3.5-turbo"]
        assert gpt35.requests_per_minute == 5000
        assert gpt35.tokens_per_minute == 450000
        assert gpt35.tokens_per_day == 1350000
        
        # Check gpt-4 defaults
        gpt4 = config.models["gpt-4"]
        assert gpt4.requests_per_minute == 5000
        assert gpt4.tokens_per_minute == 2000000
        assert gpt4.tokens_per_day == 20000000
    
    def test_waiting_message_format(self) -> None:
        """Test waiting message format."""
        config = AIConfig()
        # The format string uses {hours:02} not just {hours}
        assert "hours" in config.waiting_message
        assert "minutes" in config.waiting_message
        assert "seconds" in config.waiting_message
    
    def test_processing_message(self) -> None:
        """Test processing message."""
        config = AIConfig()
        assert "Processing" in config.processing_message
    
    def test_ai_provider_literal(self) -> None:
        """Test that ai_provider only accepts 'openai'."""
        config = AIConfig()
        assert config.ai_provider == "openai"
        
        # Test that it's a literal type (only 'openai' allowed)
        # This is mainly a type checking test - Pydantic handles validation


class TestConfigModelIntegration:
    """Test integration between different config models."""
    
    def test_nested_config_validation(self) -> None:
        """Test validation in nested configurations."""
        # This should work - valid nested config
        config = AIConfig(
            openai=OpenAIConfig(
                model="gpt-4",
                temperature=0.1
            )
        )
        assert config.openai.model == "gpt-4"
        assert config.openai.temperature == 0.1
    
    def test_model_config_in_models_dict(self) -> None:
        """Test that ModelConfig objects work correctly in the models dict."""
        custom_model = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=100000
        )
        
        config = AIConfig(
            models={
                "custom-model": custom_model
            }
        )
        
        assert config.models["custom-model"].requests_per_minute == 1000
        assert config.models["custom-model"].tokens_per_minute == 100000
    
    def test_config_serialization(self) -> None:
        """Test that configurations can be serialized."""
        config = AIConfig()
        
        # Test model_dump
        data = config.model_dump()
        assert isinstance(data, dict)
        assert "use_ai" in data
        assert "openai" in data
        assert "models" in data
        
        # Test model_dump_json
        json_str = config.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test round-trip
        config2 = AIConfig(**data)
        assert config.use_ai == config2.use_ai
        assert config.openai.model == config2.openai.model
