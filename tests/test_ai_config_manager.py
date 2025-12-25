"""
test_ai_config_manager.py

Tests for AIConfigManager with Pydantic models and dynamic rate limits.
"""

import pytest
import tempfile
import shutil
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from configparser import ConfigParser

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.ai_config_manager import AIConfigManager
from ai_utilities.config_models import AIConfig, ModelConfig, OpenAIConfig
from ai_utilities.exceptions import ConfigError


class TestAIConfigManager:
    """Test AIConfigManager functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.ini"
        self.api_key = "test-api-key"
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_without_api_key(self):
        """Test AIConfigManager initialization without API key."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        assert manager.config_path == str(self.config_path)
        assert manager._config is None
        assert manager._rate_limit_fetcher is None
    
    def test_initialization_with_api_key(self):
        """Test AIConfigManager initialization with API key."""
        manager = AIConfigManager(
            config_path=str(self.config_path),
            api_key=self.api_key
        )
        
        assert manager.config_path == str(self.config_path)
        assert manager._config is None
        assert manager._rate_limit_fetcher is not None
        assert manager._rate_limit_fetcher.cache_days == 30
    
    def test_load_config_basic(self):
        """Test basic configuration loading."""
        manager = AIConfigManager(config_path=str(self.config_path))
        config = manager.load_config()
        
        assert isinstance(config, AIConfig)
        assert config.use_ai is True
        assert config.ai_provider == "openai"
        assert len(config.models) >= 3
        assert manager._config is config
    
    def test_load_config_with_data(self):
        """Test loading configuration with custom data."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        config_data = {
            "use_ai": False,
            "openai": {
                "model": "test-model-2",
                "temperature": 0.5
            }
        }
        
        config = manager.load_config(config_data)
        
        assert config.use_ai is False
        assert config.openai.model == "test-model-2"
        assert config.openai.temperature == 0.5
    
    def test_load_config_invalid_data(self):
        """Test loading configuration with invalid data."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        with pytest.raises(ConfigError):
            manager.load_config({"use_ai": "invalid_boolean"})
    
    def test_load_from_file_nonexistent(self):
        """Test loading from non-existent file."""
        manager = AIConfigManager(config_path="nonexistent.ini")
        
        # Should fall back to defaults
        config = manager.load_from_file()
        assert isinstance(config, AIConfig)
        assert config.use_ai is True
    
    def test_load_from_file_valid(self):
        """Test loading from valid configuration file."""
        # Create a test config file
        config_parser = ConfigParser()
        config_parser.add_section('AI')
        config_parser.set('AI', 'use_ai', 'false')
        config_parser.set('AI', 'ai_provider', 'openai')
        
        config_parser.add_section('openai')
        config_parser.set('openai', 'model', 'test-model-2')
        config_parser.set('openai', 'temperature', '0.3')
        
        with open(self.config_path, 'w') as f:
            config_parser.write(f)
        
        manager = AIConfigManager(config_path=str(self.config_path))
        config = manager.load_from_file()
        
        assert config.use_ai is False
        assert config.openai.model == "test-model-2"
        assert config.openai.temperature == 0.3
    
    def test_save_config(self):
        """Test saving configuration to file."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        # Create custom config
        config = AIConfig(
            use_ai=False,
            openai=OpenAIConfig(
                model="test-model-2",
                temperature=0.5
            )
        )
        
        manager.save_config(config)
        
        # Verify file was created and contains correct data
        assert self.config_path.exists()
        
        # Load and verify
        loaded_config = manager.load_from_file()
        assert loaded_config.use_ai is False
        assert loaded_config.openai.model == "test-model-2"
        assert loaded_config.openai.temperature == 0.5
    
    def test_get_model_config(self):
        """Test getting model configuration."""
        manager = AIConfigManager(config_path=str(self.config_path))
        config = manager.load_config()
        
        gpt4_config = manager.get_model_config("test-model-1")
        assert isinstance(gpt4_config, ModelConfig)
        assert gpt4_config.requests_per_minute > 0
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_load_config_with_dynamic_limits(self, mock_rate_limit_fetcher):
        """Test loading configuration with dynamic rate limits."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        # Mock rate limits
        mock_limits = {
            "test-model-1": Mock()
        }
        mock_limits["test-model-1"].to_model_config.return_value = ModelConfig(
            requests_per_minute=6000,
            tokens_per_minute=500000,
            tokens_per_day=1500000
        )
        mock_fetcher_instance.get_rate_limits.return_value = mock_limits
        
        manager = AIConfigManager(
            config_path=str(self.config_path),
            api_key=self.api_key
        )
        
        config = manager.load_config_with_dynamic_limits()
        
        # Verify rate limits were fetched and applied
        mock_fetcher_instance.get_rate_limits.assert_called_once()
        assert config.models["test-model-1"].requests_per_minute == 6000
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_load_config_with_dynamic_limits_failure(self, mock_rate_limit_fetcher):
        """Test handling of dynamic rate limit fetch failure."""
        # Mock rate limit fetcher that fails
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_rate_limits.side_effect = Exception("API Error")
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        manager = AIConfigManager(
            config_path=str(self.config_path),
            api_key=self.api_key
        )
        
        # Should fall back to defaults
        config = manager.load_config_with_dynamic_limits()
        assert isinstance(config, AIConfig)
        assert len(config.models) >= 3
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_update_rate_limits(self, mock_rate_limit_fetcher):
        """Test updating rate limits."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        # Mock rate limits
        mock_limits = {
            "test-model-1": Mock()
        }
        mock_limits["test-model-1"].to_model_config.return_value = ModelConfig(
            requests_per_minute=7000,
            tokens_per_minute=600000,
            tokens_per_day=1800000
        )
        mock_fetcher_instance.get_rate_limits.return_value = mock_limits
        
        manager = AIConfigManager(
            config_path=str(self.config_path),
            api_key=self.api_key
        )
        
        # Load initial config
        initial_config = manager.load_config()
        assert initial_config.models["test-model-1"].requests_per_minute != 7000
        
        # Update rate limits
        result = manager.update_rate_limits()
        
        assert result is True
        assert manager._config.models["test-model-1"].requests_per_minute == 7000
    
    def test_update_rate_limits_no_fetcher(self):
        """Test updating rate limits without rate limit fetcher."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        result = manager.update_rate_limits()
        assert result is False
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_should_update_rate_limits(self, mock_rate_limit_fetcher):
        """Test checking if rate limits should be updated."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        # Test with no cache
        mock_fetcher_instance.get_cache_status.return_value = {"cached": False}
        manager = AIConfigManager(api_key=self.api_key)
        
        should_update = manager.should_update_rate_limits()
        assert should_update is True
        
        # Test with fresh cache (5 days old)
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 5.0
        }
        
        should_update = manager.should_update_rate_limits()
        assert should_update is False
        
        # Test with old cache (30 days old)
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 30.0
        }
        
        should_update = manager.should_update_rate_limits()
        assert should_update is True
    
    def test_should_update_rate_limits_no_fetcher(self):
        """Test checking update status without rate limit fetcher."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        should_update = manager.should_update_rate_limits()
        assert should_update is False
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_update_rate_limits_if_needed(self, mock_rate_limit_fetcher):
        """Test updating rate limits only if needed."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        # Test when update is not needed
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 5.0
        }
        
        manager = AIConfigManager(api_key=self.api_key)
        result = manager.update_rate_limits_if_needed()
        assert result is False
        
        # Test when update is needed
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 30.0
        }
        mock_fetcher_instance.get_rate_limits.return_value = {}
        
        result = manager.update_rate_limits_if_needed()
        assert result is True
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        status = manager.get_rate_limit_status()
        
        assert status["dynamic_limits_enabled"] is False
        assert "reason" in status
        assert status["reason"] == "No API key provided"
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_get_rate_limit_status_with_fetcher(self, mock_rate_limit_fetcher):
        """Test getting rate limit status with fetcher."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 10.0,
            "models_count": 8
        }
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        manager = AIConfigManager(api_key=self.api_key)
        manager.load_config()  # Load config to have models
        
        status = manager.get_rate_limit_status()
        
        assert status["dynamic_limits_enabled"] is True
        assert "cache_status" in status
        assert "available_models" in status
        assert len(status["available_models"]) >= 3
    
    def test_clear_rate_limit_cache(self):
        """Test clearing rate limit cache."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        # Should not raise exception without fetcher
        manager.clear_rate_limit_cache()
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_clear_rate_limit_cache_with_fetcher(self, mock_rate_limit_fetcher):
        """Test clearing rate limit cache with fetcher."""
        # Mock rate limit fetcher
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        manager = AIConfigManager(api_key=self.api_key)
        manager.clear_rate_limit_cache()
        
        mock_fetcher_instance.clear_cache.assert_called_once()


class TestAIConfigManagerIntegration:
    """Integration tests for AIConfigManager."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.ini"
        self.api_key = "test-api-key"
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_configuration_workflow(self):
        """Test complete configuration workflow."""
        manager = AIConfigManager(
            config_path=str(self.config_path),
            api_key=self.api_key
        )
        
        # Load configuration with dynamic limits
        config = manager.load_config_with_dynamic_limits()
        
        # Verify configuration
        assert isinstance(config, AIConfig)
        assert config.use_ai is True
        assert len(config.models) >= 3
        
        # Save configuration
        manager.save_config(config)
        assert self.config_path.exists()
        
        # Load from file
        loaded_config = manager.load_from_file()
        assert isinstance(loaded_config, AIConfig)
        assert loaded_config.use_ai is True
    
    def test_config_file_roundtrip(self):
        """Test configuration file save/load roundtrip."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        # Create custom configuration
        original_config = AIConfig(
            use_ai=False,
            openai=OpenAIConfig(
                model="test-model-2",
                temperature=0.3,
                max_tokens=500
            ),
            models={
                "custom-model": ModelConfig(
                    requests_per_minute=1000,
                    tokens_per_minute=100000,
                    tokens_per_day=1000000
                )
            }
        )
        
        # Save and reload
        manager.save_config(original_config)
        loaded_config = manager.load_from_file()
        
        # Verify data integrity
        assert loaded_config.use_ai is False
        assert loaded_config.openai.model == "test-model-2"
        assert loaded_config.openai.temperature == 0.3
        assert loaded_config.openai.max_tokens == 500
        assert "custom-model" in loaded_config.models
        assert loaded_config.models["custom-model"].requests_per_minute == 1000
    
    def test_environment_variable_integration(self):
        """Test environment variable integration."""
        from ai_utilities.env_overrides import override_env
        
        # Test with environment variable overrides
        with override_env({
            'AI_USE_AI': 'false',
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '0.2'
        }):
            manager = AIConfigManager(config_path=str(self.config_path))
            config = manager.load_config()
            
            # Verify environment variables were applied
            assert config.use_ai is False
            assert config.openai.model == 'test-model-2'
            assert config.openai.temperature == 0.2
    
    @patch('ai_utilities.ai_config_manager.RateLimitFetcher')
    def test_dynamic_limits_integration(self, mock_rate_limit_fetcher):
        """Test dynamic rate limits integration."""
        # Mock rate limit fetcher with realistic data
        mock_fetcher_instance = Mock()
        mock_rate_limit_fetcher.return_value = mock_fetcher_instance
        
        mock_limits = {
            "test-model-1": Mock(),
            "test-model-2": Mock(),
            "test-model-1-turbo": Mock()
        }
        
        # Configure mock limits
        for model_name in mock_limits:
            mock_limits[model_name].to_model_config.return_value = ModelConfig(
                requests_per_minute=8000,
                tokens_per_minute=800000,
                tokens_per_day=2400000
            )
        
        mock_fetcher_instance.get_rate_limits.return_value = mock_limits
        mock_fetcher_instance.get_cache_status.return_value = {
            "cached": True,
            "cache_age_days": 5.0,
            "models_count": 3
        }
        
        manager = AIConfigManager(api_key=self.api_key)
        
        # Load with dynamic limits
        config = manager.load_config_with_dynamic_limits()
        
        # Verify dynamic limits were applied
        for model_name in mock_limits:
            assert model_name in config.models
            assert config.models[model_name].requests_per_minute == 8000
        
        # Test status checking
        status = manager.get_rate_limit_status()
        assert status["dynamic_limits_enabled"] is True
        assert status["cache_status"]["models_count"] == 3
        
        # Test update checking
        should_update = manager.should_update_rate_limits()
        assert should_update is False  # Cache is fresh (5 days)
    
    def test_error_handling_workflow(self):
        """Test error handling throughout workflow."""
        manager = AIConfigManager(config_path=str(self.config_path))
        
        # Test invalid configuration data
        with pytest.raises(ConfigError):
            manager.load_config({"use_ai": "not_a_boolean"})
        
        # Test invalid configuration file
        invalid_config_path = Path(self.temp_dir) / "invalid.ini"
        with open(invalid_config_path, 'w') as f:
            f.write("invalid ini content [")
        
        # Should fall back to defaults
        config = manager.load_from_file(str(invalid_config_path))
        assert isinstance(config, AIConfig)
        assert config.use_ai is True
