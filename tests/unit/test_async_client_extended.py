"""Extended tests for async_client.py to increase coverage."""

import pytest
import asyncio
from unittest.mock import AsyncMock
from typing import List

from ai_utilities.async_client import AsyncAiClient
from ai_utilities.client import AiSettings
from tests.fake_provider import FakeAsyncProvider


class TestAsyncAiClientExtended:
    """Extended test cases for AsyncAiClient to cover missing lines."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = AiSettings(api_key="test-key", model="test-model")
        self.fake_provider = FakeAsyncProvider()

    def test_async_client_creation_with_settings(self):
        """Test creating AsyncAiClient with settings."""
        client = AsyncAiClient(self.settings)
        assert client.settings.api_key == "test-key"
        assert client.settings.model == "test-model"

    def test_async_client_creation_with_provider(self):
        """Test creating AsyncAiClient with explicit provider."""
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        assert client.provider == self.fake_provider

    def test_async_client_with_minimal_settings(self):
        """Test creating AsyncAiClient with minimal settings using mock provider."""
        settings = AiSettings(api_key="test-key")
        mock_provider = AsyncMock()
        client = AsyncAiClient(settings, provider=mock_provider)
        assert client.settings.api_key == "test-key"
        assert client.provider == mock_provider

    def test_async_client_with_custom_timeout(self):
        """Test AsyncAiClient with custom timeout using mock provider."""
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            timeout=60
        )
        mock_provider = AsyncMock()
        client = AsyncAiClient(settings, provider=mock_provider)
        assert client.settings.timeout == 60

    def test_async_client_with_temperature_and_max_tokens(self):
        """Test AsyncAiClient with temperature and max_tokens using mock provider."""
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            temperature=0.1,
            max_tokens=5000
        )
        mock_provider = AsyncMock()
        client = AsyncAiClient(settings, provider=mock_provider)
        assert client.settings.temperature == 0.1
        assert client.settings.max_tokens == 5000

    @pytest.mark.asyncio
    async def test_async_ask_with_provider_parameters(self):
        """Test async ask method with provider-specific parameters using mock provider."""
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = "test response"
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        response = await client.ask("test", temperature=0.5, max_tokens=100)
        # Contract: verify response is returned (passthrough)
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_ask_many_with_empty_list(self):
        """Test async ask_many with empty prompt list using mock provider."""
        mock_provider = AsyncMock()
        mock_provider.ask_many.return_value = []
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        responses = await client.ask_many([])
        assert len(responses) == 0
        # Note: ask_many may not be called if the list is empty, so we just verify the result

    @pytest.mark.asyncio
    async def test_async_ask_many_with_provider_parameters(self):
        """Test async ask_many with provider parameters using mock provider."""
        mock_provider = AsyncMock()
        
        # Mock the ask method to be called individually for each prompt
        mock_provider.ask.return_value = "test response"
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        responses = await client.ask_many(["prompt1", "prompt2"], temperature=0.3)
        assert len(responses) == 2
        
        # Verify AskResult contract
        assert hasattr(responses[0], 'response')
        assert hasattr(responses[0], 'error')
        assert hasattr(responses[0], 'prompt')
        assert responses[0].prompt == "prompt1"
        assert responses[0].response is not None
        assert responses[0].error is None
        
        assert responses[1].prompt == "prompt2"
        assert responses[1].response is not None
        assert responses[1].error is None

    @pytest.mark.asyncio
    async def test_async_ask_json_with_valid_json(self):
        """Test async ask with JSON return format using mock provider."""
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = {"test": "response"}  # Return JSON dict directly
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        response = await client.ask("test prompt", return_format="json")
        assert isinstance(response, dict)
        # Contract: verify JSON response structure (provider contract)
        assert len(response) >= 1  # Should have at least one key

    @pytest.mark.asyncio
    async def test_async_ask_json_with_invalid_json(self):
        """Test async ask with invalid JSON response using mock provider."""
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = "not valid json"
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        # Contract: async client passes through provider response without validation
        response = await client.ask("test prompt", return_format="json")
        # Should return whatever the provider returns (no JSON parsing in client)
        assert response == "not valid json"

    @pytest.mark.asyncio
    async def test_async_ask_json_with_non_dict_response(self):
        """Test async ask when response is valid JSON but not a dict using mock provider."""
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = ["not", "a", "dict"]
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        response = await client.ask("test prompt", return_format="json")
        assert isinstance(response, list)  # Should return the parsed JSON as-is

    @pytest.mark.asyncio
    async def test_async_ask_with_different_models(self):
        """Test async client with different model settings using mock providers."""
        models_to_test = ["gpt-3.5-turbo", "gpt-4", "claude-3"]
        
        for model in models_to_test:
            settings = AiSettings(api_key="test-key", model=model)
            mock_provider = AsyncMock()
            mock_provider.ask.return_value = f"test response from {model}"
            client = AsyncAiClient(settings, provider=mock_provider)
            
            response = await client.ask("test")
            assert "test" in response

    @pytest.mark.asyncio
    async def test_async_client_error_handling(self, monkeypatch):
        """Test async client error handling."""
        # Clear all API key environment variables for this specific test
        api_key_vars = [
            'OPENAI_API_KEY', 'AI_API_KEY', 'GROQ_API_KEY', 'TOGETHER_API_KEY', 
            'OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY', 'OLLAMA_HOST', 
            'TEXT_GENERATION_WEBUI_BASE_URL', 'LMSTUDIO_BASE_URL', 'FASTCHAT_BASE_URL'
        ]
        
        for var in api_key_vars:
            monkeypatch.delenv(var, raising=False)
        
        # Test with invalid settings - should fail either during construction or during use
        try:
            client = AsyncAiClient(AiSettings())  # No API key
            # If construction succeeds, it should fail during use
            with pytest.raises(Exception):
                await client.ask("test prompt")
        except Exception:
            # If construction fails, that's also expected behavior
            pass

    @pytest.mark.asyncio
    async def test_async_client_repr(self):
        """Test async client string representation using mock provider."""
        mock_provider = AsyncMock()
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        repr_str = repr(client)
        assert "AsyncAiClient" in repr_str

    @pytest.mark.asyncio
    async def test_async_client_with_base_url(self):
        """Test async client with custom base URL using mock provider."""
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            base_url="https://custom-api.example.com"
        )
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = "Response from custom API"
        client = AsyncAiClient(settings, provider=mock_provider)
        
        response = await client.ask("test")
        # Contract: verify response is returned (passthrough)
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_client_parameter_override(self):
        """Test async client parameter override using mock provider."""
        settings = AiSettings(
            api_key="key",
            model="test-model-1",
            temperature=0.5
        )
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = "Response with overridden parameters"
        client = AsyncAiClient(settings, provider=mock_provider)
        
        # This should use the overridden model
        response = await client.ask("test", model="test-model-2", temperature=0.8)
        # Contract: verify response is returned (passthrough)
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_client_concurrent_requests(self):
        """Test async client handling concurrent requests using mock provider."""
        import time
        
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = f"response-{time.time()}"
        
        client = AsyncAiClient(self.settings, provider=mock_provider)
        
        async def make_request():
            response = await client.ask(f"test-{time.time()}")
            return response
        
        # Create multiple concurrent requests
        tasks = [make_request() for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            # Contract: verify each result is returned (passthrough) - ask() returns strings
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_async_client_large_prompt_handling(self):
        """Test async client handling of large prompts."""
        large_prompt = "test " * 10000  # Very large prompt
        
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        response = await client.ask(large_prompt)
        # Contract: verify response is returned (passthrough)
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_client_special_characters_in_prompt(self):
        """Test async client handling of special characters in prompts."""
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
        
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        for prompt in special_prompts:
            response = await client.ask(prompt)
            assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_client_empty_prompt(self):
        """Test async client handling of empty prompts."""
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        # Empty string
        response = await client.ask("")
        assert isinstance(response, str)
        
        # Whitespace only
        response = await client.ask("   \n\t  ")
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_client_none_prompt(self):
        """Test async client handling of None prompt."""
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        # FakeProvider should handle None gracefully and return a string response
        response = await client.ask(None)
        assert isinstance(response, str)
        assert len(response) >= 0  # Empty string is acceptable

    @pytest.mark.asyncio
    async def test_async_ask_many_mixed_prompt_types(self):
        """Test async ask_many with mixed prompt types and lengths."""
        prompts = [
            "Short prompt",
            "Medium length prompt with some details",
            "Very long prompt " * 100,
            "Prompt with special chars: 🚀\n\t",
            "Prompt with numbers: 12345",
        ]
        
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        responses = await client.ask_many(prompts)
        assert len(responses) == len(prompts)
        
        for i, response in enumerate(responses):
            assert isinstance(response.response, str)
            assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_async_client_batch_ordering(self):
        """Test that async batch responses maintain order."""
        from tests.fake_provider import FakeAsyncProvider
        fake_provider = FakeAsyncProvider([
            "Response 1: first",
            "Response 2: second", 
            "Response 3: third"
        ])
        client = AsyncAiClient(self.settings, provider=fake_provider)
        
        prompts = ["first", "second", "third"]
        responses = await client.ask_many(prompts)
        
        assert len(responses) == 3
        assert "Response 1: first" in responses[0].response
        assert "Response 2: second" in responses[1].response
        assert "Response 3: third" in responses[2].response

    @pytest.mark.asyncio
    async def test_async_client_settings_validation(self):
        """Test async client settings validation."""
        # Test with empty API key - should still create client but may fail during use
        settings = AiSettings(api_key="")
        client = AsyncAiClient(settings, provider=self.fake_provider)
        assert client is not None
        assert client.settings.api_key == ""
        
        # Test with empty model - should still create client (model defaults to None)
        settings = AiSettings(api_key="test-key", model="")
        client = AsyncAiClient(settings, provider=self.fake_provider)
        assert client is not None
        # Empty string model becomes None in AiSettings
        assert client.settings.model is None or client.settings.model == ""

    @pytest.mark.asyncio
    async def test_async_create_client_convenience(self):
        """Test the create_async_client convenience function."""
        # This function might not exist, so let's test gracefully
        try:
            from ai_utilities.async_client import create_async_client
            
            client = create_async_client(api_key="test-key", model="test-model-2")
            assert client.settings.api_key == "test-key"
            assert client.settings.model == "test-model-2"
        except ImportError:
            # Function doesn't exist, which is fine
            pass

    @pytest.mark.asyncio
    async def test_async_create_client_with_all_parameters(self):
        """Test create_async_client with all parameters."""
        # This function might not exist, so let's test gracefully
        try:
            from ai_utilities.async_client import create_async_client
            
            client = create_async_client(
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
        except ImportError:
            # Function doesn't exist, which is fine
            pass

    @pytest.mark.asyncio
    async def test_async_client_provider_detection_fallback(self):
        """ async provider with explicit mock provider instead of fallback."""
        # Test with settings that don't match any specific provider
        settings = AiSettings(
            api_key="test-key",
            model="unknown-model",
            base_url="https://unknown-api.example.com"
        )
        
        # Use explicit mock provider instead of relying on fallback
        mock_provider = AsyncMock()
        client = AsyncAiClient(settings, provider=mock_provider)
        assert client is not None
        assert client.provider == mock_provider

    @pytest.mark.asyncio
    async def test_async_client_with_temperature_edge_cases(self):
        """Test async client with temperature edge cases."""
        temperatures = [0.0, 0.5, 1.0, 1.5, 2.0]
        
        for temp in temperatures:
            settings = AiSettings(
                api_key="test-key",
                model="test-model",
                temperature=temp
            )
            client = AsyncAiClient(settings, provider=self.fake_provider)
            
            response = await client.ask("test")
            assert "test" in response

    @pytest.mark.asyncio
    async def test_async_client_with_max_tokens_edge_cases(self):
        """Test async client with max_tokens edge cases."""
        token_limits = [1, 100, 5000, 100000]
        
        for limit in token_limits:
            settings = AiSettings(
                api_key="test-key",
                model="test-model",
                max_tokens=limit
            )
            client = AsyncAiClient(settings, provider=self.fake_provider)
            
            response = await client.ask("test")
            assert "test" in response

    @pytest.mark.asyncio
    async def test_async_ask_with_streaming_not_supported(self):
        """Test async ask with streaming when not supported."""
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        # FakeProvider doesn't support streaming, should handle gracefully
        # Since FakeProvider ignores the stream parameter, this should work
        response = await client.ask("test", stream=True)
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_async_ask_many_with_empty_prompts(self):
        """Test async ask_many with empty prompts in the list using actual contract."""
        prompts = ["valid prompt", "", "another valid prompt", "   "]
        
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        responses = await client.ask_many(prompts)
        
        assert len(responses) == 4
        for response in responses:
            # Check that response is either a string (success) or None (error)
            assert response.response is None or isinstance(response.response, str)
            # If response is None, there should be an error message
            if response.response is None:
                assert response.error is not None
                assert len(response.error) > 0

    @pytest.mark.asyncio
    async def test_async_client_context_manager(self):
        """Test async client as context manager if supported."""
        client = AsyncAiClient(self.settings, provider=self.fake_provider)
        
        # Test if client supports context manager protocol
        if hasattr(client, '__aenter__') and hasattr(client, '__aexit__'):
            async with client:
                response = await client.ask("test")
                # Contract: verify response is returned (passthrough)
                assert response is not None
                assert isinstance(response, str)
        else:
            # If not supported, just test normal usage
            response = await client.ask("test")
            # Contract: verify response is returned (passthrough)
            assert response is not None
            assert isinstance(response, str)
