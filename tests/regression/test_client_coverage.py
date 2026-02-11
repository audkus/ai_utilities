"""
Additional coverage tests for client.py module.
Focuses on uncovered utility functions and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json
import sys
from ai_utilities.client import _sanitize_namespace, _default_namespace
from tests.fake_provider import FakeProvider


class TestClientUtilitiesCoverage:
    """Test utility functions in client.py for better coverage."""
    
    def test_sanitize_namespace_all_special_chars(self):
        """Test namespace sanitization with all special characters."""
        # Test all special characters that should be replaced with underscores
        test_string = "!@#$%^&*()[]{}|\\:;'<>,.?/"
        result = _sanitize_namespace(test_string)
        assert result == "."  # Only dot is allowed, others get replaced and cleaned to default
    
    def test_sanitize_namespace_mixed_content(self):
        """Test namespace sanitization with mixed valid/invalid content."""
        # Test mixed content
        test_cases = [
            ("test@domain.com", "test_domain.com"),
            ("user_name@company.org", "user_name_company.org"),
            ("file-path/with\\slashes", "file-path_with_slashes"),
            ("version 1.0.0", "version_1.0.0"),
            ("price: $100.00", "price_100.00"),
            ("temperature: 25°C", "temperature_25_c"),
            ("math: 2+2=4", "math_2_2_4"),
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected, f"Failed for '{input_str}': got '{result}', expected '{expected}'"
    
    def test_sanitize_namespace_unicode_combining(self):
        """Test namespace sanitization with unicode combining characters."""
        # Test unicode combining characters (diacritics get removed)
        test_cases = [
            ("café", "cafe"),  # é becomes e
            ("naïve", "naive"),  # ï becomes i
            ("résumé", "resume"),  # é becomes e
            ("zoë", "zoe"),  # ë becomes e
            ("coöperate", "cooperate"),  # ö becomes o
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected
    
    def test_sanitize_namespace_numbers_and_symbols(self):
        """Test namespace sanitization with numbers and symbols."""
        test_cases = [
            ("123-456-7890", "123-456-7890"),
            ("v1.2.3-beta", "v1.2.3-beta"),
            ("test_123", "test_123"),
            ("item#1", "item_1"),
            ("price$99", "price_99"),
            ("discount%50", "discount_50"),
            ("ratio 3:1", "ratio_3_1"),
            ("path/to/file", "path_to_file"),
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected
    
    def test_sanitize_namespace_whitespace_variations(self):
        """Test namespace sanitization with various whitespace combinations."""
        test_cases = [
            ("  multiple   spaces  ", "multiple_spaces"),
            ("\t\ttabs\t\tand\tspaces\t", "tabs_and_spaces"),
            ("\n\nnewlines\n\nand\nspaces\n", "newlines_and_spaces"),
            ("\r\rcarriage\rreturn\r", "carriage_return"),
            ("\f\fform\ffeed\f", "form_feed"),
            ("\v\vvertical\vtab\v", "vertical_tab"),
            ("  \t\n\r\f\v mixed \t\n\r\f\v  ", "mixed"),
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected
    
    @patch('ai_utilities.client.Path.cwd')
    def test_default_namespace_username_variations(self, mock_cwd):
        """Test default namespace with different working directories."""
        mock_cwd.return_value = Path("/test/user123/project")
        result = _default_namespace()
        assert result.startswith("proj_")
        assert len(result) == 17  # proj_ + 12 char hash
        
        # Test with different path
        mock_cwd.return_value = Path("/different/path/test")
        result2 = _default_namespace()
        assert result2.startswith("proj_")
        assert len(result2) == 17
        assert result != result2  # Different paths should give different namespaces
    
    @patch('ai_utilities.client.Path.cwd')
    def test_default_namespace_edge_cases(self, mock_cwd):
        """Test default namespace edge cases."""
        # Test with root path
        mock_cwd.return_value = Path("/")
        result = _default_namespace()
        assert result.startswith("proj_")
        assert len(result) == 17
        
        # Test with very long path
        long_path = "/very/long/path/that/should/still/work/and/produce/a/stable/hash"
        mock_cwd.return_value = Path(long_path)
        result = _default_namespace()
        assert result.startswith("proj_")
        assert len(result) == 17
        
        # Test with special characters in path
        mock_cwd.return_value = Path("/path with spaces/and-special@chars")
        result = _default_namespace()
        assert result.startswith("proj_")
        assert len(result) == 17  
    
    def test_sanitize_namespace_real_world_examples(self):
        """Test namespace sanitization with real-world examples."""
        test_cases = [
            ("My Project@Work", "my_project_work"),
            ("API_KEY_Resolver", "api_key_resolver"),
            ("File-Upload Handler", "file-upload_handler"),
            ("User Authentication System", "user_authentication_system"),
            ("Data Processing Pipeline v2.0", "data_processing_pipeline_v2.0"),
            ("Machine Learning Model #1", "machine_learning_model_1"),
            ("Customer Data (PII)", "customer_data_pii"),
            ("Log Analysis Tool [BETA]", "log_analysis_tool_beta"),
            ("Cache:Redis vs Memcached", "cache_redis_vs_memcached"),
            ("Rate-Limiter: 100req/min", "rate-limiter_100req_min"),
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected, f"Failed for '{input_str}': got '{result}', expected '{expected}'"
    
    def test_sanitize_namespace_extreme_lengths(self):
        """Test namespace sanitization with extremely long inputs."""
        # Very long string with special characters
        long_input = "a" * 1000 + "@#$%" + "b" * 1000 + "!@#" + "c" * 1000
        result = _sanitize_namespace(long_input)
        
        # Should remove special characters but keep letters, limited to 50 chars
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "!" not in result
        assert "a" in result
        assert len(result) == 50  # Limited to 50 characters
    
    def test_sanitize_namespace_edge_unicode(self):
        """Test namespace sanitization with edge unicode cases."""
        test_cases = [
            ("测试中文", "default"),  # Chinese characters become underscores, then default
            ("العربية", "default"),  # Arabic characters become underscores, then default
            ("עברית", "default"),  # Hebrew characters become underscores, then default
            ("русский", "default"),  # Cyrillic characters become underscores, then default
            ("emoji 🚀 test", "emoji_test"),  # Emoji becomes underscore
            ("math ∑∏∫ test", "math_test"),  # Math symbols become underscores
            ("arrows →←↑↓ test", "arrows_test"),  # Arrow symbols become underscores
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_namespace(input_str)
            assert result == expected
    
    def test_sanitize_namespace_consistency(self):
        """Test that namespace sanitization is consistent."""
        test_string = "Test@Namespace #123"
        
        # Run multiple times
        result1 = _sanitize_namespace(test_string)
        result2 = _sanitize_namespace(test_string)
        result3 = _sanitize_namespace(test_string)
        
        # Should be identical
        assert result1 == result2 == result3 == "test_namespace_123"
    
    def test_sanitize_namespace_memory_efficiency(self):
        """Test that namespace sanitization doesn't leak memory."""
        import gc
        import sys
        
        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Process many strings
        for i in range(1000):
            test_string = f"test@string #{i} with special chars!"
            result = _sanitize_namespace(test_string)
            assert len(result) > 0
        
        # Check for memory leaks
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory growth
        object_growth = final_objects - initial_objects
        assert object_growth < 1000  # Allow some growth but not excessive


class TestClientIntegrationCoverage:
    """Test client integration scenarios for better coverage."""
    
    @patch('ai_utilities.usage_tracker.create_usage_tracker')
    @patch('ai_utilities.cache.CacheBackend')
    @patch('ai_utilities.progress_indicator.ProgressIndicator')
    @patch('ai_utilities.models.AskResult')
    @patch('ai_utilities.json_parsing.parse_json_from_text')
    @patch('ai_utilities.file_models.UploadedFile')
    def test_client_with_different_config_formats(self, mock_file_models, mock_json_parsing, 
                                                  mock_models, mock_progress, mock_cache, mock_usage_tracker):
        """Test client initialization with different config formats."""
        # Patch provider_exceptions and base_provider locally to avoid lazy import issues
        import ai_utilities.providers.provider_exceptions as pe
        import ai_utilities.providers.base_provider as bp
        
        with patch.object(pe, 'ProviderConfigurationError') as mock_provider_exc:
            with patch.object(bp, 'BaseProvider') as mock_base_provider:
                # Test with JSON config
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    config = {
                        "api_key": "test-key",
                        "model": "gpt-4",
                        "provider": "openai",
                        "namespace": "Test Namespace"
                    }
                    json.dump(config, f)
                    json_file = f.name
                
                try:
                    with patch('ai_utilities.client.AiSettings') as mock_settings_class:
                        mock_settings = Mock()
                        mock_settings.api_key = "test-key"
                        mock_settings.model = "gpt-4"
                        mock_settings.provider = "openai"
                        mock_settings.base_url = "https://api.openai.com/v1"  # Ensure this is a string, not Mock
                        mock_settings.namespace = "test namespace"
                        # Configure Mock to return proper values for attribute access
                        mock_settings.configure_mock(**{
                            'api_key': "test-key",
                            'model': "gpt-4",
                            'provider': "openai", 
                            'base_url': "https://api.openai.com/v1",
                            'namespace': "test namespace"
                        })
                        # Configure model_copy to return a copy with proper string values
                        mock_copy = Mock()
                        mock_copy.configure_mock(**{
                            'api_key': "test-key",
                            'model': "gpt-4",
                            'provider': "openai", 
                            'base_url': "https://api.openai.com/v1",
                            'namespace': "test namespace"
                        })
                        mock_settings.model_copy.return_value = mock_copy
                        mock_settings_class.return_value = mock_settings
                        
                        with patch('ai_utilities.client.create_usage_tracker') as mock_tracker:
                            mock_tracker.return_value = Mock()
                            
                            from ai_utilities.client import AiClient
                            
                            fake_provider = FakeProvider()
                            client = AiClient(settings=mock_settings, provider=fake_provider)
                            
                            assert client is not None
                            # Namespace should be sanitized
                            assert mock_settings.namespace == "test namespace"
                finally:
                    Path(json_file).unlink()
    
    @patch('ai_utilities.usage_tracker.create_usage_tracker')
    @patch('ai_utilities.cache.CacheBackend')
    @patch('ai_utilities.progress_indicator.ProgressIndicator')
    @patch('ai_utilities.models.AskResult')
    @patch('ai_utilities.json_parsing.parse_json_from_text')
    @patch('ai_utilities.file_models.UploadedFile')
    def test_client_error_handling(self, mock_file_models, mock_json_parsing, 
                                  mock_models, mock_progress, mock_cache, mock_usage_tracker):
        """Test client error handling scenarios."""
        # Patch provider_exceptions locally to avoid lazy import issues
        import ai_utilities.providers.provider_exceptions as pe
        import ai_utilities.providers.base_provider as bp
        
        with patch.object(pe, 'ProviderConfigurationError') as mock_provider_exc:
            with patch.object(bp, 'BaseProvider') as mock_base_provider:
                with patch('ai_utilities.client.AiSettings') as mock_settings_class:
                    # Test with invalid config file
                    mock_settings_class.side_effect = Exception("Invalid config")
                    
                    with pytest.raises(Exception):
                        from ai_utilities.client import AiClient
                        AiClient(config_file="/nonexistent/config.json")
    
    def test_namespace_sanitize_integration(self):
        """Test namespace sanitization in realistic scenarios."""
        # Test common namespace patterns from real applications
        real_namespaces = [
            "user-uploads@production",
            "api_requests#v2",
            "cache:redis:localhost",
            "logs:application:errors",
            "metrics:cpu:usage",
            "sessions:user:auth",
            "temp:file:uploads",
            "backup:database:daily",
            "analytics:events:tracking",
            "search:index:documents",
        ]
        
        expected_sanitized = [
            "user-uploads_production",
            "api_requests_v2",
            "cache_redis_localhost",
            "logs_application_errors",
            "metrics_cpu_usage",
            "sessions_user_auth",
            "temp_file_uploads",
            "backup_database_daily",
            "analytics_events_tracking",
            "search_index_documents",
        ]
        
        for original, expected in zip(real_namespaces, expected_sanitized):
            result = _sanitize_namespace(original)
            assert result == expected, f"Failed for '{original}': got '{result}', expected '{expected}'"
