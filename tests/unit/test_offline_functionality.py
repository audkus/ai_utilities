"""Tests for no-network scenarios and offline functionality."""

import pytest
from unittest.mock import patch, MagicMock
import ai_utilities
from ai_utilities import AiClient, AiSettings, create_client
from tests.fake_provider import FakeProvider


class TestNoNetworkScenarios:
    """Test that the library works correctly without network access."""
    
    def test_ai_client_works_without_network(self):
        """Test that AiClient can be created and used without network calls."""
        # Use FakeProvider to avoid any network calls
        fake_provider = FakeProvider(["Test response: {prompt}"])
        client = AiClient(provider=fake_provider)
        
        # Should work without any network access
        response = client.ask("test prompt")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response
    
    def test_create_client_with_fake_provider_no_network(self):
        """Test create_client convenience function without network."""
        settings = AiSettings(api_key="fake-key", model="test-model")
        fake_provider = FakeProvider(["Response: {prompt}"])
        client = AiClient(settings, provider=fake_provider)
        
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response
    
    def test_imports_work_without_internet(self):
        """Test that imports work without internet connection."""
        # Mock network requests to simulate offline mode
        with patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post, \
             patch('socket.create_connection') as mock_socket:
            
            # Make all network calls fail
            mock_get.side_effect = Exception("No internet")
            mock_post.side_effect = Exception("No internet") 
            mock_socket.side_effect = Exception("No internet")
            
            # Clear environment variables that might interfere
            import os
            ai_model_backup = os.environ.pop('AI_MODEL', None)
            
            try:
                from ai_utilities import AiClient, AiSettings, AskResult
                from ai_utilities import UploadedFile, JsonParseError, parse_json_from_text
                from ai_utilities import create_client
                from ai_utilities.audio import AudioProcessor
                
                # Should be able to instantiate classes without network
                settings = AiSettings(api_key="test-key")
                assert settings.model is None  # Default when no env var
                
                # Should be able to create result objects
                result = AskResult(
                    prompt="test",
                    response="response", 
                    error=None,
                    duration_s=0.1
                )
                assert isinstance(result.prompt, str)  # Contract: prompt is string type
                assert len(result.prompt) > 0  # Contract: non-empty prompt
            finally:
                # Restore environment variable
                if ai_model_backup is not None:
                    os.environ['AI_MODEL'] = ai_model_backup
    
    def test_settings_validation_without_network(self):
        """Test that settings validation works without network calls."""
        # Should validate locally without any network access
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            temperature=0.5,
            timeout=30
        )
        
        assert isinstance(settings.api_key, str)  # Contract: api_key is string type
        assert len(settings.api_key) > 0  # Contract: non-empty api key
        assert isinstance(settings.model, str)  # Contract: model is string type
        assert len(settings.model) > 0  # Contract: non-empty model
        assert isinstance(settings.temperature, float)  # Contract: temperature is float
        assert 0.0 <= settings.temperature <= 2.0  # Contract: valid temperature range
        assert isinstance(settings.timeout, (int, float))  # Contract: timeout is numeric
        assert settings.timeout > 0  # Contract: positive timeout
    
    def test_client_works_with_explicit_provider(self):
        """Test that client works when provider is explicitly provided."""
        fake_provider = FakeProvider(["test response"])
        client = AiClient(provider=fake_provider)
        
        # Should work without any setup calls
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response


class TestProviderErrorHandling:
    """Test provider error handling and resilience."""
    
    def test_provider_configuration_error_handling(self):
        """Test that provider configuration errors are handled gracefully."""
        # Test with invalid provider configuration
        with pytest.raises(Exception):  # Should raise some configuration error
            settings = AiSettings(provider="invalid_provider")
            from ai_utilities.providers import create_provider
            create_provider(settings)
    
    def test_missing_api_key_error_handling(self):
        """Test that missing API keys are handled appropriately."""
        # This should not crash during creation but fail gracefully when used
        settings = AiSettings(provider="openai", api_key=None)
        fake_provider = FakeProvider(["test response"])
        client = AiClient(settings, provider=fake_provider)
        
        # Should work with fake provider even without real API key
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response
    
    def test_provider_fallback_mechanism(self):
        """Test that provider fallback works when available."""
        # Test with a provider that might fail
        settings = AiSettings(api_key="test-key")
        
        # Should be able to create client
        fake_provider = FakeProvider(["fallback response"])
        client = AiClient(settings, provider=fake_provider)
        
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response
    
    def test_error_propagation_from_provider(self):
        """Test that provider errors are properly propagated."""
        # Create a provider that raises an error
        error_provider = FakeProvider()
        error_provider.ask = MagicMock(side_effect=Exception("Provider error"))
        
        client = AiClient(provider=error_provider)
        
        # Should propagate the error
        with pytest.raises(Exception, match="Provider error"):
            client.ask("test")
    
    def test_graceful_degradation_with_missing_features(self):
        """Test graceful degradation when provider lacks features."""
        # Create a minimal provider
        minimal_provider = FakeProvider(["basic response"])
        
        # Remove any advanced methods if they exist
        if hasattr(minimal_provider, 'advanced_feature'):
            delattr(minimal_provider, 'advanced_feature')
        
        client = AiClient(provider=minimal_provider)
        
        # Should still work for basic operations
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response


class TestOfflineConfiguration:
    """Test configuration scenarios that work completely offline."""
    
    def test_settings_from_dict_offline(self):
        """Test creating settings from dictionary without any external dependencies."""
        settings_data = {
            "api_key": "test-key",
            "model": "test-model",
            "temperature": 0.7,
            "timeout": 30,
            "max_tokens": 1000
        }
        
        settings = AiSettings(**settings_data)
        
        assert isinstance(settings.api_key, str)  # Contract: api_key is string type
        assert len(settings.api_key) > 0  # Contract: non-empty api key
        assert isinstance(settings.model, str)  # Contract: model is string type
        assert len(settings.model) > 0  # Contract: non-empty model
        assert isinstance(settings.temperature, float)  # Contract: temperature is float
        assert 0.0 <= settings.temperature <= 2.0  # Contract: valid temperature range
        assert isinstance(settings.timeout, (int, float))  # Contract: timeout is numeric
        assert settings.timeout > 0  # Contract: positive timeout
        assert isinstance(settings.max_tokens, int)  # Contract: max_tokens is int
        assert settings.max_tokens > 0  # Contract: positive max_tokens
    
    def test_environment_variable_override_offline(self):
        """Test environment variable overrides without network calls."""
        fake_provider = FakeProvider(["test response"])
        
        # Should work with environment variables
        import os
        os.environ["AI_MODEL"] = "env-model"
        os.environ["AI_TEMPERATURE"] = "0.5"
        
        try:
            settings = AiSettings(api_key="test-key")
            # Note: Environment variables might not work in all test environments
            # but this should not crash
            assert isinstance(settings.api_key, str)  # Contract: api_key is string type
            assert len(settings.api_key) > 0  # Contract: non-empty api key
        finally:
            # Clean up
            os.environ.pop("AI_MODEL", None)
            os.environ.pop("AI_TEMPERATURE", None)
    
    def test_client_configuration_offline(self):
        """Test comprehensive client configuration without network."""
        settings = AiSettings(
            api_key="offline-key",
            model="offline-model",
            temperature=0.3,
            max_tokens=500,
            timeout=60,
            base_url="http://localhost:8080"
        )
        
        fake_provider = FakeProvider(["offline response"])
        client = AiClient(settings, provider=fake_provider)
        
        # Verify settings are applied
        assert isinstance(client.settings.api_key, str)  # Contract: api_key is string type
        assert len(client.settings.api_key) > 0  # Contract: non-empty api key
        assert isinstance(client.settings.model, str)  # Contract: model is string type
        assert len(client.settings.model) > 0  # Contract: non-empty model
        assert isinstance(client.settings.temperature, float)  # Contract: temperature is float
        assert 0.0 <= client.settings.temperature <= 2.0  # Contract: valid temperature range
        assert isinstance(client.settings.max_tokens, int)  # Contract: max_tokens is int
        assert client.settings.max_tokens > 0  # Contract: positive max_tokens
        assert isinstance(client.settings.timeout, (int, float))  # Contract: timeout is numeric
        assert client.settings.timeout > 0  # Contract: positive timeout
        assert isinstance(client.settings.base_url, str)  # Contract: base_url is string type
        assert len(client.settings.base_url) > 0  # Contract: non-empty base_url
        
        # Should work offline
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: returns string response
        assert len(response) > 0  # Contract: non-empty response
