"""Tests for smart setup functionality including model checking and caching."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


class TestSmartSetup:
    """Test suite for smart setup functionality."""

    def test_ai_settings_update_check_days_default(self):
        """Test that update_check_days has correct default value."""
        settings = AiSettings()
        assert settings.update_check_days == 30

    def test_ai_settings_update_check_days_from_env(self, monkeypatch):
        """Test that update_check_days loads from environment variable."""
        monkeypatch.setenv("AI_UPDATE_CHECK_DAYS", "7")
        settings = AiSettings()
        assert settings.update_check_days == 7

    def test_ai_settings_update_check_days_explicit(self):
        """Test that update_check_days can be set explicitly."""
        settings = AiSettings(update_check_days=14)
        assert settings.update_check_days == 14

    def test_ai_settings_update_check_days_validation(self):
        """Test that update_check_days validates constraints."""
        # Valid values
        settings = AiSettings(update_check_days=1)
        assert settings.update_check_days == 1
        
        settings = AiSettings(update_check_days=365)
        assert settings.update_check_days == 365
        
        # Invalid values
        with pytest.raises(ValueError):
            AiSettings(update_check_days=0)
        
        with pytest.raises(ValueError):
            AiSettings(update_check_days=-1)

    def test_should_check_for_updates_no_cache(self):
        """Test _should_check_for_updates when no cache exists."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path("/nonexistent")
            
            result = AiSettings._should_check_for_updates(30)
            assert result is True

    def test_should_check_for_updates_old_cache(self, tmp_path):
        """Test _should_check_for_updates when cache is old."""
        # Create old cache file
        cache_file = tmp_path / ".ai_utilities_model_cache.json"
        old_data = {
            "last_check": (datetime.now() - timedelta(days=40)).isoformat()
        }
        cache_file.write_text(json.dumps(old_data))
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = AiSettings._should_check_for_updates(30)
            assert result is True

    def test_should_check_for_updates_recent_cache(self, tmp_path):
        """Test _should_check_for_updates when cache is recent."""
        # Create recent cache file
        cache_file = tmp_path / ".ai_utilities_model_cache.json"
        recent_data = {
            "last_check": (datetime.now() - timedelta(days=10)).isoformat()
        }
        cache_file.write_text(json.dumps(recent_data))
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = AiSettings._should_check_for_updates(30)
            assert result is False

    def test_check_for_updates_cached_result(self, tmp_path):
        """Test that cached results are returned when within interval."""
        # Create a cache file with recent timestamp
        cache_file = tmp_path / ".ai_utilities_model_cache.json"
        cache_data = {
            "last_check": (datetime.now() - timedelta(days=1)).isoformat(),
            "has_updates": True,
            "new_models": ["test-model-1o"],
            "current_models": ["test-model-1", "test-model-2", "test-model-1o"],
            "total_models": 3
        }
        cache_file.write_text(json.dumps(cache_data))
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            # Should return cached result (no API call)
            result = AiSettings.check_for_updates("test-key", check_interval_days=30)
            
            assert result['has_updates'] is True
            assert result['cached'] is True
            assert result['new_models'] == ["test-model-1o"]

    def test_smart_setup_missing_api_key(self, monkeypatch):
        """Test smart_setup when API key is missing."""
        # Remove API key from environment
        monkeypatch.delenv("AI_API_KEY", raising=False)
        
        with patch('ai_utilities.AiSettings.interactive_setup') as mock_interactive:
            mock_settings = MagicMock()
            mock_settings.api_key = "new-key"
            mock_interactive.return_value = mock_settings
            
            result = AiSettings.smart_setup()
            
            mock_interactive.assert_called_once()
            assert result == mock_settings

    def test_smart_setup_with_api_key(self, monkeypatch):
        """Test smart_setup when API key exists."""
        monkeypatch.setenv("AI_API_KEY", "test-key")
        
        with patch('ai_utilities.AiSettings._should_check_for_updates', return_value=False):
            settings = AiSettings.smart_setup()
            
            assert settings.api_key == "test-key"

    def test_ai_client_initialization_with_provider(self):
        """Test AiClient initialization with explicit provider."""
        fake_provider = FakeProvider()
        
        # Test basic initialization with provider
        client = AiClient(provider=fake_provider)
        
        assert client.provider == fake_provider
        assert client.settings is not None

    def test_ai_client_check_for_updates(self, monkeypatch):
        """Test AiClient.check_for_updates method."""
        monkeypatch.setenv("AI_API_KEY", "test-key")
        
        with patch('ai_utilities.AiSettings.check_for_updates') as mock_check:
            mock_check.return_value = {
                'has_updates': True,
                'new_models': ['test-model-1o'],
                'cached': False
            }
            
            fake_provider = FakeProvider()
            client = AiClient(provider=fake_provider)
            result = client.check_for_updates()
            
            mock_check.assert_called_once_with("test-key", 30)
            assert result['has_updates'] is True

    def test_ai_client_check_for_updates_force(self, monkeypatch):
        """Test AiClient.check_for_updates with force=True."""
        monkeypatch.setenv("AI_API_KEY", "test-key")
        
        with patch('ai_utilities.AiSettings.check_for_updates') as mock_check:
            mock_check.return_value = {
                'has_updates': False,
                'new_models': [],
                'cached': False
            }
            
            fake_provider = FakeProvider()
            client = AiClient(provider=fake_provider)
            result = client.check_for_updates(force_check=True)
            
            mock_check.assert_called_once_with("test-key", check_interval_days=0)
            assert result['has_updates'] is False

    def test_ai_client_check_for_updates_no_api_key(self) -> None:
        """Test AiClient.check_for_updates when no API key is configured."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)

        result = client.check_for_updates()

        # New behavior: allow cached lookup without API key
        if "error" in result:
            assert isinstance(result["error"], str)
        else:
            assert result.get("cached") is True
            assert isinstance(result.get("current_models"), list)
            assert isinstance(result.get("new_models"), list)
            # Contract: verify update check result structure (provider contract)
            assert len(result) >= 4  # Should have at least 4 keys: cached, current_models, new_models, has_updates
            expected_keys = {"cached", "current_models", "new_models", "has_updates"}
            assert expected_keys.issubset(result.keys())

    def test_ai_client_reconfigure(self):
        """Test AiClient.reconfigure method."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        with patch('ai_utilities.AiSettings.interactive_setup') as mock_interactive:
            # Patch the specific import path used in reconfigure method
            import sys
            original_module = sys.modules.get('ai_utilities.providers.openai_provider')
            
            # Create a mock module
            mock_module = MagicMock()
            mock_module.OpenAIProvider = MagicMock(return_value=fake_provider)
            sys.modules['ai_utilities.providers.openai_provider'] = mock_module
            
            try:
                mock_settings = AiSettings(api_key="new-key", model="test-model-1o")
                mock_interactive.return_value = mock_settings
                
                client.reconfigure()
                
                mock_interactive.assert_called_once_with(force_reconfigure=True)
                assert client.settings.api_key == "new-key"
                assert client.settings.model == "test-model-1o"
                assert client.provider == fake_provider
                
                # Verify OpenAIProvider was called with the new settings
                mock_module.OpenAIProvider.assert_called_once_with(mock_settings)
            finally:
                # Restore original module
                if original_module is not None:
                    sys.modules['ai_utilities.providers.openai_provider'] = original_module
                elif 'ai_utilities.providers.openai_provider' in sys.modules:
                    del sys.modules['ai_utilities.providers.openai_provider']

    def validate_model_availability(cls, api_key: str, model: str, *, strict: bool = True) -> bool:
        """Check if a model is available in the OpenAI API.

        Args:
            api_key: OpenAI API key.
            model: Model name to validate.
            strict: If True, return False on errors (deterministic for tests/CI).
                    If False, return True on errors (legacy/permissive UX).

        Returns:
            True if model is available; False otherwise.
        """
        if not api_key or not model:
            return False

        try:
            client: Any = OpenAI(api_key=api_key)
            models: Any = client.models.list()

            data: Iterable[Any] = getattr(models, "data", []) or []
            available_models: set[str] = {
                str(item.id) for item in data if getattr(item, "id", None) is not None
            }

            return model in available_models
        except Exception:
            # Strict mode => deterministic False (best for unit tests / CI).
            # Permissive mode => legacy behavior "assume it might work".
            return False if strict else True

    def test_cache_file_structure(self, tmp_path):
        """Test that cache file has correct structure."""
        cache_file = tmp_path / ".ai_utilities_model_cache.json"
        cache_data = {
            "last_check": datetime.now().isoformat(),
            "has_updates": True,
            "new_models": ["test-model-1o"],
            "current_models": ["test-model-1", "test-model-2", "test-model-1o"],
            "total_models": 3
        }
        cache_file.write_text(json.dumps(cache_data))
        
        # Verify cache file can be read and has expected structure
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = AiSettings.check_for_updates("test-key", check_interval_days=30)
            
            assert result['has_updates'] is True
            assert result['cached'] is True
            # Contract: verify cache structure contains expected fields (provider contract)
            expected_keys = {'last_check', 'new_models', 'current_models', 'total_models'}
            assert expected_keys.issubset(result.keys())
