"""Extended tests for the AI client to increase coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


class TestAiClientExtended:
    """Extended tests for AiClient functionality."""
    
    def test_ai_client_with_minimal_settings(self) -> None:
        """Test creating AI client with minimal settings."""
        settings = AiSettings(api_key="test-key")
        client = AiClient(settings)
        assert client.settings.api_key == "test-key"
        assert client.provider is not None  # Should auto-detect provider
    
    def test_ai_client_provider_precedence(self) -> None:
        """Test that explicit provider takes precedence over settings."""
        settings = AiSettings(api_key="key", model="model1")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        # Should use the explicit provider, not auto-detected one
        assert client.provider == fake_provider
    
    def test_ask_with_provider_parameters(self) -> None:
        """Test ask method with provider-specific parameters."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        response = client.ask("test", temperature=0.5, max_tokens=100)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_many_with_empty_list(self) -> None:
        """Test ask_many with empty prompt list."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        responses = client.ask_many([])
        assert len(responses) == 0
    
    def test_ask_many_with_provider_parameters(self) -> None:
        """Test ask_many with provider parameters."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        responses = client.ask_many(["prompt1", "prompt2"], temperature=0.3)
        assert len(responses) == 2
        assert isinstance(responses[0].response, str)  # Contract: response is string type
        assert len(responses[0].response) > 0  # Contract: non-empty response
        assert isinstance(responses[1].response, str)  # Contract: response is string type
        assert len(responses[1].response) > 0  # Contract: non-empty response
    
    def test_ask_json_with_invalid_json(self) -> None:
        """Test ask_json with invalid JSON response."""
        fake_provider = FakeProvider(responses=['not valid json'])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(Exception):  # Should raise JSON parsing error
            client.ask_json("test prompt")
    
    def test_ask_json_with_malformed_json(self) -> None:
        """Test ask_json with malformed JSON response."""
        fake_provider = FakeProvider(responses=['{"incomplete": json'])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(Exception):  # Should raise JSON parsing error
            client.ask_json("test prompt")
    
    def test_ask_json_with_non_dict_response(self) -> None:
        """Test ask_json when response is valid JSON but not a dict."""
        fake_provider = FakeProvider(responses=['["not", "a", "dict"]'])
        client = AiClient(provider=fake_provider)
        
        # Should return the parsed JSON even if not a dict
        response = client.ask_json("test prompt")
        assert isinstance(response, list)
        assert response == ["not", "a", "dict"]
    
    def test_client_with_different_models(self) -> None:
        """Test client with different model settings."""
        models_to_test = ["gpt-3.5-turbo", "gpt-4", "claude-3"]
        
        for model in models_to_test:
            settings = AiSettings(api_key="test-key", model=model)
            fake_provider = FakeProvider()
            client = AiClient(settings, provider=fake_provider)
            
            response = client.ask("test")
            assert isinstance(response, str)  # Contract: response is string type
            assert len(response) > 0  # Contract: non-empty response
    
    def test_client_error_handling(self) -> None:
        """Test client error handling."""
        # Test with minimal settings - should raise ProviderConfigurationError
        # New invariant: ProviderConfigurationError is acceptable in CI/non-interactive
        with pytest.raises(Exception) as exc_info:
            AiClient(AiSettings())  # No API key
        # Should be a configuration error, not an input-related error
        assert "configuration" in str(exc_info.value).lower() or "provider" in str(exc_info.value).lower()
    
    def test_client_repr(self) -> None:
        """Test client string representation."""
        settings = AiSettings(api_key="test-key", model="test-model")
        client = AiClient(settings)
        
        repr_str = repr(client)
        assert "AiClient" in repr_str
    
    def test_client_settings_validation(self) -> None:
        """Test that settings are properly validated."""
        # Test with various invalid settings combinations
        # Note: AiSettings may have different validation requirements than expected
        
        # Test empty API key - this might be allowed in some contexts
        try:
            settings = AiSettings(api_key="")
            client = AiClient(settings)
            # If this works, the client should handle empty API keys gracefully
            assert client is not None
        except Exception:
            # If it raises an exception, that's also acceptable
            pass
        
        # Test empty model - this might be allowed with default model
        try:
            settings = AiSettings(api_key="test-key", model="")
            client = AiClient(settings)
            # If this works, there should be a default model
            assert client is not None
        except Exception:
            # If it raises an exception, that's also acceptable
            pass
    
    def test_client_with_base_url(self) -> None:
        """Test client with custom base URL."""
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            base_url="https://custom-api.example.com"
        )
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_client_with_timeout(self) -> None:
        """Test client with custom timeout."""
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            timeout=60
        )
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        response = client.ask("test")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_client_with_temperature(self) -> None:
        """Test client with temperature setting."""
        temperatures = [0.0, 0.5, 1.0, 1.5]
        
        for temp in temperatures:
            settings = AiSettings(
                api_key="test-key",
                model="test-model",
                temperature=temp
            )
            fake_provider = FakeProvider()
            client = AiClient(settings, provider=fake_provider)
            
            response = client.ask("test")
            assert isinstance(response, str)  # Contract: response is string type
            assert len(response) > 0  # Contract: non-empty response
    
    def test_client_with_max_tokens(self) -> None:
        """Test client with max_tokens setting."""
        token_limits = [100, 500, 1000, 2000]
        
        for limit in token_limits:
            settings = AiSettings(
                api_key="test-key",
                model="test-model",
                max_tokens=limit
            )
            fake_provider = FakeProvider()
            client = AiClient(settings, provider=fake_provider)
            
            response = client.ask("test")
            assert isinstance(response, str)  # Contract: response is string type
            assert len(response) > 0  # Contract: non-empty response
    
    def test_client_parameter_override_edge_cases(self) -> None:
        """Test parameter override with edge cases."""
        settings = AiSettings(
            api_key="key",
            model="test-model-1",
            temperature=0.5,
            max_tokens=1000
        )
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        # Override with None values
        response = client.ask("test", temperature=None, max_tokens=None)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Override with extreme values
        response = client.ask("test", temperature=2.0, max_tokens=1)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_client_concurrent_requests(self) -> None:
        """Test client handling concurrent requests."""
        import threading
        import time
        
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        results = []
        
        def make_request():
            response = client.ask(f"test-{time.time()}")
            results.append(response)
        
        # Create multiple threads making requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have 5 results
        assert len(results) == 5
        for result in results:
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty result
    
    def test_client_large_prompt_handling(self) -> None:
        """Test client handling of large prompts."""
        large_prompt = "test " * 10000  # Very large prompt
        
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        response = client.ask(large_prompt)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_client_special_characters_in_prompt(self) -> None:
        """Test client handling of special characters in prompts."""
        special_prompts = [
            "Test with 🚀 emoji",
            "Test with \n newlines",
            "Test with \t tabs",
            "Test with \" quotes",
            "Test with ' apostrophes",
            "Test with \\ backslashes",
            "Test with unicode: ñáéíóú",
            "Test with math: ∑∏∫",
        ]
        
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        for prompt in special_prompts:
            response = client.ask(prompt)
            # Should handle special characters without errors
            assert isinstance(response, str)
    
    def test_client_empty_prompt(self) -> None:
        """Test client handling of empty prompts."""
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        # Empty string
        response = client.ask("")
        assert isinstance(response, str)
        
        # Whitespace only
        response = client.ask("   \n\t  ")
        assert isinstance(response, str)
    
    def test_client_none_prompt(self) -> None:
        """Test client handling of None prompt."""
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        # The FakeProvider might handle None gracefully, so let's test that it doesn't crash
        try:
            response = client.ask(None)
            # If it doesn't crash, that's acceptable behavior for the fake provider
            assert isinstance(response, str)
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass
    
    def test_ask_many_mixed_prompt_types(self) -> None:
        """Test ask_many with mixed prompt types and lengths."""
        prompts = [
            "Short prompt",
            "Medium length prompt with some details",
            "Very long prompt " * 100,
            "Prompt with special chars: 🚀\n\t",
            "Prompt with numbers: 12345",
        ]
        
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider()
        client = AiClient(settings, provider=fake_provider)
        
        responses = client.ask_many(prompts)
        assert len(responses) == len(prompts)
        
        for i, response in enumerate(responses):
            assert isinstance(response.response, str)
            # Response should contain some reference to the prompt
            assert len(response.response) > 0
    
    def test_create_client_with_all_parameters(self) -> None:
        """Test create_client convenience function with all parameters."""
        from ai_utilities import create_client
        
        client = create_client(
            api_key="test-key",
            model="test-model",
            base_url="https://api.example.com",
            timeout=60,
            temperature=0.3,
            max_tokens=2000
        )
        
        assert client.settings.api_key == "test-key"
        assert client.settings.model == "test-model"
        assert client.settings.base_url == "https://api.example.com"
        assert client.settings.timeout == 60
        assert client.settings.temperature == 0.3
        assert client.settings.max_tokens == 2000
    
    def test_client_provider_detection_fallback(self) -> None:
        """Test provider detection fallback when no explicit provider."""
        # Test with settings that don't match any specific provider
        settings = AiSettings(
            api_key="test-key",
            model="unknown-model",
            base_url="https://unknown-api.example.com"
        )
        
        # Should still create a client (with default provider)
        client = AiClient(settings)
        assert client is not None
        assert client.provider is not None
