"""Focused validation tests for config_models.py to improve coverage.

This module targets specific validation paths that are currently missing coverage.
"""

from typing import Any, Dict, Optional
import pytest
from pydantic import ValidationError

# Force import to ensure coverage can track the module
import ai_utilities.config_models
from ai_utilities.config_models import ModelConfig, OpenAIConfig, AiSettings


class TestConfigModelsValidation:
    """Test specific validation paths in config_models.py."""

    def test_model_config_edge_cases(self) -> None:
        """Test edge cases for ModelConfig validation."""
        # Test boundary values
        config = ModelConfig(
            requests_per_minute=1,  # Minimum
            tokens_per_minute=1000,  # Minimum (1 * 10)
            tokens_per_day=10000    # Minimum
        )
        assert config.requests_per_minute == 1
        assert config.tokens_per_minute == 1000
        assert config.tokens_per_day == 10000

        # Test maximum values
        config = ModelConfig(
            requests_per_minute=10000,  # Maximum
            tokens_per_minute=2000000,   # Maximum
            tokens_per_day=50000000     # Maximum
        )
        assert config.requests_per_minute == 10000
        assert config.tokens_per_minute == 2000000
        assert config.tokens_per_day == 50000000

    def test_model_config_validation_messages(self) -> None:
        """Test specific validation error messages."""
        # Test tokens_per_minute validation message
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                requests_per_minute=5000,
                tokens_per_minute=40000  # Too low: need 50000 minimum
            )
        error_msg = str(exc_info.value)
        assert "tokens_per_minute (40000) too low for requests_per_minute (5000)" in error_msg
        assert "Minimum recommended: 50000 tokens" in error_msg

        # Test tokens_per_day validation message
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                requests_per_minute=100,
                tokens_per_minute=2000,   # Meets minimum (100 * 10)
                tokens_per_day=4000000    # Too high: max is 2000 * 60 * 24 = 2880000
            )
        error_msg = str(exc_info.value)
        assert "tokens_per_day (4000000) exceeds theoretical maximum" in error_msg
        assert "based on tokens_per_minute (2000)" in error_msg

    def test_openai_config_all_models(self) -> None:
        """Test OpenAIConfig with different model names."""
        models = [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "text-davinci-003",
            "text-curie-001",
            "text-babbage-001",
            "text-ada-001"
        ]
        
        for model in models:
            config = OpenAIConfig(model=model)
            assert config.model == model

    def test_ai_settings_provider_validation(self) -> None:
        """Test AiSettings provider validation with specific error messages."""
        # Test all valid providers
        valid_providers = [
            "auto",
            "openai", 
            "groq",
            "together",
            "openrouter",
            "ollama",
            "lmstudio",
            "text-generation-webui",
            "fastchat",
            "openai_compatible"
        ]
        
        for provider in valid_providers:
            settings = AiSettings(api_key="test-key", provider=provider)
            assert settings.provider == provider

        # Test invalid provider error message
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", provider="invalid-provider")
        error_msg = str(exc_info.value)
        assert "provider" in error_msg
        assert "Input should be" in error_msg  # Pydantic validation message

    def test_ai_settings_parameter_validation(self) -> None:
        """Test AiSettings parameter validation with edge cases."""
        # Test temperature boundary values
        settings = AiSettings(api_key="test-key", temperature=0.0)
        assert settings.temperature == 0.0
        
        settings = AiSettings(api_key="test-key", temperature=2.0)
        assert settings.temperature == 2.0

        # Test max_tokens boundary values
        settings = AiSettings(api_key="test-key", max_tokens=1)
        assert settings.max_tokens == 1

        # Test timeout boundary values
        settings = AiSettings(api_key="test-key", timeout=1)
        assert settings.timeout == 1

    def test_ai_settings_validation_error_messages(self) -> None:
        """Test specific validation error messages for AiSettings."""
        # Test temperature validation
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", temperature=-0.1)
        error_msg = str(exc_info.value)
        assert "temperature" in error_msg
        assert "Input should be greater than or equal to 0" in error_msg

        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", temperature=2.1)
        error_msg = str(exc_info.value)
        assert "temperature" in error_msg
        assert "Input should be less than or equal to 2" in error_msg

        # Test max_tokens validation
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", max_tokens=0)
        error_msg = str(exc_info.value)
        assert "max_tokens" in error_msg
        assert "Input should be greater than or equal to 1" in error_msg

        # Test timeout validation
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", timeout=0)
        error_msg = str(exc_info.value)
        assert "timeout" in error_msg
        assert "Input should be greater than or equal to 1" in error_msg

    def test_ai_settings_url_validation(self, isolated_env) -> None:
        """Test AiSettings base URL validation."""
        # Test various URL formats
        urls = [
            "https://api.openai.com/v1",
            "http://localhost:8080/v1",
            "https://custom.example.com/api",
            "https://api.groq.com/openai/v1",
            "http://127.0.0.1:11434/v1"
        ]
        
        for url in urls:
            settings = AiSettings(api_key="test-key", base_url=url)
            assert settings.base_url == url

        # Test empty and None URLs
        settings = AiSettings(api_key="test-key", base_url=None)
        assert settings.base_url is None

        settings = AiSettings(api_key="test-key", base_url="")
        assert settings.base_url == ""

    def test_ai_settings_serialization_round_trip(self) -> None:
        """Test AiSettings serialization and deserialization."""
        original = AiSettings(
            api_key="test-key-12345",
            provider="groq",
            base_url="https://api.groq.com/openai/v1",
            model="llama-3-70b",
            temperature=0.7,
            max_tokens=2048,
            timeout=60
        )
        
        # Test dict serialization
        settings_dict = original.model_dump()
        assert isinstance(settings_dict, dict)
        assert settings_dict["api_key"] == "test-key-12345"
        assert settings_dict["provider"] == "groq"
        assert settings_dict["model"] == "llama-3-70b"
        assert settings_dict["temperature"] == 0.7
        assert settings_dict["max_tokens"] == 2048
        assert settings_dict["timeout"] == 60

        # Test JSON serialization
        settings_json = original.model_dump_json()
        assert isinstance(settings_json, str)
        assert "test-key-12345" in settings_json
        assert "groq" in settings_json

        # Test round-trip
        restored = AiSettings(**settings_dict)
        assert restored.api_key == original.api_key
        assert restored.provider == original.provider
        assert restored.base_url == original.base_url
        assert restored.model == original.model
        assert restored.temperature == original.temperature
        assert restored.max_tokens == original.max_tokens
        assert restored.timeout == original.timeout

    def test_model_config_serialization(self) -> None:
        """Test ModelConfig serialization."""
        config = ModelConfig(
            requests_per_minute=1500,
            tokens_per_minute=30000,
            tokens_per_day=1500000
        )
        
        # Test dict serialization
        config_dict = config.model_dump()
        assert config_dict["requests_per_minute"] == 1500
        assert config_dict["tokens_per_minute"] == 30000
        assert config_dict["tokens_per_day"] == 1500000

        # Test JSON serialization
        config_json = config.model_dump_json()
        assert "1500" in config_json
        assert "30000" in config_json
        assert "1500000" in config_json

    def test_openai_config_serialization(self) -> None:
        """Test OpenAIConfig serialization."""
        config = OpenAIConfig(model="gpt-4-turbo")
        
        # Test dict serialization
        config_dict = config.model_dump()
        assert config_dict["model"] == "gpt-4-turbo"

        # Test JSON serialization
        config_json = config.model_dump_json()
        assert "gpt-4-turbo" in config_json
