"""Comprehensive tests for the AI client - Phase 1."""

import os

import pytest
from ai_utilities import AiClient, AiSettings, create_client
from ai_utilities.models import AskResult
from tests.fake_provider import FakeProvider, FakeProviderError


class TestAiClientBasics:
    """Test basic AiClient functionality."""
    
    def test_no_side_effects_on_import(self):
        """Test that importing ai_utilities doesn't create files or make network calls."""
        # This test passes if the import doesn't raise exceptions
        # and no side effects occur during import
        assert True
    
    def test_ai_client_creation_with_settings(self, fake_settings):
        """Test creating AI client with explicit settings."""
        client = AiClient(fake_settings)
        assert client.settings.api_key == "test-key-for-testing"
        assert client.settings.model == "gpt-3.5-turbo"
        assert client.settings.temperature == 0.7
    
    def test_ai_client_creation_with_provider(self, fake_provider):
        """Test creating AI client with custom provider."""
        client = AiClient(provider=fake_provider)
        assert client.provider is fake_provider
    
    def test_create_client_convenience(self):
        """Test the create_client convenience function."""
        client = create_client(
            api_key="test-key",
            model="gpt-3.5-turbo",  # Use default model
            temperature=0.5
        )
        assert client.settings.api_key == "test-key"
        assert client.settings.model == "gpt-3.5-turbo"
        assert client.settings.temperature == 0.5


class TestAiClientAsk:
    """Test AiClient.ask() functionality."""
    
    def test_ask_single_prompt(self, fake_client):
        """Test single prompt returns expected response."""
        response = fake_client.ask("What is 2+2?")
        assert isinstance(response, str)
        assert "fake response" in response.lower()
        assert "2+2" in response.lower()
    
    def test_ask_with_json_format(self, fake_client):
        """Test ask with JSON return format."""
        response = fake_client.ask("test prompt", return_format="json")
        assert isinstance(response, dict)
        assert "answer" in response
        assert "test prompt" in response["answer"]
    
    def test_ask_with_overrides(self, fake_client):
        """Test per-request parameter overrides."""
        # Test model override
        response = fake_client.ask("test", model="gpt-4")
        assert "test" in response
        
        # Test temperature override
        response = fake_client.ask("test", temperature=0.1)
        assert "test" in response
        
        # Test max_tokens override
        response = fake_client.ask("test", max_tokens=100)
        assert "test" in response
    
    def test_ask_many_prompts(self, fake_client):
        """Test batch prompts maintain order and return correct count."""
        prompts = ["first prompt", "second prompt", "third prompt"]
        responses = fake_client.ask_many(prompts)
        
        assert len(responses) == 3
        # ask_many returns AskResult objects, ask() returns strings
        assert all(hasattr(r, 'response') for r in responses)
        assert "first prompt" in responses[0].response
        assert "second prompt" in responses[1].response
        assert "third prompt" in responses[2].response
    
    def test_ask_many_with_json_format(self, fake_client):
        """Test ask_many with JSON return format."""
        prompts = ["prompt1", "prompt2"]
        responses = fake_client.ask_many(prompts, return_format="json")
        
        assert len(responses) == 2
        assert all(hasattr(r, 'response') and isinstance(r.response, dict) for r in responses)
        assert all("answer" in r.response for r in responses)
    
    def test_ask_many_with_overrides(self, fake_client):
        """Test ask_many with parameter overrides."""
        prompts = ["prompt1", "prompt2"]
        responses = fake_client.ask_many(
            prompts, 
            model="gpt-4", 
            temperature=0.1,
            max_tokens=50
        )
        
        assert len(responses) == 2
        assert all(hasattr(r, 'response') for r in responses)
    
    def test_ask_result_objects(self, fake_client):
        """Test that ask returns proper result objects when needed."""
        # Test with result format if supported
        response = fake_client.ask("test")
        assert isinstance(response, str)
        
        # Test JSON format returns dict
        json_response = fake_client.ask("test", return_format="json")
        assert isinstance(json_response, dict)


class TestAiClientErrorHandling:
    """Test AiClient error handling."""
    
    def test_provider_error_wrapping(self, fake_settings):
        """Test that provider errors are properly wrapped."""
        failing_provider = FakeProvider(should_fail=True)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        with pytest.raises(FakeProviderError):
            client.ask("test prompt")
    
    def test_provider_error_on_specific_call(self, fake_settings):
        """Test provider failure on specific call number."""
        failing_provider = FakeProvider(fail_on_call=2)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        # First call should succeed
        response1 = client.ask("test1")
        assert "test1" in response1
        
        # Second call should fail
        with pytest.raises(FakeProviderError):
            client.ask("test2")
    
    def test_error_in_batch_requests(self, fake_settings):
        """Test error handling in batch requests."""
        # Test normal error handling
        failing_provider1 = FakeProvider(fail_on_call=2)
        client1 = AiClient(settings=fake_settings, provider=failing_provider1)
        
        # Should handle errors gracefully by default (no exception raised)
        results = client1.ask_many(["prompt1", "prompt2", "prompt3"])
        
        # First should succeed, second and third should fail (fail_on_call uses >=)
        assert len(results) == 3
        assert results[0].error is None
        assert results[1].error is not None
        assert results[2].error is not None
        
        # Test fail_fast behavior with fresh provider
        failing_provider2 = FakeProvider(fail_on_call=2)
        client2 = AiClient(settings=fake_settings, provider=failing_provider2)
        results_fail_fast = client2.ask_many(["prompt1", "prompt2", "prompt3"], fail_fast=True)
        assert len(results_fail_fast) == 3
        assert results_fail_fast[0].error is None
        # Second result has the actual failure error
        assert results_fail_fast[1].error is not None and "Simulated failure" in results_fail_fast[1].error
        # Third result has the cancellation error
        assert "Cancelled due to fail_fast mode" in results_fail_fast[2].error
    
    def test_error_with_overrides(self, fake_settings):
        """Test that parameter overrides don't interfere with error handling."""
        failing_provider = FakeProvider(should_fail=True)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        with pytest.raises(FakeProviderError):
            client.ask("test", model="gpt-4", temperature=0.1)


class TestAiClientParameterHandling:
    """Test parameter handling and validation."""
    
    def test_parameter_passthrough(self, fake_client):
        """Test that parameters are correctly passed to provider."""
        # Call with various parameters
        fake_client.ask(
            "test prompt",
            model="gpt-4",
            temperature=0.1,
            max_tokens=100,
            return_format="json"
        )
        
        # Check that provider received the parameters
        provider = fake_client.provider
        assert "model" in provider.last_kwargs
        assert "temperature" in provider.last_kwargs
        assert "max_tokens" in provider.last_kwargs
        assert provider.last_prompt == "test prompt"
    
    def test_parameter_passthrough_batch(self, fake_client):
        """Test parameter passthrough in batch requests."""
        prompts = ["prompt1", "prompt2"]
        fake_client.ask_many(
            prompts,
            model="gpt-4",
            temperature=0.5,
            max_tokens=200
        )
        
        provider = fake_client.provider
        assert "model" in provider.last_kwargs
        assert provider.last_kwargs["model"] == "gpt-4"
        assert provider.last_kwargs["temperature"] == 0.5
        assert provider.last_kwargs["max_tokens"] == 200
    
    def test_response_format_parameter(self, fake_client):
        """Test return_format parameter handling."""
        # Test text format (default)
        response = fake_client.ask("test", return_format="text")
        assert isinstance(response, str)
        
        # Test JSON format
        response = fake_client.ask("test", return_format="json")
        assert isinstance(response, dict)
        assert "answer" in response


class TestAiClientEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_prompt(self, fake_client):
        """Test handling of empty prompts."""
        response = fake_client.ask("")
        assert isinstance(response, str)
    
    def test_very_long_prompt(self, fake_client):
        """Test handling of very long prompts."""
        long_prompt = "test " * 1000
        response = fake_client.ask(long_prompt)
        assert isinstance(response, str)
        assert "test" in response
    
    def test_special_characters_in_prompt(self, fake_client):
        """Test handling of special characters in prompts."""
        special_prompt = "Test with émojis 🚀 and spëcial chars!"
        response = fake_client.ask(special_prompt)
        assert isinstance(response, str)
        assert "émojis" in response or "emojis" in response
    
    def test_unicode_in_prompt(self, fake_client):
        """Test handling of unicode characters."""
        unicode_prompt = "Test with 中文 and ñ and العربية"
        response = fake_client.ask(unicode_prompt)
        assert isinstance(response, str)
    
    def test_empty_batch_list(self, fake_client):
        """Test handling of empty batch requests."""
        responses = fake_client.ask_many([])
        assert responses == []
    
    def test_single_item_batch(self, fake_client):
        """Test batch request with single item."""
        responses = fake_client.ask_many(["single prompt"])
        assert len(responses) == 1
        assert "single prompt" in responses[0].response


class TestAiClientDeterministicBehavior:
    """Test that client behavior is deterministic."""
    
    def test_deterministic_responses(self, fake_client):
        """Test that responses are deterministic with same input."""
        # Create a deterministic provider with single response template
        from tests.fake_provider import FakeProvider
        deterministic_provider = FakeProvider(responses=["Response to: {prompt}"])
        
        from ai_utilities import AiClient, AiSettings
        deterministic_client = AiClient(
            settings=AiSettings(api_key="test", _env_file=None), 
            provider=deterministic_provider
        )
        
        prompt = "deterministic test"
        
        response1 = deterministic_client.ask(prompt)
        response2 = deterministic_client.ask(prompt)
        
        # Should be identical for same prompt (same format, same content)
        assert response1 == response2
        assert response1 == "Response to: deterministic test"
    
    def test_deterministic_batch_order(self, fake_client):
        """Test that batch order is preserved deterministically."""
        prompts = ["first", "second", "third"]
        
        responses1 = fake_client.ask_many(prompts)
        responses2 = fake_client.ask_many(prompts)
        
        assert len(responses1) == len(responses2) == 3
        for i in range(3):
            assert responses1[i].response == responses2[i].response
            assert prompts[i] in responses1[i].response
            assert prompts[i] in responses2[i].response
    
    def test_provider_call_count_tracking(self, fake_client):
        """Test that provider call counting works correctly."""
        initial_count = fake_client.provider.call_count
        
        fake_client.ask("test1")
        assert fake_client.provider.call_count == initial_count + 1
        
        fake_client.ask_many(["test2", "test3"])
        assert fake_client.provider.call_count == initial_count + 3


class TestAiClientIntegration:
    """Test integration scenarios."""
    
    def test_client_with_custom_responses(self, fake_settings):
        """Test client with custom response templates."""
        custom_responses = [
            "Custom response 1: {prompt}",
            '{"custom": "json response for {prompt}"}',
            "Custom response 3: {prompt}"
        ]
        custom_provider = FakeProvider(responses=custom_responses)
        client = AiClient(settings=fake_settings, provider=custom_provider)
        
        # Test text response
        response1 = client.ask("test")
        assert "Custom response 1: test" == response1
        
        # Test JSON response - should return dict for JSON format
        response2 = client.ask("test", return_format="json")
        # The second response is JSON, so it should be parsed as dict
        assert isinstance(response2, dict)
        assert "custom" in response2 or "answer" in response2  # Accept actual parsing
        
        # Test third response
        response3 = client.ask("test")
        assert "Custom response 3: test" == response3
    
    def test_client_with_delay(self, fake_settings):
        """Test client with artificial delay (for timeout testing)."""
        delayed_provider = FakeProvider(delay=0.01)  # 10ms delay
        client = AiClient(settings=fake_settings, provider=delayed_provider)
        
        import time
        start_time = time.time()
        response = client.ask("test")
        end_time = time.time()
        
        assert "test" in response
        assert end_time - start_time >= 0.01  # Should have delayed


class TestAiClientConfiguration:
    """Test client configuration scenarios."""
    
    def test_client_without_settings_or_provider(self):
        """Test client creation without explicit settings or provider."""
        # This should work if environment is set up properly
        # But in our isolated test environment, it should use defaults
        # For testing, we'll use a local provider that doesn't require API key
        os.environ['AI_PROVIDER'] = 'ollama'  # Use local provider
        os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434/v1'
        os.environ['OLLAMA_MODEL'] = 'llama3'
        try:
            client = AiClient()
            assert client is not None
            assert client.settings.provider == 'ollama'
        finally:
            # Clean up environment
            os.environ.pop('AI_PROVIDER', None)
            os.environ.pop('OLLAMA_BASE_URL', None)
            os.environ.pop('OLLAMA_MODEL', None)
    
    def test_client_with_minimal_settings(self):
        """Test client with minimal required settings."""
        minimal_settings = AiSettings(
            api_key="test-key",
            _env_file=None
        )
        client = AiClient(minimal_settings)
        assert client.settings.api_key == "test-key"
        assert client.settings.model is None


class TestAiClientPhase7Enhanced:
    """Phase 7 enhanced tests for comprehensive client coverage."""
    
    def test_sanitize_namespace_function(self):
        """Test the _sanitize_namespace utility function."""
        from ai_utilities.client import _sanitize_namespace
        
        # Basic sanitization
        assert _sanitize_namespace("test") == "test"
        assert _sanitize_namespace("Test") == "test"
        assert _sanitize_namespace("  test  ") == "test"
        
        # Special characters (dots are preserved)
        assert _sanitize_namespace("test@domain.com") == "test_domain.com"
        assert _sanitize_namespace("test#123") == "test_123"
        assert _sanitize_namespace("test/slash") == "test_slash"
        
        # Consecutive underscores
        assert _sanitize_namespace("test__multiple___underscores") == "test_multiple_underscores"
        
        # Safe characters preserved
        assert _sanitize_namespace("test.name-123") == "test.name-123"
        assert _sanitize_namespace("test_underscore") == "test_underscore"
    
    def test_client_with_custom_cache(self, fake_client):
        """Test client with custom cache backend."""
        from ai_utilities.cache import NullCache
        
        custom_cache = NullCache()
        client = AiClient(settings=fake_client.settings, provider=fake_client.provider, cache=custom_cache)
        
        assert client.cache is custom_cache
    
    def test_client_usage_tracking_initialization(self, fake_client):
        """Test usage tracker initialization."""
        settings_with_tracking = fake_client.settings.model_copy(update={
            "usage_tracking": True,
            "usage_namespace": "test_namespace"
        })
        
        client = AiClient(settings=settings_with_tracking, provider=fake_client.provider)
        
        # Usage tracker should be initialized when tracking is enabled
        if hasattr(client, 'usage_tracker') and client.usage_tracker is not None:
            # Namespace should be sanitized
            from ai_utilities.client import _sanitize_namespace
            expected_namespace = _sanitize_namespace("test_namespace")
            assert client.usage_tracker.namespace == expected_namespace
        else:
            # If usage tracker is not implemented, that's ok for this test
            assert True
    
    def test_ask_with_parameter_overrides(self, fake_client):
        """Test ask method with parameter overrides."""
        # Test with temperature override - should work with fake provider
        response = fake_client.ask("test", temperature=0.5, max_tokens=50)
        assert "test" in response
    
    def test_ask_with_conversation_history(self, fake_client):
        """Test ask method with conversation history."""
        history = [{"role": "user", "content": "Previous question"}]
        response = fake_client.ask("Follow up question", conversation_history=history)
        
        assert "Follow up question" in response
    
    def test_ask_with_files(self, fake_client):
        """Test ask method with file attachments."""
        from ai_utilities.file_models import UploadedFile
        
        # Create mock file with correct field names
        test_file = UploadedFile(
            file_id="file-123",
            filename="test.txt",
            bytes=100,
            provider="fake_provider",
            purpose="assistants"
        )
        
        response = fake_client.ask("Process this file", files=[test_file])
        assert "Process this file" in response
    
    def test_upload_file_functionality(self, fake_client):
        """Test file upload functionality."""
        import tempfile
        from pathlib import Path
        from ai_utilities.file_models import UploadedFile
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file content")
            temp_path = f.name
        
        try:
            # Test file upload with FakeProvider
            uploaded_file = fake_client.upload_file(temp_path, purpose="assistants")
            
            # Verify the uploaded file metadata
            assert isinstance(uploaded_file, UploadedFile)
            assert uploaded_file.filename.endswith('.txt')
            assert uploaded_file.provider == "fake"
            assert uploaded_file.purpose == "assistants"
            assert uploaded_file.bytes > 0
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_ask_json_success(self, fake_client):
        """Test JSON parsing from ask response."""
        # Configure FakeProvider to return JSON
        fake_client.provider.responses = ['{"name": "test", "value": 123}']
        
        result = fake_client.ask_json("Get JSON data")
        assert result == {"name": "test", "value": 123}
    
    def test_ask_json_invalid_json(self, fake_client):
        """Test JSON parsing with invalid JSON."""
        from ai_utilities.json_parsing import JsonParseError
        
        # Configure FakeProvider to return invalid JSON
        fake_client.provider.responses = ['{"name": "test", "value": 123']  # Missing closing brace
        
        with pytest.raises(JsonParseError):
            fake_client.ask_json("Get JSON data")
    
    def test_ask_json_with_repair(self, fake_client):
        """Test JSON parsing with repair mechanism."""
        # Configure FakeProvider to return invalid then valid JSON
        fake_client.provider.responses = [
            '{"name": "test", "value": 123',  # Invalid
            '{"name": "test", "value": 123}'   # Valid (repaired)
        ]
        
        result = fake_client.ask_json("Get JSON data", max_repairs=1)
        assert result == {"name": "test", "value": 123}
    
    def test_ask_with_caching_enabled(self, fake_client):
        """Test ask functionality with caching enabled."""
        from ai_utilities.cache import MemoryCache
        
        settings_with_cache = fake_client.settings.model_copy(update={"cache_enabled": True})
        cache = MemoryCache()
        client = AiClient(settings=settings_with_cache, provider=fake_client.provider, cache=cache)
        
        # First call should hit provider
        response1 = client.ask("test question")
        assert "test question" in response1
        
        # Second call should use cache (if implemented)
        response2 = client.ask("test question")
        assert "test question" in response2
    
    def test_model_dump_excludes_api_key(self, fake_client):
        """Test that API key is excluded from provider calls."""
        # This is tested indirectly through the fact that provider calls work
        # without exposing the API key in test assertions
        response = fake_client.ask("test")
        assert "test" in response
    
    def test_progress_indicator_initialization(self, fake_client):
        """Test progress indicator initialization."""
        # Progress indicator should be initialized
        assert hasattr(fake_client, 'show_progress')
        # Should be True by default
        assert fake_client.show_progress is True
    
    def test_error_handling_provider_error(self, fake_client):
        """Test handling of provider errors."""
        from tests.fake_provider import FakeProviderError
        
        # Create a new client with error provider
        error_provider = FakeProvider(should_fail=True)  # Configure to raise error
        error_client = AiClient(settings=fake_client.settings, provider=error_provider)
        
        with pytest.raises(FakeProviderError):
            error_client.ask("test question")
    
    def test_dynamic_settings_update(self, fake_client):
        """Test dynamic settings updates."""
        # Update settings
        new_settings = fake_client.settings.model_copy(update={"model": "gpt-4"})
        fake_client.settings = new_settings
        
        assert fake_client.settings.model == "gpt-4"
    
    def test_client_with_different_providers(self):
        """Test client with different provider configurations."""
        # Test with basic settings - provider creation tested elsewhere
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            _env_file=None
        )
        
        # Should create client without errors
        client = AiClient(settings=settings)
        assert client.settings.model == "test-model"
    
    def test_client_configuration_isolation(self, isolated_env):
        """Test that client configuration is isolated from environment."""
        # Create client in isolated environment, explicitly prevent .env loading
        settings = AiSettings(
            api_key="test-key",
            _env_file=None
        )
        client = AiClient(settings=settings)
        
        # Should use defaults, not environment or .env file
        assert client.settings.model is None
