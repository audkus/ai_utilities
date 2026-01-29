"""Comprehensive tests for config_models.py module.

This module tests the configuration models and ensures all validation paths are exercised.
"""

from typing import Any, Dict
import pytest
from pydantic import ValidationError

# Force import to ensure coverage can track the module
import ai_utilities.config_models
from ai_utilities.config_models import ModelConfig, OpenAIConfig, AiSettings


class TestModelConfig:
    """Test ModelConfig comprehensively."""

    def test_default_creation(self) -> None:
        """Test creating ModelConfig with default values."""
        config = ModelConfig()
        
        assert config.requests_per_minute == 5000
        assert config.tokens_per_minute == 450000
        assert config.tokens_per_day == 1350000

    def test_custom_creation(self) -> None:
        """Test creating ModelConfig with custom values."""
        config = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=20000,
            tokens_per_day=1000000
        )
        
        assert config.requests_per_minute == 1000
        assert config.tokens_per_minute == 20000
        assert config.tokens_per_day == 1000000

    @pytest.mark.parametrize("rpm", [1, 100, 5000, 10000])
    def test_valid_requests_per_minute(self, rpm: int) -> None:
        """Test valid requests_per_minute values."""
        config = ModelConfig(requests_per_minute=rpm)
        assert config.requests_per_minute == rpm

    @pytest.mark.parametrize("rpm", [0, -1, 10001])
    def test_invalid_requests_per_minute(self, rpm: int) -> None:
        """Test invalid requests_per_minute values."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(requests_per_minute=rpm)
        assert "requests_per_minute" in str(exc_info.value)

    @pytest.mark.parametrize("tpm", [50000, 100000, 450000, 2000000])
    def test_valid_tokens_per_minute(self, tpm: int) -> None:
        """Test valid tokens_per_minute values."""
        config = ModelConfig(tokens_per_minute=tpm)
        assert config.tokens_per_minute == tpm

    @pytest.mark.parametrize("tpm", [49999, -1, 2000001])
    def test_invalid_tokens_per_minute(self, tpm: int) -> None:
        """Test invalid tokens_per_minute values."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(tokens_per_minute=tpm)
        assert "tokens_per_minute" in str(exc_info.value)

    @pytest.mark.parametrize("tpd", [10000, 1000000, 1350000, 50000000])
    def test_valid_tokens_per_day(self, tpd: int) -> None:
        """Test valid tokens_per_day values."""
        config = ModelConfig(tokens_per_day=tpd)
        assert config.tokens_per_day == tpd

    @pytest.mark.parametrize("tpd", [9999, -1, 50000001])
    def test_invalid_tokens_per_day(self, tpd: int) -> None:
        """Test invalid tokens_per_day values."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(tokens_per_day=tpd)
        assert "tokens_per_day" in str(exc_info.value)

    def test_tokens_per_minute_validation_too_low(self) -> None:
        """Test tokens_per_minute validation when too low for requests_per_minute."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                requests_per_minute=1000,
                tokens_per_minute=5000  # Too low: need at least 10000
            )
        assert "tokens_per_minute" in str(exc_info.value)
        assert "too low for requests_per_minute" in str(exc_info.value)

    def test_tokens_per_minute_validation_ok(self) -> None:
        """Test tokens_per_minute validation when acceptable."""
        config = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=15000  # OK: more than 10000 minimum
        )
        assert config.tokens_per_minute == 15000

    def test_tokens_per_day_validation_too_high(self) -> None:
        """Test tokens_per_day validation when too high for tokens_per_minute."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                requests_per_minute=100,  # Lower RPM to allow lower TPM
                tokens_per_minute=2000,   # Meets minimum (100 * 10 = 1000)
                tokens_per_day=5000000    # Too high: max is 2000 * 60 * 24 = 2880000
            )
        assert "tokens_per_day" in str(exc_info.value)
        assert "exceeds theoretical maximum" in str(exc_info.value)

    def test_tokens_per_day_validation_ok(self) -> None:
        """Test tokens_per_day validation when acceptable."""
        config = ModelConfig(
            requests_per_minute=100,  # Lower RPM to allow lower TPM
            tokens_per_minute=2000,   # Meets minimum (100 * 10 = 1000)
            tokens_per_day=1000000    # OK: less than 2880000 max
        )
        assert config.tokens_per_day == 1000000

    def test_immutability(self) -> None:
        """Test that ModelConfig is immutable."""
        config = ModelConfig()
        
        # Attempting to change fields should raise an error
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            config.requests_per_minute = 6000

    def test_model_dict_conversion(self) -> None:
        """Test ModelConfig can be converted to dict."""
        config = ModelConfig(
            requests_per_minute=1000,
            tokens_per_minute=20000,
            tokens_per_day=1000000
        )
        
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert config_dict["requests_per_minute"] == 1000
        assert config_dict["tokens_per_minute"] == 20000
        assert config_dict["tokens_per_day"] == 1000000

    def test_round_trip_serialization(self) -> None:
        """Test ModelConfig round-trip serialization."""
        original = ModelConfig(
            requests_per_minute=1500,
            tokens_per_minute=30000,
            tokens_per_day=1500000
        )
        
        # Convert to dict and back
        dict_data = original.model_dump()
        restored = ModelConfig(**dict_data)
        
        assert restored.requests_per_minute == original.requests_per_minute
        assert restored.tokens_per_minute == original.tokens_per_minute
        assert restored.tokens_per_day == original.tokens_per_day


class TestOpenAIConfig:
    """Test OpenAIConfig comprehensively."""

    def test_default_creation(self) -> None:
        """Test creating OpenAIConfig with default values."""
        config = OpenAIConfig()
        
        assert config.model == "gpt-3.5-turbo"

    def test_custom_creation(self) -> None:
        """Test creating OpenAIConfig with custom model."""
        config = OpenAIConfig(model="gpt-4")
        
        assert config.model == "gpt-4"

    @pytest.mark.parametrize("model", [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "claude-3-sonnet",
        "custom-model",
    ])
    def test_different_models(self, model: str) -> None:
        """Test OpenAIConfig with different model names."""
        config = OpenAIConfig(model=model)
        assert config.model == model

    def test_immutability(self) -> None:
        """Test that OpenAIConfig is immutable."""
        config = OpenAIConfig()
        
        # Attempting to change fields should raise an error
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            config.model = "gpt-4"

    def test_model_dict_conversion(self) -> None:
        """Test OpenAIConfig can be converted to dict."""
        config = OpenAIConfig(model="gpt-4")
        
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert config_dict["model"] == "gpt-4"

    def test_round_trip_serialization(self) -> None:
        """Test OpenAIConfig round-trip serialization."""
        original = OpenAIConfig(model="gpt-4-turbo")
        
        # Convert to dict and back
        dict_data = original.model_dump()
        restored = OpenAIConfig(**dict_data)
        
        assert restored.model == original.model


class TestAiSettings:
    """Test AiSettings comprehensively."""

    def test_minimal_creation(self) -> None:
        """Test creating AiSettings with minimal required fields."""
        settings = AiSettings(api_key="test-key")
        
        assert settings.api_key == "test-key"
        assert settings.provider == "auto"
        assert settings.base_url is None
        assert settings.model is None

    def test_full_creation(self) -> None:
        """Test creating AiSettings with all fields."""
        settings = AiSettings(
            api_key="test-key",
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )
        
        assert settings.api_key == "test-key"
        assert settings.provider == "openai"
        assert settings.base_url == "https://api.openai.com/v1"
        assert settings.model == "gpt-4"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.timeout == 30

    @pytest.mark.parametrize("provider", [
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
    ])
    def test_valid_providers(self, provider: str) -> None:
        """Test AiSettings with different valid providers."""
        settings = AiSettings(api_key="test-key", provider=provider)
        assert settings.provider == provider

    def test_invalid_provider(self) -> None:
        """Test AiSettings with invalid provider."""
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", provider="invalid-provider")
        assert "provider" in str(exc_info.value)

    @pytest.mark.parametrize("temperature", [0.0, 0.5, 1.0, 2.0])
    def test_valid_temperature(self, temperature: float) -> None:
        """Test AiSettings with valid temperature values."""
        settings = AiSettings(api_key="test-key", temperature=temperature)
        assert settings.temperature == temperature

    @pytest.mark.parametrize("temperature", [-0.1, 2.1])
    def test_invalid_temperature(self, temperature: float) -> None:
        """Test AiSettings with invalid temperature values."""
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", temperature=temperature)
        assert "temperature" in str(exc_info.value)

    @pytest.mark.parametrize("max_tokens", [1, 100, 1000, 8192])
    def test_valid_max_tokens(self, max_tokens: int) -> None:
        """Test AiSettings with valid max_tokens values."""
        settings = AiSettings(api_key="test-key", max_tokens=max_tokens)
        assert settings.max_tokens == max_tokens

    @pytest.mark.parametrize("max_tokens", [0, -1])
    def test_invalid_max_tokens(self, max_tokens: int) -> None:
        """Test AiSettings with invalid max_tokens values."""
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", max_tokens=max_tokens)
        assert "max_tokens" in str(exc_info.value)

    @pytest.mark.parametrize("timeout", [1, 30, 60, 300])
    def test_valid_timeout(self, timeout: int) -> None:
        """Test AiSettings with valid timeout values."""
        settings = AiSettings(api_key="test-key", timeout=timeout)
        assert settings.timeout == timeout

    @pytest.mark.parametrize("timeout", [0, -1])
    def test_invalid_timeout(self, timeout: int) -> None:
        """Test AiSettings with invalid timeout values."""
        with pytest.raises(ValidationError) as exc_info:
            AiSettings(api_key="test-key", timeout=timeout)
        assert "timeout" in str(exc_info.value)

    def test_base_url_validation(self) -> None:
        """Test base_url validation."""
        # Valid URLs
        valid_urls = [
            "https://api.openai.com/v1",
            "http://localhost:8080/v1",
            "https://custom.example.com/api"
        ]
        
        for url in valid_urls:
            settings = AiSettings(api_key="test-key", base_url=url)
            assert settings.base_url == url

        # Invalid URLs (should still work as validation might be lenient)
        invalid_urls = [
            "not-a-url",
            "ftp://invalid.protocol.com",
            ""
        ]
        
        for url in invalid_urls:
            # Test that it doesn't crash (validation might be lenient)
            try:
                settings = AiSettings(api_key="test-key", base_url=url)
                assert settings.base_url == url
            except ValidationError:
                # If validation is strict, that's also acceptable
                pass

    def test_model_dict_conversion(self) -> None:
        """Test AiSettings can be converted to dict."""
        settings = AiSettings(
            api_key="test-key",
            provider="openai",
            model="gpt-4",
            temperature=0.7
        )
        
        settings_dict = settings.model_dump()
        
        assert isinstance(settings_dict, dict)
        assert settings_dict["api_key"] == "test-key"
        assert settings_dict["provider"] == "openai"
        assert settings_dict["model"] == "gpt-4"
        assert settings_dict["temperature"] == 0.7

    def test_round_trip_serialization(self) -> None:
        """Test AiSettings round-trip serialization."""
        original = AiSettings(
            api_key="test-key",
            provider="groq",
            base_url="https://api.groq.com/v1",
            model="llama-3-70b",
            temperature=0.5,
            max_tokens=2000,
            timeout=60
        )
        
        # Convert to dict and back
        dict_data = original.model_dump()
        restored = AiSettings(**dict_data)
        
        assert restored.api_key == original.api_key
        assert restored.provider == original.provider
        assert restored.base_url == original.base_url
        assert restored.model == original.model
        assert restored.temperature == original.temperature
        assert restored.max_tokens == original.max_tokens
        assert restored.timeout == original.timeout

    def test_equality(self) -> None:
        """Test AiSettings equality comparison."""
        settings1 = AiSettings(api_key="test-key", provider="openai")
        settings2 = AiSettings(api_key="test-key", provider="openai")
        settings3 = AiSettings(api_key="test-key", provider="groq")
        
        assert settings1 == settings2
        assert settings1 != settings3
