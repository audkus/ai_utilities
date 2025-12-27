"""Tests for AiSettings configuration system."""

import os
import tempfile
from pathlib import Path

import pytest

from src.ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


def test_ai_settings_defaults():
    """Test that AiSettings loads correct defaults."""
    settings = AiSettings()
    
    assert settings.model == "test-model-1"
    assert settings.temperature == 0.7
    assert settings.timeout == 30
    assert settings.api_key is None
    assert settings.max_tokens is None
    assert settings.base_url is None
    assert settings.update_check_days == 30


def test_ai_settings_from_env_vars(monkeypatch):
    """Test that AiSettings loads from environment variables."""
    # Set environment variables
    monkeypatch.setenv("AI_API_KEY", "test-key-from-env")
    monkeypatch.setenv("AI_MODEL", "test-model-2")
    monkeypatch.setenv("AI_TEMPERATURE", "0.5")
    monkeypatch.setenv("AI_MAX_TOKENS", "1000")
    monkeypatch.setenv("AI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("AI_TIMEOUT", "60")
    monkeypatch.setenv("AI_UPDATE_CHECK_DAYS", "7")
    
    settings = AiSettings()
    
    assert settings.api_key == "test-key-from-env"
    assert settings.model == "test-model-2"
    assert settings.temperature == 0.5
    assert settings.max_tokens == 1000
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.timeout == 60
    assert settings.update_check_days == 7


def test_ai_settings_explicit_override_env(monkeypatch):
    """Test that explicit settings override environment variables."""
    # Set environment variables
    monkeypatch.setenv("AI_API_KEY", "env-key")
    monkeypatch.setenv("AI_MODEL", "test-model-2")
    
    # Create explicit settings
    explicit_settings = AiSettings(
        api_key="explicit-key",
        model="test-model-1"
    )
    
    assert explicit_settings.api_key == "explicit-key"
    assert explicit_settings.model == "test-model-1"


def test_ai_settings_validation():
    """Test that AiSettings validates constraints."""
    # Valid temperature range
    settings = AiSettings(temperature=1.5)
    assert settings.temperature == 1.5
    
    # Invalid temperature (too high)
    with pytest.raises(ValueError):
        AiSettings(temperature=3.0)
    
    # Invalid temperature (too low)
    with pytest.raises(ValueError):
        AiSettings(temperature=-0.1)
    
    # Invalid max_tokens (too low)
    with pytest.raises(ValueError):
        AiSettings(max_tokens=0)
    
    # Invalid timeout (too low)
    with pytest.raises(ValueError):
        AiSettings(timeout=0)


def test_ai_settings_from_ini():
    """Test loading settings from INI file."""
    ini_content = """[AI]
use_ai = true
ai_provider = openai

[openai]
model = test-model-2
api_key = ini-api-key-here

[test-model-1]
requests_per_minute = 5000
tokens_per_minute = 450000
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(ini_content)
        f.flush()
        
        try:
            settings = AiSettings.from_ini(f.name)
            
            assert settings.model == "test-model-2"
            assert settings.api_key == "ini-api-key-here"
            # Should still have defaults for other fields
            assert settings.temperature == 0.7
            assert settings.timeout == 30
            
        finally:
            os.unlink(f.name)


def test_ai_settings_from_ini_missing_file():
    """Test that from_ini raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        AiSettings.from_ini("/nonexistent/config.ini")


def test_ai_settings_from_ini_with_env_placeholder():
    """Test that from_ini handles AI_API_KEY placeholder."""
    ini_content = """[openai]
model = test-model-2
api_key = AI_API_KEY
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(ini_content)
        f.flush()
        
        try:
            settings = AiSettings.from_ini(f.name)
            
            assert settings.model == "test-model-2"
            # The placeholder is returned as-is (user should replace it with actual key)
            assert settings.api_key == "AI_API_KEY"
            
        finally:
            os.unlink(f.name)


def test_ai_client_uses_env_vars(monkeypatch):
    """Test that AiClient loads settings from environment variables."""
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "test-model-2")
    
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, auto_setup=False)
    
    assert client.settings.api_key == "test-key"
    assert client.settings.model == "test-model-2"


def test_ai_client_explicit_settings_override_env(monkeypatch):
    """Test that explicit settings passed to AiClient override environment."""
    monkeypatch.setenv("AI_API_KEY", "env-key")
    monkeypatch.setenv("AI_MODEL", "test-model-2")
    
    explicit_settings = AiSettings(
        api_key="explicit-key",
        model="test-model-1"
    )
    
    fake_provider = FakeProvider()
    client = AiClient(settings=explicit_settings, provider=fake_provider, auto_setup=False)
    
    assert client.settings.api_key == "explicit-key"
    assert client.settings.model == "test-model-1"


def test_ai_client_no_config_file_access():
    """Test that creating AiClient does not touch config.ini or filesystem."""
    # This test ensures no import-time side effects
    import tempfile
    
    # Create a temporary directory with no config.ini
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Creating AiClient should not fail or create files
            fake_provider = FakeProvider()
            client = AiClient(provider=fake_provider, auto_setup=False)
            
            # Should work fine without any config files
            assert client.settings.model == "test-model-1"  # Default
            
            # Verify no config.ini was created
            assert not (temp_path / "config.ini").exists()
            
        finally:
            os.chdir(original_cwd)


def test_ai_settings_extra_fields_ignored(monkeypatch):
    """Test that extra environment variables are ignored."""
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_UNKNOWN_FIELD", "should-be-ignored")
    
    settings = AiSettings()
    
    assert settings.api_key == "test-key"
    # Should not have unknown_field
    assert not hasattr(settings, "unknown_field")


def test_ai_settings_from_toml_style_fallback():
    """Test that from_ini can handle basic configuration parsing."""
    ini_content = """[openai]
model = custom-model
api_key = custom-key
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(ini_content)
        f.flush()
        
        try:
            settings = AiSettings.from_ini(f.name)
            assert settings.model == "custom-model"
            assert settings.api_key == "custom-key"
            
        finally:
            os.unlink(f.name)
