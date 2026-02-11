"""
test_rate_limit_fetching.py

Tests for dynamic rate limit fetching system with 30-day cache.
"""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the entire openai_client module to avoid import errors
import sys
sys.modules['ai_utilities.openai_client'] = Mock()

from ai_utilities.config_models import ModelConfig
from ai_utilities.rate_limit_fetcher import RateLimitFetcher, RateLimitInfo


class TestRateLimitInfo:
    """Test RateLimitInfo dataclass."""
    
    def test_rate_limit_info_creation(self):
        """Test RateLimitInfo creation."""
        now = datetime.now()
        info = RateLimitInfo(
            model_name="test-model-1",
            requests_per_minute=5000,
            tokens_per_minute=450000,
            tokens_per_day=1350000,
            last_updated=now
        )
        
        assert info.model_name == "test-model-1"
        assert info.requests_per_minute == 5000
        assert info.tokens_per_minute == 450000
        assert info.tokens_per_day == 1350000
        assert info.last_updated == now
    
    def test_to_model_config(self):
        """Test conversion to ModelConfig."""
        info = RateLimitInfo(
            model_name="test-model-1",
            requests_per_minute=5000,
            tokens_per_minute=450000,
            tokens_per_day=1350000,
            last_updated=datetime.now()
        )
        
        config = info.to_model_config()
        
        assert isinstance(config, ModelConfig)
        assert config.requests_per_minute == 5000
        assert config.tokens_per_minute == 450000
        assert config.tokens_per_day == 1350000


class TestRateLimitFetcher:
    """Test RateLimitFetcher functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.api_key = "test-api-key"
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test RateLimitFetcher initialization."""
        fetcher = RateLimitFetcher(
            api_key=self.api_key,
            cache_dir=self.temp_dir,
            cache_days=30
        )
        
        assert fetcher.api_key == self.api_key
        assert fetcher.cache_dir == Path(self.temp_dir)
        assert fetcher.cache_days == 30
        assert fetcher.cache_file == Path(self.temp_dir) / "openai_rate_limits.json"
        assert fetcher.cache_dir.exists()
    
    def test_initialization_default_cache_dir(self):
        """Test RateLimitFetcher with default cache directory."""
        fetcher = RateLimitFetcher(api_key=self.api_key)
        
        # Should use home directory
        expected_dir = Path.home() / ".ai_utilities" / "rate_limits"
        assert fetcher.cache_dir == expected_dir
    
    @patch('ai_utilities.openai_client._create_openai_sdk_client')
    def test_get_rate_limits_first_time(self, mock_create_client):
        """Test getting rate limits for the first time (no cache)."""
        # Mock OpenAI client
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.headers = {
            'x-ratelimit-limit-requests': '3000',
            'x-ratelimit-limit-tokens': '2000000'
        }
        mock_client_instance.create_chat_completion.return_value = mock_response
        mock_create_client.return_value = mock_client_instance
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        limits = fetcher.get_rate_limits()
        
        # Should have fetched limits for known models
        assert len(limits) > 0
        assert "test-model-1" in limits
        assert "test-model-2" in limits
        
        # Verify cache was created
        assert fetcher.cache_file.exists()
        
        # Verify cache content
        with open(fetcher.cache_file) as f:
            cache_data = json.load(f)
        assert 'models' in cache_data
        assert 'last_updated' in cache_data
    
    def test_get_rate_limits_from_cache(self):
        """Test getting rate limits from cache."""
        # Create fetcher with temporary cache directory
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Create a cache file
        cache_data = {
            'last_updated': datetime.now().isoformat(),
            'models': {
                'test-model-1': {
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 450000,
                    'tokens_per_day': 1350000,
                    'last_updated': datetime.now().isoformat()
                }
            }
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        limits = fetcher.get_rate_limits()
        
        # Should load from cache
        assert len(limits) == 1
        assert "test-model-1" in limits
        assert limits["test-model-1"].requests_per_minute == 5000
    
    def test_get_rate_limits_cache_expired(self):
        """Test getting rate limits when cache is expired."""
        # Create fetcher with temporary cache directory
        fetcher = RateLimitFetcher(api_key=self.api_key)
        
        # Create an old cache file (31 days ago)
        old_date = datetime.now() - timedelta(days=31)
        cache_data = {
            'last_updated': old_date.isoformat(),
            'models': {
                'test-model-1': {
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 450000,
                    'tokens_per_day': 1350000,
                    'last_updated': old_date.isoformat()
                }
            }
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        with patch('ai_utilities.openai_client._create_openai_sdk_client') as mock_openai_client:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.headers = {}
            mock_client_instance.create_chat_completion.return_value = mock_response
            mock_openai_client.return_value = mock_client_instance
            
            fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
            limits = fetcher.get_rate_limits()
            
            # Should fetch fresh data (cache expired)
            assert len(limits) >= 8  # Known defaults
    
    def test_get_rate_limits_force_refresh(self):
        """Test force refresh ignoring cache."""
        # Create fetcher with temporary cache directory
        fetcher = RateLimitFetcher(api_key=self.api_key)
        
        # Create a fresh cache file
        cache_data = {
            'last_updated': datetime.now().isoformat(),
            'models': {
                'test-model-1': {
                    'requests_per_minute': 1000,  # Old value
                    'tokens_per_minute': 100000,
                    'tokens_per_day': 1000000,
                    'last_updated': datetime.now().isoformat()
                }
            }
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        with patch('ai_utilities.openai_client._create_openai_sdk_client') as mock_openai_client:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.headers = {}
            mock_client_instance.create_chat_completion.return_value = mock_response
            mock_openai_client.return_value = mock_client_instance
            
            fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
            limits = fetcher.get_rate_limits(force_refresh=True)
            
            # Should fetch fresh data despite valid cache
            assert len(limits) >= 8  # Known defaults
            assert limits["test-model-1"].requests_per_minute != 1000  # Updated value
    
    def test_get_model_rate_limit(self):
        """Test getting rate limit for specific model."""
        # Create fetcher with temporary cache directory
        fetcher = RateLimitFetcher(api_key=self.api_key)
        
        # Setup cache
        cache_data = {
            'last_updated': datetime.now().isoformat(),
            'models': {
                'test-model-1': {
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 450000,
                    'tokens_per_day': 1350000,
                    'last_updated': datetime.now().isoformat()
                }
            }
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Existing model
        gpt4_limit = fetcher.get_model_rate_limit("test-model-1")
        assert gpt4_limit is not None
        assert gpt4_limit.requests_per_minute == 5000
        
        # Non-existing model
        unknown_limit = fetcher.get_model_rate_limit("unknown-model")
        assert unknown_limit is None
    
    def test_fetch_from_response_headers(self):
        """Test fetching rate limits from response headers."""
        # Mock response with rate limit headers
        mock_response = Mock()
        mock_response.headers = {
            'x-ratelimit-limit-requests': '3000',
            'x-ratelimit-limit-tokens': '1500000'
        }
        
        # Configure the mock client that was set up during RateLimitFetcher initialization
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        fetcher.client.create_chat_completion = Mock(return_value=mock_response)
        
        limits = fetcher._fetch_from_response_headers()
        
        assert limits is not None
        assert "gpt-3.5-turbo" in limits
        assert limits["gpt-3.5-turbo"].requests_per_minute == 3000
        assert limits["gpt-3.5-turbo"].tokens_per_minute == 1500000
    
    def test_fetch_from_response_headers_invalid_headers(self):
        """Test handling invalid response headers."""
        # Mock response with invalid headers
        mock_response = Mock()
        mock_response.headers = {
            'x-ratelimit-limit-requests': 'invalid',
            'x-ratelimit-limit-tokens': 'invalid'
        }
        
        # Configure the mock client
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        fetcher.client.create_chat_completion = Mock(return_value=mock_response)
        
        limits = fetcher._fetch_from_response_headers()
        
        # Should return None when headers are invalid (fallback happens at higher level)
        assert limits is None
    
    def test_get_known_rate_limits(self):
        """Test getting known rate limits."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        limits = fetcher._get_known_rate_limits()
        
        # Should have known models
        assert len(limits) >= 8
        assert "test-model-1" in limits
        assert "test-model-2" in limits
        assert "test-model-3" in limits
        
        # Verify reasonable values
        gpt4 = limits["test-model-1"]
        assert gpt4.requests_per_minute > 0
        assert gpt4.tokens_per_minute > 0
        assert gpt4.tokens_per_day > 0
        assert gpt4.tokens_per_day > gpt4.tokens_per_minute
    
    def test_clear_cache(self):
        """Test clearing cache."""
        # Create cache file
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        fetcher.get_rate_limits()  # Create cache
        
        assert fetcher.cache_file.exists()
        
        # Clear cache
        fetcher.clear_cache()
        assert not fetcher.cache_file.exists()
    
    def test_get_cache_status_no_cache(self):
        """Test cache status when no cache exists."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        status = fetcher.get_cache_status()
        
        assert status["cached"] is False
        assert status["cache_file"] == str(fetcher.cache_file)
        assert status["last_updated"] is None
        assert status["models_count"] == 0
    
    def test_get_cache_status_with_cache(self):
        """Test cache status when cache exists."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        fetcher.get_rate_limits()  # Create cache
        
        status = fetcher.get_cache_status()
        
        assert status["cached"] is True
        assert status["cache_file"] == str(fetcher.cache_file)
        assert status["last_updated"] is not None
        assert status["models_count"] > 0
        assert status["cache_age_days"] >= 0
    
    def test_cache_age_calculation(self):
        """Test cache age calculation."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Create cache with known timestamp
        past_time = datetime.now() - timedelta(days=5)
        cache_data = {
            'last_updated': past_time.isoformat(),
            'models': {}
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        status = fetcher.get_cache_status()
        
        # Should be approximately 5 days old
        assert 4.9 <= status["cache_age_days"] <= 5.1


class TestRateLimitFetcherErrorHandling:
    """Test RateLimitFetcher error handling."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.api_key = "test-api-key"
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_corrupted_cache_file(self):
        """Test handling of corrupted cache file."""
        # Create corrupted cache file
        with open(Path(self.temp_dir) / "openai_rate_limits.json", 'w') as f:
            f.write("invalid json content")
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Should handle corrupted cache gracefully
        limits = fetcher.get_rate_limits()
        assert len(limits) >= 8  # Should fall back to known limits
    
    @patch('ai_utilities.openai_client._create_openai_sdk_client')
    def test_api_call_failure(self, mock_openai_client):
        """Test handling of API call failures."""
        # Mock API failure
        mock_client_instance = Mock()
        mock_client_instance.create_chat_completion.side_effect = Exception("API Error")
        mock_openai_client.return_value = mock_client_instance
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Should fall back to known limits
        limits = fetcher.get_rate_limits()
        assert len(limits) >= 8
        assert "test-model-1" in limits
    
    def test_cache_directory_creation_failure(self):
        """Test handling of cache directory creation failure."""
        # Use an invalid path that can't be created
        invalid_path = "/root/nonexistent/invalid/path"
        
        # Should not raise exception, just log warning
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=invalid_path)
        
        # Should still work (just without caching)
        limits = fetcher.get_rate_limits()
        assert len(limits) >= 8
    
    def test_cache_save_failure(self):
        """Test handling of cache save failure."""
        # Create cache directory but make it read-only
        cache_dir = Path(self.temp_dir) / "readonly"
        cache_dir.mkdir()
        cache_dir.chmod(0o444)  # Read-only
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=str(cache_dir))
        
        # Should handle save failure gracefully
        limits = fetcher.get_rate_limits()
        assert len(limits) >= 8
        
        # Cleanup
        cache_dir.chmod(0o755)  # Restore permissions for cleanup
    
    def test_get_model_rate_limit(self):
        """Test getting rate limit for specific model."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Get rate limit for specific model
        limit = fetcher.get_model_rate_limit("test-model-1")
        
        assert limit is not None
        assert limit.model_name == "test-model-1"
        assert limit.requests_per_minute > 0
        assert limit.tokens_per_minute > 0
        assert limit.tokens_per_day > 0
        
        # Test non-existent model
        limit = fetcher.get_model_rate_limit("non-existent-model")
        assert limit is None
    
    def test_get_model_rate_limit_force_refresh(self):
        """Test getting rate limit with force refresh."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # First call should populate cache
        limit1 = fetcher.get_model_rate_limit("test-model-1")
        
        # Second call without force should use cache
        limit2 = fetcher.get_model_rate_limit("test-model-1")
        
        # Third call with force refresh should update
        limit3 = fetcher.get_model_rate_limit("test-model-1", force_refresh=True)
        
        assert limit1.model_name == limit2.model_name == limit3.model_name
    
    def test_clear_cache(self):
        """Test clearing cache."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Populate cache
        fetcher.get_rate_limits()
        assert fetcher.cache_file.exists()
        
        # Clear cache
        fetcher.clear_cache()
        assert not fetcher.cache_file.exists()
    
    def test_get_cache_status(self):
        """Test getting cache status."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Initial status (no cache)
        status = fetcher.get_cache_status()
        assert not status["cached"]
        assert status["models_count"] == 0
        assert status["last_updated"] is None
        
        # After populating cache
        fetcher.get_rate_limits()
        status = fetcher.get_cache_status()
        assert status["cached"]
        assert status["models_count"] > 0
        assert status["last_updated"] is not None
    
    def test_cache_expiration(self):
        """Test cache expiration logic."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir, cache_days=1)
        
        # Create expired cache
        old_date = datetime.now() - timedelta(days=2)
        cache_data = {
            "models": {
                "test-model": {
                    "model_name": "test-model",
                    "requests_per_minute": 100,
                    "tokens_per_minute": 1000,
                    "tokens_per_day": 10000,
                    "last_updated": old_date.isoformat()
                }
            },
            "last_updated": old_date.isoformat(),
            "cache_days": 1
        }
        
        with open(fetcher.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # Should detect expired cache and fetch fresh data
        with patch.object(fetcher, '_fetch_from_api') as mock_fetch:
            mock_fetch.return_value = {}
            fetcher.get_rate_limits()
            mock_fetch.assert_called_once()
    
    def test_to_model_config_value_clamping(self):
        """Test that RateLimitInfo.to_model_config clamps values properly."""
        # Create info with excessive values
        info = RateLimitInfo(
            model_name="test-model",
            requests_per_minute=50000,  # Exceeds max
            tokens_per_minute=5000000,  # Exceeds max
            tokens_per_day=500000000,   # Exceeds max
            last_updated=datetime.now()
        )
        
        config = info.to_model_config()
        
        # Values should be clamped to maximums
        assert config.requests_per_minute <= 10000
        assert config.tokens_per_minute <= 2000000
        assert config.tokens_per_day <= 50000000
    
    def test_cache_file_permissions_error(self):
        """Test handling cache file permission errors."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Create cache file and make it read-only
        fetcher.cache_file.write_text("test")
        fetcher.cache_file.chmod(0o444)
        
        try:
            # Should handle permission error gracefully
            limits = fetcher.get_rate_limits()
            assert len(limits) >= 8
        finally:
            # Restore permissions for cleanup
            fetcher.cache_file.chmod(0o644)
    
    def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        import threading
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        def worker():
            return fetcher.get_rate_limits()
        
        # Run multiple threads accessing cache
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(worker()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        for result in results:
            assert len(result) >= 8


class TestRateLimitFetcherIntegration:
    """Integration tests for RateLimitFetcher."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.api_key = "test-api-key"
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # First call - should fetch and cache
        limits1 = fetcher.get_rate_limits()
        assert len(limits1) >= 8
        
        # Verify cache was created
        assert fetcher.cache_file.exists()
        
        # Second call - should use cache
        limits2 = fetcher.get_rate_limits()
        assert len(limits2) == len(limits1)
        
        # Verify same data
        for model_name in limits1:
            assert model_name in limits2
            assert limits1[model_name].requests_per_minute == limits2[model_name].requests_per_minute
    
    def test_model_config_conversion_workflow(self):
        """Test conversion to ModelConfig workflow."""
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Get rate limits
        limits = fetcher.get_rate_limits()
        
        # Convert to ModelConfig
        model_configs = {}
        for model_name, limit_info in limits.items():
            model_configs[model_name] = limit_info.to_model_config()
        
        # Verify conversions
        for model_name, config in model_configs.items():
            assert isinstance(config, ModelConfig)
            assert config.requests_per_minute > 0
            assert config.tokens_per_minute > 0
            assert config.tokens_per_day > 0
    
    def test_cache_expiration_workflow(self):
        """Test cache expiration workflow."""
        # Create expired cache
        old_date = datetime.now() - timedelta(days=31)
        cache_data = {
            'last_updated': old_date.isoformat(),
            'models': {
                'test-model-1': {
                    'requests_per_minute': 1000,  # Old value
                    'tokens_per_minute': 100000,
                    'tokens_per_day': 1000000,
                    'last_updated': old_date.isoformat()
                }
            }
        }
        
        with open(Path(self.temp_dir) / "openai_rate_limits.json", 'w') as f:
            json.dump(cache_data, f)
        
        fetcher = RateLimitFetcher(api_key=self.api_key, cache_dir=self.temp_dir)
        
        # Should detect expired cache and refresh
        limits = fetcher.get_rate_limits()
        
        # Should have fresh data
        assert len(limits) >= 8
        if "test-model-1" in limits:
            assert limits["test-model-1"].requests_per_minute != 1000  # Updated
