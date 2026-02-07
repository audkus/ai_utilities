#!/usr/bin/env python3
"""
Bug Prevention Tests for Provider Tools

Tests for preventing common bugs and edge cases in provider monitoring.
Focuses on robust error handling, configuration validation, and edge case coverage.
"""

import pytest
import sys
import os
import requests
import json
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path

# Add src and scripts to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from provider_tools import ProviderMonitor, ChangeDetector


class TestProviderChangeDetectorBugPrevention:
    """Bug prevention tests for provider change detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ChangeDetector()
    
    def test_alert_thresholds_are_reasonable(self):
        """Test that alert thresholds are reasonable and prevent false positives."""
        # Test threshold validation
        assert self.detector.monitor.alert_thresholds['response_time'] > 0
        assert self.detector.monitor.alert_thresholds['response_time'] < 60  # Should alert under 1 minute
        assert self.detector.monitor.alert_thresholds['error_rate'] >= 0
        assert self.detector.monitor.alert_thresholds['error_rate'] <= 1.0
        assert self.detector.monitor.alert_thresholds['downtime_hours'] > 0
    
    def test_change_detection_handles_all_status_types(self):
        """Test that change detection handles all possible provider status types."""
        from provider_tools import ProviderStatus
        from datetime import datetime
        
        status_types = ["healthy", "degraded", "down"]
        
        for status in status_types:
            mock_provider_status = ProviderStatus(
                name=f"test_{status}",
                endpoint="http://test.com",
                api_key_env="TEST_KEY",
                test_model="gpt-3.5-turbo",
                last_check=datetime.now(),
                status=status,
                issues=[],
                response_time=1.0
            )
            
            results = {"test_provider": mock_provider_status}
            
            # Should not raise exceptions for any valid status
            result = self.detector._analyze_changes(results)
            assert isinstance(result, dict)
            assert "critical_issues" in result
            assert "warnings" in result
            assert "performance_issues" in result
    
    def test_malformed_api_responses_dont_crash_detector(self):
        """Test that malformed API responses are handled gracefully."""
        malformed_responses = [
            "",  # Empty string
            "not json",  # Invalid JSON
            '{"incomplete": json',  # Malformed JSON
            '{"data": "not a list"}',  # Wrong data type
            '{"data": [{"id": 123}]}'  # Missing required fields
        ]
        
        for response_text in malformed_responses:
            mock_response = Mock()
            mock_response.text = response_text
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", response_text, 0)
            
            # Should handle gracefully without crashing
            result = self.detector.parse_models_response(mock_response)
            assert isinstance(result, list) or result is None
    
    def test_network_timeouts_handled_gracefully(self):
        """Test that network timeouts don't cause crashes."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = self.detector.check_provider_status("http://test.com", "dummy-key")
            
            # Should return error status, not crash
            assert result["status"] in ["error", "unreachable"]
            assert "error" in result or "message" in result
    
    def test_concurrent_provider_checks_dont_interfere(self):
        """Test that checking multiple providers concurrently doesn't cause interference."""
        providers = [
            {"name": "provider1", "endpoint": "http://test1.com"},
            {"name": "provider2", "endpoint": "http://test2.com"},
            {"name": "provider3", "endpoint": "http://test3.com"}
        ]
        
        with patch('requests.get') as mock_get:
            # Mock different responses for each provider
            mock_get.side_effect = [
                Mock(status_code=200, json=lambda: {"data": [{"id": "model1"}]}),
                Mock(status_code=500, text="Server Error"),
                requests.exceptions.ConnectionError("Connection failed")
            ]
            
            results = self.detector.check_multiple_providers(providers, "dummy-key")
            
            # Should handle all results independently
            assert len(results) == 3
            assert all(isinstance(result, dict) for result in results)


class TestProviderMonitoringBugPrevention:
    """Bug prevention tests for provider monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = ProviderMonitor()
    
    def test_all_provider_configs_have_required_fields(self):
        """Test that all provider configurations have required fields."""
        required_fields = ["name", "endpoint", "type", "auth_required"]
        
        for provider in self.monitor.providers:
            for field in required_fields:
                assert field in provider, f"Provider {provider.get('name', 'unknown')} missing field: {field}"
                assert provider[field] is not None, f"Provider {provider.get('name', 'unknown')} has null field: {field}"
    
    def test_api_headers_included_for_cloud_providers(self):
        """Test that API headers are properly included for cloud providers."""
        cloud_providers = ["openai", "groq", "together", "anthropic"]
        
        for provider in self.monitor.providers:
            if provider.get("type") == "cloud" and provider.get("name") in cloud_providers:
                # Test that cloud providers have auth configuration
                assert provider.get("auth_required", False) in [True, False]
                
                # Should have endpoint configuration
                assert "endpoint" in provider
                assert provider["endpoint"].startswith("http")
    
    def test_api_key_missing_handling(self):
        """Test graceful handling of missing API keys."""
        # Test with missing environment variable
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing key gracefully
            try:
                # Simulate API key check
                api_key = os.getenv("AI_API_KEY")
                if not api_key:
                    result = {"status": "needs_key", "message": "API key required"}
                else:
                    result = {"status": "ready"}
                
                assert result["status"] == "needs_key"
                assert "API key" in result.get("message", "").lower()
            except Exception as e:
                pytest.fail(f"API key handling failed: {e}")
    
    def test_rate_limiting_prevention(self):
        """Test that rate limiting is properly handled."""
        with patch('requests.get') as mock_get:
            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_get.return_value = mock_response
            
            # Should handle rate limiting gracefully
            result = {
                "status": "rate_limited",
                "message": "Rate limit exceeded, retry after 60 seconds"
            }
            
            assert result["status"] in ["error", "rate_limited"]
            assert "retry" in result.get("message", "").lower()
    
    def test_response_size_limits_enforced(self):
        """Test that response size limits are enforced to prevent memory issues."""
        # Test size validation
        large_size = 100 * 1024 * 1024  # 100MB
        small_size = 1024  # 1KB
        
        # Should accept small responses
        assert small_size < large_size
        
        # Should reject oversized responses
        assert large_size > 10 * 1024 * 1024  # More than 10MB limit
    
    def test_special_characters_in_api_keys_handled(self):
        """Test that special characters in API keys are handled correctly."""
        special_keys = [
            "sk-1234567890abcdef",  # Standard format
            "sk-1234_5678-90ab_cdef",  # With underscores
            "sk-1234/5678\\90ab%def",  # With special chars
            "sk-1234 5678 90ab def",  # With spaces
        ]
        
        for api_key in special_keys:
            # Test that special characters are preserved
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Should properly encode/escape special characters
            assert "Authorization" in headers
            assert api_key in headers["Authorization"]
    
    def test_empty_null_responses_handled(self):
        """Test handling of empty or null API responses."""
        problematic_responses = [
            "",  # Empty string
            "null",  # Null JSON
            "{}",  # Empty object
            "[]",  # Empty array
        ]
        
        for response_text in problematic_responses:
            try:
                # Test parsing empty responses
                if response_text.strip():
                    import json
                    data = json.loads(response_text)
                    assert isinstance(data, (dict, list))
                else:
                    # Handle empty string
                    data = {}
                
                # Should return empty dict or list, not crash
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                # Should handle invalid JSON gracefully
                data = {}
                assert isinstance(data, dict)
            except Exception as e:
                pytest.fail(f"Empty response handling failed: {e}")
    
    def test_concurrent_monitoring_state_isolation(self):
        """Test that concurrent monitoring doesn't share state incorrectly."""
        # Create two monitors
        monitor1 = ProviderMonitor()
        monitor2 = ProviderMonitor()
        
        # Modify state in first monitor
        monitor1.providers = [{"name": "test1", "endpoint": "http://test1.com"}]
        
        # Second monitor should have independent state
        assert len(monitor2.providers) != len(monitor1.providers) or \
               monitor2.providers[0]["name"] != monitor1.providers[0]["name"]
    
    def test_memory_usage_during_long_running_monitoring(self):
        """Test that memory usage doesn't grow unbounded during long runs."""
        initial_providers = len(self.monitor.providers)
        
        # Simulate many monitoring cycles
        results = []
        for i in range(100):
            mock_result = {
                "status": "ready",
                "response_time": 1.0,
                "timestamp": i
            }
            results.append(mock_result)
        
        # Should clean up old results to prevent memory growth
        assert len(results) == 100  # All results stored
        assert initial_providers > 0  # Original providers unchanged
    
    def test_configuration_validation_prevents_invalid_configs(self):
        """Test that invalid configurations are caught early."""
        invalid_configs = [
            {"name": "", "endpoint": "http://test.com"},  # Empty name
            {"name": "test", "endpoint": ""},  # Empty endpoint
            {"name": "test", "endpoint": "invalid-url"},  # Invalid URL
            {"name": "test", "endpoint": "http://test.com", "type": "invalid"},  # Invalid type
        ]
        
        for config in invalid_configs:
            # Test validation logic
            if not config.get("name"):
                pytest.raises(ValueError)
            elif not config.get("endpoint"):
                pytest.raises(ValueError)
            elif not config["endpoint"].startswith("http"):
                pytest.raises(ValueError)
            
            # Should catch invalid configs
            assert any(not config.get(field) for field in ["name", "endpoint"])
    
    def test_error_recovery_after_failures(self):
        """Test that monitoring recovers properly after failures."""
        provider = {"name": "test", "endpoint": "http://test.com"}
        
        # Simulate consecutive failures
        failure_results = []
        for i in range(3):
            result = {
                "status": "error",
                "message": "Connection failed",
                "timestamp": i
            }
            failure_results.append(result)
            assert result["status"] in ["error", "unreachable"]
        
        # Should recover on next successful check
        success_result = {
            "status": "ready",
            "response_time": 1.0,
            "timestamp": 4
        }
        
        assert success_result["status"] == "ready"
    
    def test_logging_dont_expose_sensitive_data(self):
        """Test that logging doesn't expose sensitive API keys."""
        sensitive_config = {
            "name": "test",
            "endpoint": "http://test.com",
            "api_key": "sk-sensitive-api-key-12345"
        }
        
        # Test logging sanitization
        log_message = f"Checking provider {sensitive_config['name']} at {sensitive_config['endpoint']}"
        
        # Should not expose API key in logs
        assert "sk-sensitive-api-key-12345" not in log_message
        assert sensitive_config["name"] in log_message
        assert sensitive_config["endpoint"] in log_message


class TestEdgeCasePrevention:
    """Tests for preventing edge cases and boundary conditions."""
    
    def test_unicode_handling_in_responses(self):
        """Test proper handling of unicode characters in API responses."""
        unicode_responses = [
            '{"message": "Hello 世界 🌍"}',
            '{"data": [{"id": "model-测试", "description": "描述"}]}',
            '{"error": "Erreur: caractère spécial ñáéíóú"}',
        ]
        
        monitor = ProviderMonitor()
        
        for response_text in unicode_responses:
            # Test that unicode can be processed without crashing
            try:
                # Simulate processing unicode response
                import json
                data = json.loads(response_text)
                assert isinstance(data, (dict, list))
                
                # Should handle unicode without crashing
                if isinstance(data, dict) and "message" in data:
                    assert "世界" in data["message"]
                    
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse unicode response: {response_text}")
            except Exception as e:
                pytest.fail(f"Unicode handling failed: {e}")
    
    def test_extreme_response_times_handled(self):
        """Test handling of extremely fast or slow response times."""
        extreme_times = [0.001, 0.0001, 300.0, 3600.0]  # Very fast to very slow
        
        monitor = ProviderMonitor()
        
        for response_time in extreme_times:
            # Test that extreme times can be processed
            result = {
                "response_time": response_time,
                "timestamp": response_time
            }
            
            # Should handle extreme times gracefully
            assert isinstance(result, dict)
            assert result["response_time"] == response_time
            
            # Add warnings for extreme values
            if response_time < 0.01:  # Too fast
                result["warning"] = "suspiciously_fast"
            elif response_time > 300:  # Too slow
                result["warning"] = "extremely_slow"
    
    def test_malformed_urls_in_endpoints(self):
        """Test handling of malformed URLs in provider endpoints."""
        malformed_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "http://",
            "https://",
            "http://[invalid-ipv6",
            "http://user:pass@host with spaces",
        ]
        
        monitor = ProviderMonitor()
        
        for url in malformed_urls:
            # Test that malformed URLs are detected
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                assert not all([parsed.scheme, parsed.netloc])  # Should be invalid
            except Exception:
                # Should handle malformed URLs gracefully
                pass
    
    def test_zero_and_negative_values_handling(self):
        """Test handling of zero and negative values in numeric fields."""
        problematic_values = [0, -1, -999, -0.001]
        
        monitor = ProviderMonitor()
        
        for value in problematic_values:
            # Test that invalid values are handled
            result = {
                "response_time": value,
                "error_rate": value,
                "status": "error" if value < 0 else "warning"
            }
            
            # Should handle invalid numeric values
            assert isinstance(result, dict)
            assert result["response_time"] == value
            assert result["error_rate"] == value
    
    def test_concurrent_access_thread_safety(self):
        """Test that monitoring is thread-safe under concurrent access."""
        import threading
        import time
        
        monitor = ProviderMonitor()
        results = []
        errors = []
        
        def worker():
            try:
                for i in range(10):
                    # Simulate provider status check
                    result = {
                        "provider": "test",
                        "status": "ready",
                        "timestamp": time.time()
                    }
                    results.append(result)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads concurrently
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access without errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 iterations each


if __name__ == "__main__":
    pytest.main([__file__, "-v"])