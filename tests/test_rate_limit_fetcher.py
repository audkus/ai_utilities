"""Tests for rate_limit_fetcher.py module."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile

from ai_utilities.rate_limit_fetcher import (
    RateLimitInfo,
    RateLimitFetcher
)
from ai_utilities.config_models import ModelConfig


class TestRateLimitInfo:
    """Test RateLimitInfo dataclass."""
    
    def test_rate_limit_info_creation(self):
        """Test RateLimitInfo creation."""
        now = datetime.now()
        info = RateLimitInfo(
            model_name="gpt-4",
            requests_per_minute=5000,
            tokens_per_minute=160000,
            tokens_per_day=1000000,
            last_updated=now
        )
        
        assert info.model_name == "gpt-4"
        assert info.requests_per_minute == 5000
        assert info.tokens_per_minute == 160000
        assert info.tokens_per_day == 1000000
        assert info.last_updated == now
    
    def test_to_model_config_normal_values(self):
        """Test conversion to ModelConfig with normal values."""
        info = RateLimitInfo(
            model_name="gpt-4",
            requests_per_minute=5000,
            tokens_per_minute=160000,
            tokens_per_day=1000000,
            last_updated=datetime.now()
        )
        
        config = info.to_model_config()
        
        assert isinstance(config, ModelConfig)
        assert config.requests_per_minute == 5000
        assert config.tokens_per_minute == 160000
        assert config.tokens_per_day == 1000000
    
    def test_to_model_config_clamped_values(self):
        """Test conversion to ModelConfig with values that need clamping."""
        info = RateLimitInfo(
            model_name="gpt-4",
            requests_per_minute=50000,  # Above max of 10000
            tokens_per_minute=5000000,  # Above max of 2000000
            tokens_per_day=100000000,   # Above max of 50000000
            last_updated=datetime.now()
        )
        
        config = info.to_model_config()
        
        assert config.requests_per_minute == 10000  # Clamped
        assert config.tokens_per_minute == 2000000  # Clamped
        assert config.tokens_per_day == 50000000    # Clamped
    
    def test_to_model_config_minimum_values(self):
        """Test conversion with minimum valid values."""
        info = RateLimitInfo(
            model_name="gpt-4",
            requests_per_minute=1,    # Minimum allowed value (ge=1)
            tokens_per_minute=1000,  # Minimum allowed value (ge=1000)
            tokens_per_day=10000,     # Minimum allowed value (ge=10000)
            last_updated=datetime.now()
        )
        
        config = info.to_model_config()
        
        assert config.requests_per_minute == 1
        assert config.tokens_per_minute == 1000
        assert config.tokens_per_day == 10000


class TestRateLimitFetcher:
    """Test RateLimitFetcher class."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test-api-key-12345"
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def rate_limit_fetcher(self, mock_api_key, temp_cache_dir):
        """Create RateLimitFetcher instance for testing."""
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client:
            mock_client.return_value = MagicMock()
            return RateLimitFetcher(api_key=mock_api_key, cache_dir=temp_cache_dir)
    
    def test_initialization(self, mock_api_key, temp_cache_dir):
        """Test RateLimitFetcher initialization."""
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client:
            mock_client.return_value = MagicMock()
            
            fetcher = RateLimitFetcher(api_key=mock_api_key, cache_dir=temp_cache_dir)
            
            assert fetcher.api_key == mock_api_key
            assert fetcher.cache_dir == Path(temp_cache_dir)
            assert fetcher.cache_file == Path(temp_cache_dir) / "openai_rate_limits.json"
            assert fetcher.cache_days == 30
            assert fetcher.client is not None
    
    def test_initialization_default_cache_dir(self, mock_api_key):
        """Test initialization with default cache directory."""
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client:
            mock_client.return_value = MagicMock()
            
            fetcher = RateLimitFetcher(api_key=mock_api_key)
            
            expected_dir = Path.home() / ".ai_utilities" / "rate_limits"
            assert fetcher.cache_dir == expected_dir
            assert fetcher.cache_file == expected_dir / "openai_rate_limits.json"
    
    def test_initialization_cache_dir_creation_failure(self, mock_api_key):
        """Test fallback to temp directory when cache creation fails."""
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client:
            mock_client.return_value = MagicMock()
            
            with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
                with patch('tempfile.mkdtemp', return_value="/tmp/fallback_dir") as mock_tempdir:
                    fetcher = RateLimitFetcher(api_key=mock_api_key)
                    
                    assert fetcher.cache_dir == Path("/tmp/fallback_dir")
                    mock_tempdir.assert_called_once_with(prefix="ai_utilities_rate_limits_")
    
    def test_load_from_cache_no_file(self, rate_limit_fetcher):
        """Test loading cache when no cache file exists."""
        result = rate_limit_fetcher._load_from_cache()
        assert result is None
    
    def test_load_from_cache_file_access_error(self, rate_limit_fetcher):
        """Test loading cache when file cannot be accessed."""
        with patch.object(Path, 'exists', side_effect=OSError("Permission denied")):
            result = rate_limit_fetcher._load_from_cache()
            assert result is None
    
    def test_load_from_cache_expired(self, rate_limit_fetcher):
        """Test loading expired cache."""
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        cache_data = {
            'last_updated': old_date,
            'models': {
                'gpt-4': {
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 160000,
                    'tokens_per_day': 1000000,
                    'last_updated': old_date
                }
            }
        }
        
        mock_file_data = json.dumps(cache_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_data)):
            with patch.object(Path, 'exists', return_value=True):
                result = rate_limit_fetcher._load_from_cache()
                assert result is None
    
    def test_load_from_cache_valid(self, rate_limit_fetcher):
        """Test loading valid cache."""
        recent_date = (datetime.now() - timedelta(days=1)).isoformat()
        cache_data = {
            'last_updated': recent_date,
            'models': {
                'gpt-4': {
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 160000,
                    'tokens_per_day': 1000000,
                    'last_updated': recent_date
                },
                'gpt-3.5-turbo': {
                    'requests_per_minute': 3500,
                    'tokens_per_minute': 90000,
                    'tokens_per_day': 1000000,
                    'last_updated': recent_date
                }
            }
        }
        
        mock_file_data = json.dumps(cache_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_data)):
            with patch.object(Path, 'exists', return_value=True):
                result = rate_limit_fetcher._load_from_cache()
                
                assert result is not None
                assert len(result) == 2
                assert 'gpt-4' in result
                assert 'gpt-3.5-turbo' in result
                
                gpt4_info = result['gpt-4']
                assert gpt4_info.model_name == "gpt-4"
                assert gpt4_info.requests_per_minute == 5000
                assert gpt4_info.tokens_per_minute == 160000
                assert gpt4_info.tokens_per_day == 1000000
    
    def test_load_from_cache_json_error(self, rate_limit_fetcher):
        """Test loading cache with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch.object(Path, 'exists', return_value=True):
                result = rate_limit_fetcher._load_from_cache()
                assert result is None
    
    def test_save_to_cache(self, rate_limit_fetcher):
        """Test saving rate limits to cache."""
        now = datetime.now()
        rate_limits = {
            'gpt-4': RateLimitInfo(
                model_name="gpt-4",
                requests_per_minute=5000,
                tokens_per_minute=160000,
                tokens_per_day=1000000,
                last_updated=now
            )
        }
        
        expected_cache_data = {
            'last_updated': now.isoformat(),
            'models': {
                'gpt-4': {
                    'model_name': 'gpt-4',
                    'requests_per_minute': 5000,
                    'tokens_per_minute': 160000,
                    'tokens_per_day': 1000000,
                    'last_updated': now.isoformat()
                }
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_dump:
                rate_limit_fetcher._save_to_cache(rate_limits)
                
                # Verify json.dump was called
                mock_dump.assert_called_once()
                
                # Get the data that was saved
                call_args = mock_dump.call_args[0]
                saved_data = call_args[0]
                
                # Check timestamp is close (within 1 second) to handle microsecond differences
                saved_timestamp = datetime.fromisoformat(saved_data['last_updated'])
                expected_timestamp = datetime.fromisoformat(expected_cache_data['last_updated'])
                time_diff = abs((saved_timestamp - expected_timestamp).total_seconds())
                assert time_diff < 1.0, f"Timestamps differ by {time_diff} seconds"
                
                assert 'gpt-4' in saved_data['models']
    
    def test_save_to_cache_file_error(self, rate_limit_fetcher):
        """Test saving cache when file write fails."""
        rate_limits = {}
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            # Should not raise exception
            rate_limit_fetcher._save_to_cache(rate_limits)
    
    def test_get_rate_limits_from_cache(self, rate_limit_fetcher):
        """Test getting rate limits from cache."""
        with patch.object(rate_limit_fetcher, '_load_from_cache') as mock_load:
            mock_limits = {'gpt-4': MagicMock()}
            mock_load.return_value = mock_limits
            
            result = rate_limit_fetcher.get_rate_limits()
            
            assert result == mock_limits
            mock_load.assert_called_once()
    
    def test_get_rate_limits_force_refresh(self, rate_limit_fetcher):
        """Test getting rate limits with force refresh."""
        with patch.object(rate_limit_fetcher, '_load_from_cache') as mock_load:
            with patch.object(rate_limit_fetcher, '_fetch_from_api') as mock_fetch:
                with patch.object(rate_limit_fetcher, '_save_to_cache') as mock_save:
                    
                    mock_api_limits = {'gpt-4': MagicMock()}
                    mock_fetch.return_value = mock_api_limits
                    
                    result = rate_limit_fetcher.get_rate_limits(force_refresh=True)
                    
                    assert result == mock_api_limits
                    mock_load.assert_not_called()
                    mock_fetch.assert_called_once()
                    mock_save.assert_called_once_with(mock_api_limits)
    
    def test_get_rate_limits_cache_miss(self, rate_limit_fetcher):
        """Test getting rate limits when cache is empty."""
        with patch.object(rate_limit_fetcher, '_load_from_cache') as mock_load:
            with patch.object(rate_limit_fetcher, '_fetch_from_api') as mock_fetch:
                with patch.object(rate_limit_fetcher, '_save_to_cache') as mock_save:
                    
                    mock_load.return_value = None  # Cache miss
                    mock_api_limits = {'gpt-4': MagicMock()}
                    mock_fetch.return_value = mock_api_limits
                    
                    result = rate_limit_fetcher.get_rate_limits()
                    
                    assert result == mock_api_limits
                    mock_load.assert_called_once()
                    mock_fetch.assert_called_once()
                    mock_save.assert_called_once_with(mock_api_limits)
    
    def test_get_model_rate_limit_found(self, rate_limit_fetcher):
        """Test getting rate limit for specific model."""
        with patch.object(rate_limit_fetcher, 'get_rate_limits') as mock_get_all:
            gpt4_info = RateLimitInfo(
                model_name="gpt-4",
                requests_per_minute=5000,
                tokens_per_minute=160000,
                tokens_per_day=1000000,
                last_updated=datetime.now()
            )
            mock_get_all.return_value = {'gpt-4': gpt4_info}
            
            result = rate_limit_fetcher.get_model_rate_limit("gpt-4")
            
            assert result == gpt4_info
            mock_get_all.assert_called_once_with(force_refresh=False)
    
    def test_get_model_rate_limit_not_found(self, rate_limit_fetcher):
        """Test getting rate limit for non-existent model."""
        with patch.object(rate_limit_fetcher, 'get_rate_limits') as mock_get_all:
            mock_get_all.return_value = {'gpt-4': MagicMock()}
            
            result = rate_limit_fetcher.get_model_rate_limit("gpt-3.5-turbo")
            
            assert result is None
    
    def test_get_model_rate_limit_force_refresh(self, rate_limit_fetcher):
        """Test getting model rate limit with force refresh."""
        with patch.object(rate_limit_fetcher, 'get_rate_limits') as mock_get_all:
            gpt4_info = MagicMock()
            mock_get_all.return_value = {'gpt-4': gpt4_info}
            
            result = rate_limit_fetcher.get_model_rate_limit("gpt-4", force_refresh=True)
            
            assert result == gpt4_info
            mock_get_all.assert_called_once_with(force_refresh=True)


class TestRateLimitFetcherIntegration:
    """Integration tests for RateLimitFetcher."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test-api-key-12345"
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_full_workflow(self, mock_api_key, temp_cache_dir):
        """Test full workflow of fetching and caching rate limits."""
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            fetcher = RateLimitFetcher(api_key=mock_api_key, cache_dir=temp_cache_dir)
            
            # Mock API response
            mock_api_response = {
                'gpt-4': RateLimitInfo(
                    model_name="gpt-4",
                    requests_per_minute=5000,
                    tokens_per_minute=160000,
                    tokens_per_day=1000000,
                    last_updated=datetime.now()
                )
            }
            
            with patch.object(fetcher, '_fetch_from_api', return_value=mock_api_response):
                # First call should fetch from API
                result1 = fetcher.get_rate_limits()
                assert result1 == mock_api_response
                
                # Second call should use cache
                result2 = fetcher.get_rate_limits()
                assert result2 == mock_api_response
                
                # Force refresh should fetch from API again
                result3 = fetcher.get_rate_limits(force_refresh=True)
                assert result3 == mock_api_response
    
    def test_cache_persistence(self, mock_api_key, temp_cache_dir):
        """Test that cache persists across fetcher instances."""
        # Create first fetcher and populate cache
        with patch('ai_utilities.openai_client.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            fetcher1 = RateLimitFetcher(api_key=mock_api_key, cache_dir=temp_cache_dir)
            
            mock_api_response = {
                'gpt-4': RateLimitInfo(
                    model_name="gpt-4",
                    requests_per_minute=5000,
                    tokens_per_minute=160000,
                    tokens_per_day=1000000,
                    last_updated=datetime.now()
                )
            }
            
            with patch.object(fetcher1, '_fetch_from_api', return_value=mock_api_response):
                fetcher1.get_rate_limits()
            
            # Create second fetcher and verify it uses cache
            fetcher2 = RateLimitFetcher(api_key=mock_api_key, cache_dir=temp_cache_dir)
            
            with patch.object(fetcher2, '_fetch_from_api') as mock_fetch:
                result = fetcher2.get_rate_limits()
                
                # Should not call fetch_from_api since cache is valid
                mock_fetch.assert_not_called()
                assert 'gpt-4' in result
